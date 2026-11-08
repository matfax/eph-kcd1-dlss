#!/usr/bin/env python3
"""Build the KCDDLSS menu mod (a DLSS row on the KCD1 Advanced Graphics page).

Run:  python3 -I build_menu_mod.py [--extract-root DIR] [--original FILE] [--out DIR]

Reads  tools/menu-mod/MM_AdvancedGraphics.xml  and  tools/menu-mod/mod.manifest,
validates the flowgraph, and writes
    <project>/dist/mods/KCDDLSS/mod.manifest
    <project>/dist/mods/KCDDLSS/Data/kcddlss_menu.pak
        (plain zip, deflate, one entry Libs/UI/UIActions/MM_AdvancedGraphics.xml)
Prints sha256 and sizes. Exit status 1 if any validation fails (nothing is written then).

Only the Python standard library is used. The extracted game files under
--extract-root are treated as data: they are parsed, never executed.
"""
import argparse
import glob
import hashlib
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))          # .../kcd1-dlss
DEFAULT_EXTRACT = "/mnt/cache/kcd-ui-extract"
ORIG_REL = "GameData/Libs/UI/UIActions/MM_AdvancedGraphics.xml"
TOBII_REL = "GameData/Libs/UI/UIActions/MM_TobiiSettings.xml"

MOD_FOLDER = "KCDDLSS"
PAK_NAME = "kcddlss_menu.pak"
PAK_ENTRY = "Libs/UI/UIActions/MM_AdvancedGraphics.xml"
ZIP_DATE = (2026, 11, 8, 0, 0, 0)       # fixed so that rebuilding gives the same sha256

# What the modded file is allowed to differ from the original by.
ALLOWED_REMOVED_EDGES = {("557", "824", "Call", "OnCall")}     # chain link AA -> SW_OD, re-routed via the DLSS row
EXPECTED_ORIG_MD5 = "e8463b15b8be59fce10395db227992e1"        # GameData.pak copy, per FINDINGS_KCD_UI_PAKS.md


class Problems:
    def __init__(self):
        self.errors = []
        self.notes = []

    def err(self, msg):
        self.errors.append(msg)
        print("  FAIL: " + msg)

    def ok(self, msg):
        print("  ok:   " + msg)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def load_graph(path):
    """-> (root, {id: node element}, [edge tuples (nodeIn,nodeOut,portIn,portOut)], duplicate ids)"""
    root = ET.parse(path).getroot()
    nodes, dups = {}, []
    for n in root.find("Nodes"):
        i = n.get("Id")
        if i in nodes:
            dups.append(i)
        nodes[i] = n
    edges = []
    for e in root.find("Edges"):
        edges.append((e.get("nodeIn"), e.get("nodeOut"), e.get("portIn"), e.get("portOut")))
    return root, nodes, edges, dups


def canon(el):
    """Whitespace-insensitive canonical form of an element (for 'node unchanged' checks)."""
    return (el.tag, tuple(sorted(el.attrib.items())), (el.text or "").strip(),
            tuple(canon(c) for c in el))


def port_inventory(files, p):
    """Port / input-attribute names per node class, over every shipped UIAction file.
    -> in_ports[cls][name] = set(files), out_ports[cls][name], attrs[cls][name]"""
    in_ports = defaultdict(lambda: defaultdict(set))
    out_ports = defaultdict(lambda: defaultdict(set))
    attrs = defaultdict(lambda: defaultdict(set))
    parsed = 0
    for f in files:
        try:
            _, nodes, edges, _ = load_graph(f)
        except Exception as ex:                      # a broken shipped file must not hide the others
            print("  warn: cannot parse %s: %s" % (f, ex))
            continue
        parsed += 1
        short = os.path.basename(f)
        cls = {i: n.get("Class") for i, n in nodes.items()}
        for i, n in nodes.items():
            inp = n.find("Inputs")
            if inp is not None:
                for a in inp.attrib:
                    attrs[cls[i]][a].add(short)
        for nin, nout, pin, pout in edges:
            if nin in cls:
                in_ports[cls[nin]][pin].add(short)
            if nout in cls:
                out_ports[cls[nout]][pout].add(short)
    return in_ports, out_ports, attrs, parsed


def validate_manifest(path, p):
    raw = open(path, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf") or raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        p.err("mod.manifest must be UTF-8 without BOM")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as ex:
        p.err("mod.manifest is not valid UTF-8: %s" % ex)
        return
    r = ET.fromstring(raw)
    if r.tag != "kcd_mod":
        p.err("mod.manifest root is <%s>, expected <kcd_mod>" % r.tag)
    want = {"info/name": "KCD DLSS Menu", "info/author": "mrtaxerman", "info/version": "0.6.9",
            "supports/kcd_version": "1.9.*"}
    for k, v in want.items():
        e = r.find(k)
        if e is None or (e.text or "").strip() != v:
            p.err("mod.manifest %s = %r, expected %r" % (k, None if e is None else e.text, v))
    d = r.find("info/description")
    if d is None or not (d.text or "").strip():
        p.err("mod.manifest has no description")
    c = r.find("info/created_on")
    if c is None or not re.fullmatch(r"\d{4}-\d\d-\d\d", (c.text or "").strip()):
        p.err("mod.manifest created_on is not YYYY-MM-DD")
    if r.find(".//modid") is not None:
        p.err("mod.manifest must not contain a modid element")
    if not p.errors:
        p.ok("mod.manifest: UTF-8, name/author/version/created_on/kcd_version as required, no modid")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract-root", default=DEFAULT_EXTRACT, help="extracted game UI files (default %(default)s)")
    ap.add_argument("--original", default=None, help="original MM_AdvancedGraphics.xml (default: <extract-root>/" + ORIG_REL + ")")
    ap.add_argument("--xml", default=os.path.join(HERE, "MM_AdvancedGraphics.xml"))
    ap.add_argument("--manifest", default=os.path.join(HERE, "mod.manifest"))
    ap.add_argument("--out", default=os.path.join(PROJECT, "dist", "mods", MOD_FOLDER))
    a = ap.parse_args()

    p = Problems()
    orig_path = a.original or os.path.join(a.extract_root, ORIG_REL)
    tobii_path = os.path.join(a.extract_root, TOBII_REL)
    for f in (a.xml, a.manifest, orig_path, tobii_path):
        if not os.path.isfile(f):
            print("missing input: " + f)
            return 1

    xml_bytes = open(a.xml, "rb").read()
    orig_bytes = open(orig_path, "rb").read()

    print("== input files")
    print("  modded : %s (%d bytes)" % (a.xml, len(xml_bytes)))
    print("  original: %s (%d bytes, md5 %s)" % (orig_path, len(orig_bytes), hashlib.md5(orig_bytes).hexdigest()))
    if hashlib.md5(orig_bytes).hexdigest() != EXPECTED_ORIG_MD5:
        print("  warn: original md5 differs from the one in FINDINGS_KCD_UI_PAKS.md (%s); the game file may have changed" % EXPECTED_ORIG_MD5)

    print("== manifest")
    validate_manifest(a.manifest, p)

    print("== XML file conventions")
    try:
        xml_bytes.decode("ascii")
        p.ok("pure ASCII (matches encoding=\"us-ascii\" in the declaration)")
    except UnicodeDecodeError as ex:
        p.err("non-ASCII byte in the XML but the declaration says us-ascii: %s" % ex)
    if xml_bytes.count(b"\n") != xml_bytes.count(b"\r\n"):
        p.err("mixed line endings (original is CRLF throughout)")
    else:
        p.ok("CRLF line endings throughout, like the original")
    if xml_bytes.split(b"\r\n", 1)[0] != orig_bytes.split(b"\r\n", 1)[0]:
        p.err("XML declaration line differs from the original")
    if b"<!--" in xml_bytes:
        p.err("XML comment found (the original has none; keep notes in NOTES.md)")

    print("== flowgraph validation")
    try:
        _, nodes, edges, dups = load_graph(a.xml)
        _, onodes, oedges, odups = load_graph(orig_path)
    except ET.ParseError as ex:
        p.err("XML parse error: %s" % ex)
        return finish(p)
    p.ok("XML parses; %d nodes, %d edges (original: %d nodes, %d edges)" % (len(nodes), len(edges), len(onodes), len(oedges)))

    if dups:
        p.err("duplicate node ids in modded file: %s" % sorted(set(dups)))
    else:
        p.ok("node ids are unique")
    if len(set(edges)) != len(edges):
        p.err("duplicate edges in modded file")
    for e in ET.parse(a.xml).getroot().find("Edges"):
        if list(e.attrib) != ["nodeIn", "nodeOut", "portIn", "portOut", "enabled"] or e.get("enabled") != "1":
            p.err("edge %s does not follow the attribute order nodeIn/nodeOut/portIn/portOut/enabled=\"1\"" % (dict(e.attrib),))
            break
    for i, n in nodes.items():
        if not i.isdigit():
            p.err("node id %r is not numeric" % i)

    dangling = [(e, "nodeIn" if e[0] not in nodes else "nodeOut") for e in edges
                if e[0] not in nodes or e[1] not in nodes]
    if dangling:
        for e, which in dangling:
            p.err("edge %s refers to a missing %s" % (e, which))
    else:
        p.ok("every edge's nodeIn and nodeOut exists")

    if p.errors:                      # structural problems: the diff checks below would only crash
        return finish(p)

    max_orig = max(int(i) for i in onodes)
    new_ids = sorted((i for i in nodes if i not in onodes), key=int)
    lost = [i for i in onodes if i not in nodes]
    if lost:
        p.err("original nodes missing from the modded file: %s" % lost)
    changed = [i for i in onodes if i in nodes and canon(onodes[i]) != canon(nodes[i])]
    if changed:
        p.err("original nodes were modified: %s" % changed)
    else:
        p.ok("all %d original nodes are present and unchanged" % len(onodes))
    if not new_ids:
        p.err("no new nodes found")
    else:
        want = [str(max_orig + 1 + k) for k in range(len(new_ids))]
        if new_ids != want:
            p.err("new node ids %s are not the contiguous range %s..%s above the original maximum (%d)"
                  % (new_ids, want[0], want[-1], max_orig))
        else:
            p.ok("%d new node ids %s..%s are unique and above the original max id %d"
                 % (len(new_ids), new_ids[0], new_ids[-1], max_orig))

    for i in new_ids:
        if list(nodes[i].attrib) != ["Id", "Class", "pos", "flags"] or not re.fullmatch(r"-?\d+,-?\d+,0", nodes[i].get("pos", "")):
            p.err("new node %s: expected attributes Id Class pos=\"x,y,0\" flags, got %s" % (i, dict(nodes[i].attrib)))
        if len(nodes[i].findall("Inputs")) != 1 or len(list(nodes[i])) != 1:
            p.err("new node %s: expected exactly one <Inputs .../> child" % i)

    oset, mset = set(oedges), set(edges)
    removed, added = oset - mset, mset - oset
    if removed != ALLOWED_REMOVED_EDGES:
        p.err("removed edges %s, expected exactly %s" % (sorted(removed), sorted(ALLOWED_REMOVED_EDGES)))
    else:
        p.ok("only the AA->SW_OD chain edge (824 -> 557) was removed")
    newset = set(new_ids)
    stray = [e for e in added if e[0] not in newset and e[1] not in newset]
    if stray:
        p.err("added edges that do not touch a new node: %s" % stray)
    else:
        p.ok("%d added edges, every one touches a new node" % len(added))

    print("== port-name check (new nodes only)")
    files = sorted(glob.glob(os.path.join(a.extract_root, "*", "Libs", "UI", "UIActions", "*.xml")))
    in_ports, out_ports, attrs, parsed = port_inventory(files, p)
    tobii_short = os.path.basename(tobii_path)
    print("  port inventory from %d shipped UIAction files (all pak dirs under %s), incl. %s"
          % (parsed, a.extract_root, tobii_short))
    cls = {i: n.get("Class") for i, n in nodes.items()}
    checked = bad = 0
    seen_lines = []
    for nin, nout, pin, pout in sorted(added, key=lambda e: (int(e[0]), int(e[1]), e[2])):
        for node, port, table, kind in ((nin, pin, in_ports, "portIn"), (nout, pout, out_ports, "portOut")):
            c = cls[node]
            where = table[c].get(port)
            checked += 1
            if not where:
                bad += 1
                p.err("%s %r on node %s (%s) is not used for that class in any shipped UIAction file"
                      % (kind, port, node, c))
            else:
                ex = sorted(where - {"MM_AdvancedGraphics.xml"}) or sorted(where)
                seen_lines.append("    %-7s %-9s %-38s %2d file(s), e.g. %s"
                                  % (kind, port, c, len(where), ", ".join(ex[:2])))
    for l in sorted(set(seen_lines)):
        print(l)
    if not bad:
        p.ok("all %d edge-port names on new edges exist for the same Class elsewhere" % checked)
    bad = 0
    for i in new_ids:
        for at in nodes[i].find("Inputs").attrib:
            if not attrs[cls[i]].get(at):
                bad += 1
                p.err("node %s (%s): Inputs attribute %r is not used for that class in any shipped file" % (i, cls[i], at))
    if not bad:
        p.ok("all Inputs attribute names on the %d new nodes exist for the same Class elsewhere" % len(new_ids))

    print("== row consistency")
    ROWS = {"SW_DLSS": (["0", "1", "2", "3", "4", "5", "6"], "r_DLSSMode"), "SW_DLSSPRESET": (["0", "1", "2"], "r_DLSSPreset")}
    rows = [i for i in new_ids if cls[i] == "UI:Functions:MainMenu:AddChoicesButton"]
    btns = sorted(nodes[i].find("Inputs").get("buttonId") for i in rows)
    if btns != sorted(ROWS):
        p.err("expected new AddChoicesButton rows %s, found %s" % (sorted(ROWS), btns))
    for bid, (want_ids, cvar) in ROWS.items():
        opts = [i for i in new_ids if cls[i] == "UI:Functions:MainMenu:AddChoiceOption" and nodes[i].find("Inputs").get("buttonId") == bid]
        ids_opts = [nodes[i].find("Inputs").get("choiceId") for i in opts]
        if ids_opts != want_ids:
            p.err("row %s: choice ids are %s, expected %s in order" % (bid, ids_opts, want_ids))
        else:
            p.ok("row %s with options %s" % (bid, ", ".join(opts)))
        cv = [i for i in nodes if cls[i] == "Debug:ConsoleVariable" and nodes[i].find("Inputs").get("CVar") == cvar]
        if len(cv) != 1 or cv[0] not in newset:
            p.err("expected exactly one new Debug:ConsoleVariable with CVar=%s, found %s" % (cvar, cv))
        else:
            p.ok("exactly one Debug:ConsoleVariable (node %s) with CVar %s, Value=%r" % (cv[0], cvar, nodes[cv[0]].find("Inputs").get("Value")))

    if p.errors:
        return finish(p)

    print("== build")
    out_mod = a.out
    out_data = os.path.join(out_mod, "Data")
    os.makedirs(out_data, exist_ok=True)
    manifest_bytes = open(a.manifest, "rb").read()
    pak_path = os.path.join(out_data, PAK_NAME)
    tmp = pak_path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        zi = zipfile.ZipInfo(PAK_ENTRY, date_time=ZIP_DATE)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0o100644 << 16
        zi.create_system = 3
        z.writestr(zi, xml_bytes)
    os.replace(tmp, pak_path)
    man_path = os.path.join(out_mod, "mod.manifest")
    with open(man_path, "wb") as f:
        f.write(manifest_bytes)

    # read back
    with zipfile.ZipFile(pak_path) as z:
        names = z.namelist()
        if names != [PAK_ENTRY]:
            p.err("pak entries are %s" % names)
        back = z.read(PAK_ENTRY)
        info = z.getinfo(PAK_ENTRY)
        if z.testzip() is not None:
            p.err("zip CRC test failed")
        if back != xml_bytes:
            p.err("pak content differs from the source XML")
        if info.compress_type != zipfile.ZIP_DEFLATED:
            p.err("entry is not deflated")
    pak_bytes = open(pak_path, "rb").read()
    print("  wrote %s" % man_path)
    print("    size %d bytes   sha256 %s" % (len(manifest_bytes), sha256(manifest_bytes)))
    print("  wrote %s" % pak_path)
    print("    size %d bytes   sha256 %s" % (len(pak_bytes), sha256(pak_bytes)))
    print("    entry %s: %d -> %d bytes (deflate), sha256 %s"
          % (PAK_ENTRY, info.file_size, info.compress_size, sha256(back)))
    return finish(p)


def finish(p):
    if p.errors:
        print("\nVALIDATION FAILED (%d problem(s)); see FAIL lines above." % len(p.errors))
        return 1
    print("\nBUILD OK. Test install: copy dist/mods/%s/ into <game>/Mods/ and, if <game>/Mods/mod_order.txt exists,"
          " append the line %s" % (MOD_FOLDER, MOD_FOLDER))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Re-parse the BUILT pak and print the wiring of the two DLSS rows so a human can check it.

Run:  python3 -I verify_menu_mod.py [--pak PATH]

Default pak: <project>/dist/mods/KCDDLSS/Data/kcddlss_menu.pak (see build_menu_mod.py).
Reads only the pak and the mod.manifest beside it. Exit status 1 if an expectation below fails.
Rows (page order ... SW_AA, SW_DLSS, SW_DLSSPRESET, SW_OD ...):
  SW_DLSS        "DLSS / Upscaling"  cvar r_DLSSMode    0 Off, 1 Quality, 2 Balanced, 3 Performance, 4 Ultra Perf (reset 3)
  SW_DLSSPRESET  "DLSS Model"        cvar r_DLSSPreset  0 Transformer, 1 CNN (reset 0)
"""
import argparse
import hashlib
import os
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_PAK = os.path.join(PROJECT, "dist", "mods", "KCDDLSS", "Data", "kcddlss_menu.pak")
ENTRY = "Libs/UI/UIActions/MM_AdvancedGraphics.xml"
NBSP = " "
ROWS = [  # button, cvar, uiText, choices, previous row, next row, reset value
    ("SW_DLSS", "r_DLSSMode", "DLSS / Upscaling",
     [("0", "Off"), ("1", "Ultra Quality"), ("2", "Quality"), ("3", "Balanced"), ("4", "Performance"), ("5", "Ultra Perf"), ("6", "Unsupported")],
     "SW_AA", "SW_DLSSPRESET", "4"),
    ("SW_DLSSPRESET", "r_DLSSPreset", "DLSS Model",
     [("0", "Transformer"), ("1", "CNN"), ("2", "Unsupported")],
     "SW_DLSS", "SW_OD", "0"),
]


def short(cls):
    return cls.split(":")[-1] if cls else "?"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pak", default=DEFAULT_PAK)
    a = ap.parse_args()
    fails = []

    def check(cond, msg):
        print("  %s %s" % ("ok:  " if cond else "FAIL:", msg))
        if not cond:
            fails.append(msg)

    # ---- pak
    print("== pak %s" % a.pak)
    raw_pak = open(a.pak, "rb").read()
    print("  size %d bytes, sha256 %s" % (len(raw_pak), hashlib.sha256(raw_pak).hexdigest()))
    with zipfile.ZipFile(a.pak) as z:
        for i in z.infolist():
            print("  entry %s  method=%s  %d -> %d bytes  crc32=%08x" % (
                i.filename, {8: "deflate", 0: "stored"}.get(i.compress_type, i.compress_type),
                i.file_size, i.compress_size, i.CRC))
        check(z.namelist() == [ENTRY], "pak holds exactly the entry %s" % ENTRY)
        check(z.testzip() is None, "zip CRCs are good")
        data = z.read(ENTRY)
    print("  entry sha256 %s" % hashlib.sha256(data).hexdigest())
    check(b"\xc2\xa0" not in data and all(c < 128 for c in data), "entry is pure ASCII (non-breaking space written as &#160;)")
    man = os.path.join(os.path.dirname(os.path.dirname(a.pak)), "mod.manifest")
    if os.path.isfile(man):
        r = ET.parse(man).getroot()
        print("  manifest: %s" % ", ".join("%s=%s" % (k, r.findtext(k)) for k in
              ("info/name", "info/author", "info/version", "info/created_on", "supports/kcd_version")))

    root = ET.fromstring(data)
    nodes = {n.get("Id"): n for n in root.find("Nodes")}
    edges = [(e.get("nodeIn"), e.get("nodeOut"), e.get("portIn"), e.get("portOut")) for e in root.find("Edges")]
    cls = {i: n.get("Class") for i, n in nodes.items()}

    def inp(i, k, d=""):
        e = nodes[i].find("Inputs")
        return d if e is None else e.get(k, d)

    def label(i):
        c = cls[i]
        key = (inp(i, "buttonId") or inp(i, "id") or inp(i, "Idx") or inp(i, "CVar"))
        if c == "UI:Functions:MainMenu:AddChoiceOption":
            key = "%s=%s" % (inp(i, "buttonId"), inp(i, "choiceId"))
        return "%s %s%s" % (i, short(c), "[%s]" % key if key else "")

    def src(node, port):
        return sorted((nout, pout) for nin, nout, pin, pout in edges if nin == node and pin == port)

    # ---- position in the creation chain
    outs = defaultdict(list)
    for nin, nout, pin, pout in edges:
        if pin == "Call" and pout == "OnCall":
            outs[nout].append(nin)
    start = [i for i in nodes if cls[i] == "UI:Functions:MainMenu:ClearAll"]
    order, seen, stack = [], set(), list(start)
    while stack:
        i = stack.pop(0)
        if i in seen:
            continue
        seen.add(i)
        if cls[i] == "UI:Functions:MainMenu:AddChoicesButton":
            order.append(inp(i, "buttonId"))
        elif cls[i] in ("UI:Functions:MainMenu:AddValueButton", "UI:Functions:MainMenu:AddButton"):
            order.append(inp(i, "buttonId") or inp(i, "id"))
        stack = outs.get(i, []) + stack            # depth first, in file order
    print("\n== page creation order (button ids, following Call/OnCall from ClearAll)")
    print("  " + " > ".join(order))

    all_mine = set()
    for BUTTON, CVAR, UITEXT, CHOICES, PREV, NEXT, RESET in ROWS:
        print("\n######## row %s (%s)" % (BUTTON, CVAR))
        mine = [i for i in nodes
                if BUTTON in (inp(i, "buttonId"), inp(i, "id")) or (cls[i] == "Debug:ConsoleVariable" and inp(i, "CVar") == CVAR)]
        mine.sort(key=int)
        mset = set(mine)
        all_mine |= mset
        print("== nodes of the row (%d)" % len(mine))
        for i in mine:
            n = nodes[i]
            print("  %-4s %-40s pos=%s" % (i, cls[i], n.get("pos")))
            for k, v in n.find("Inputs").attrib.items():
                if v != "" or k in ("tooltip",):
                    print("         %s=%r" % (k, v))

        touching = [e for e in edges if e[0] in mset or e[1] in mset]
        print("\n== edges touching the row (%d); format  <source>.<outPort>  ->  <target>.<inPort>" % len(touching))
        for nin, nout, pin, pout in touching:
            mark = "   " if (nin in mset and nout in mset) else "ext"
            print("  %s %-44s.%-9s -> %-44s.%s" % (mark, label(nout), pout, label(nin), pin))
        print("  (ext = other end is an original node)")

        print("\n== flows")
        cur = [i for i in mine if cls[i] == "Debug:ConsoleVariable"]
        cv = cur[0] if cur else None
        setc = [i for i in mine if cls[i] == "UI:Functions:MainMenu:SetChoice"]
        getc = [i for i in mine if cls[i] == "UI:Functions:MainMenu:GetChoice"]
        if cv:
            print("  page open : %s" % "; ".join("%s.%s -> %s.Get" % (label(s), po, label(cv)) for s, po in src(cv, "Get")))
            if setc:
                print("              %s.CurValue -> %s.Call + .choiceId (shows the cvar value in the row)" % (label(cv), label(setc[0])))
            print("  apply     : %s" % "; ".join("%s.%s -> %s.Call" % (label(s), po, label(getc[0])) for s, po in src(getc[0], "Call")) if getc else "  apply     : (none)")
            if getc:
                print("              %s.OnCall -> %s.Set ; %s.ReturnVal -> %s.Value" % (label(getc[0]), label(cv), label(getc[0]), label(cv)))
            print("  reset     : %s  (Value constant = %r)" % (
                "; ".join("%s.%s -> %s.Set" % (label(s), po, label(cv)) for s, po in src(cv, "Set") if s not in mset),
                inp(cv, "Value")))

        print("\n== expectations")
        check(len(cur) == 1, "exactly one Debug:ConsoleVariable on %s (node %s)" % (CVAR, cv))
        check(BUTTON in order and order.index(BUTTON) > 0 and order[order.index(BUTTON) - 1] == PREV
              and order.index(BUTTON) + 1 < len(order) and order[order.index(BUTTON) + 1] == NEXT,
              "row order is ... %s, %s, %s ..." % (PREV, BUTTON, NEXT))
        btn = [i for i in mine if cls[i] == "UI:Functions:MainMenu:AddChoicesButton"]
        opt = [i for i in mine if cls[i] == "UI:Functions:MainMenu:AddChoiceOption"]
        check(len(btn) == 1 and inp(btn[0], "uiText") == UITEXT, "button uiText is %r" % UITEXT)
        check([(inp(i, "choiceId"), inp(i, "uiText")) for i in opt] == CHOICES,
              "choices %s (node order = list order)" % ", ".join("%s %s" % c for c in CHOICES).replace(NBSP, "<nbsp>"))
        check(all(inp(i, "containerIndex") == "0" for i in mine if cls[i].startswith("UI:")),
              "all row nodes use containerIndex 0 (same as the other rows)")
        if cv and setc and getc and btn:
            chain = [btn[0]] + opt
            ok = all((b, a_, "Call", "OnCall") in edges for a_, b in zip(chain, chain[1:]))
            check(ok, "creation chain %s is linked" % " -> ".join(chain))
            before = [nout for nin, nout, pin, pout in edges if nin == btn[0] and pin == "Call"]
            after = [nin for nin, nout, pin, pout in edges if nout == opt[-1] and pout == "OnCall"]
            check(len(before) == 1 and inp(before[0], "buttonId") == PREV and
                  len(after) == 1 and inp(after[0], "buttonId") == NEXT,
                  "chain enters from the %s row's last option (%s) and leaves to the %s row (%s)" % (PREV, before, NEXT, after))
            check(set(src(setc[0], "Call")) == {(cv, "CurValue")} and set(src(setc[0], "choiceId")) == {(cv, "CurValue")},
                  "SetChoice %s gets Call and choiceId from CurValue" % BUTTON)
            check(inp(setc[0], "id") == BUTTON, "SetChoice targets %s" % BUTTON)
            check(set(src(cv, "Set")) >= {(getc[0], "OnCall")} and src(cv, "Value") == [(getc[0], "ReturnVal")],
                  "Apply: GetChoice.OnCall -> Set and GetChoice.ReturnVal -> Value")
            get_src = src(cv, "Get")
            check(len(get_src) == 1 and cls[get_src[0][0]] == "UI:Functions:MainMenu:AddButton"
                  and inp(get_src[0][0], "id") == "IDD_Back" and get_src[0][1] == "OnCall"
                  and not outs.get(get_src[0][0]),
                  "Get is triggered by the last AddButton (IDD_Back) of the creation chain, like Tobii node 152")
            g_in = src(getc[0], "Call")
            check(len(g_in) == 1 and cls[g_in[0][0]] == "Logic:Any" and g_in[0][1] == "out",
                  "GetChoice is called from a Logic:Any 'out' (%s)" % ", ".join(label(x) for x, _ in g_in))
            also = [t for t in (nin for nin, nout, pin, pout in edges if nout == g_in[0][0] and pout == "out" and pin == "Call")
                    if cls[t] == "UI:Functions:MainMenu:GetChoice"]
            check(len(also) >= 14 and getc[0] in also, "that Logic:Any also calls the other %d GetChoice nodes" % (len(also) - 1))
            reset_src = [s for s, po in src(cv, "Set") if s not in mset]
            check(len(reset_src) == 1 and cls[reset_src[0]] == "UI:Events:MainMenu:OnConfirm"
                  and inp(reset_src[0], "Idx") == "RESET_ADVANCED_GRAPHIC" and inp(cv, "Value") == RESET,
                  "Reset: confirmed RESET_ADVANCED_GRAPHIC -> Set with constant Value %s" % RESET)

    # ---- both rows together
    print("\n######## both rows")
    ids = sorted(int(i) for i in all_mine)
    check(ids == list(range(ids[0], ids[0] + len(ids))), "the new node ids are contiguous (%d..%d)" % (ids[0], ids[-1]))
    check(all(int(i) < ids[0] for i in nodes if i not in all_mine), "all original node ids are below the new ones")
    getcs = [i for i in all_mine if cls[i] == "UI:Functions:MainMenu:GetChoice"]
    check(len({src(g, "Call")[0][0] for g in getcs if src(g, "Call")}) == 1, "both GetChoice nodes hang off the same Logic:Any (one Apply)")
    print()
    if fails:
        print("VERIFY FAILED (%d)" % len(fails))
        return 1
    print("VERIFY OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

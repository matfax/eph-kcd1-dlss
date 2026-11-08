#!/usr/bin/env bash
# Builds dist/KCDDLSS-<version>.7z (the archive for Nexus / GitHub Releases).
# usage: release/build_release.sh <version> UAL_DINPUT8_DLL UAL_LICENSE NVNGX_DLSS_DLL DLSS_LICENSE
#   UAL_DINPUT8_DLL = dinput8.dll from Ultimate ASI Loader v10.0.2 (Ultimate-ASI-Loader-NoPDB_x64.zip), shipped as version.dll
#   UAL_LICENSE     = that project's LICENSE (MIT)
#   NVNGX_DLSS_DLL  = nvngx_dlss.dll (DLSS 310.x; version read from the file by the script)
#   DLSS_LICENSE    = NVIDIA RTX SDKs licence text (the DLSS SDK's LICENSE.txt)
# Needs tools/asi/out/KCDDLSS.asi (run tools/asi/build.sh first; or ASI=<file> env to use another binary), tools/windows/KCDDLSS.ini and 7z.
# Fills @VERSION@ @ASI_SHA@ @UAL_SHA@ @DLSS_SHA@ @ASI_SIZE@ @UAL_SIZE@ @DLSS_SIZE@ @DLSS_VERSION@, inlines launch_option.py.
# .bat/.ini/README get CRLF; .sh stay LF and executable.
set -euo pipefail
[ $# -eq 5 ] || { echo "usage: $0 <version> UAL_DINPUT8_DLL UAL_LICENSE NVNGX_DLSS_DLL DLSS_LICENSE"; exit 2; }
VER=$1; UAL=$(realpath "$2"); LIC=$(realpath "$3"); DLSS=$(realpath "$4"); DLIC=$(realpath "$5")
cd "$(dirname "$0")/.."
R=release; OUT=dist/KCDDLSS-$VER.7z; S=dist/single/KCDDLSS
ASI=${ASI:-tools/asi/out/KCDDLSS.asi}; DASI=${DEBUG_ASI:-tools/asi/out/KCDDLSS-debug.asi}; INI=tools/windows/KCDDLSS.ini   # ASI=path overrides the plugin binary (release builds vs. a dev build in out/)
[ -f "$ASI" ] || { echo "$ASI missing: run tools/asi/build.sh first"; exit 1; }
[ -f "$DASI" ] || { echo "$DASI missing: run tools/asi/build.sh first (debug build)"; exit 1; }
[ "$(sha256sum "$UAL" | cut -d' ' -f1)" = 57ec56390c92a18b82f58855e63c93985e254d1e29d5f75cbc28dc08f96c8a12 ] ||
  { echo "$UAL is not dinput8.dll of Ultimate ASI Loader v10.0.2 (x64)"; exit 1; }
DLSS_VERSION=$(python3 -I - "$DLSS" <<'PY'
import re,sys
b=open(sys.argv[1],'rb').read(); m=re.search(rb'F\x00i\x00l\x00e\x00V\x00e\x00r\x00s\x00i\x00o\x00n\x00(?:\x00\x00)+((?:[0-9.,]\x00)+)',b)
v=m.group(1).decode('utf-16-le').replace(',','.').split('.') if m else []
print('.'.join(v[:3]) if len(v)>=3 else 'unknown')
PY
)
ASI_SHA=$(sha256sum "$ASI" | cut -d' ' -f1); UAL_SHA=$(sha256sum "$UAL" | cut -d' ' -f1); DLSS_SHA=$(sha256sum "$DLSS" | cut -d' ' -f1)
rm -rf dist/single; mkdir -p "$S/install"
mkdir -p "$S/debug"; cp -p "$DASI" "$S/debug/KCDDLSS.asi"; cp -p "$ASI" "$S/install/KCDDLSS.asi"; cp -p "$UAL" "$S/install/version.dll"; cp -p "$DLSS" "$S/install/nvngx_dlss.dll"
sed 's/\r$//; s/$/\r/' "$INI" > "$S/install/KCDDLSS.ini"
sed 's/\r$//; s/$/\r/' "$LIC" > "$S/install/Ultimate-ASI-Loader-LICENSE.txt"
sed 's/\r$//; s/$/\r/' "$DLIC" > "$S/install/NVIDIA-DLSS-LICENSE.txt"
MENU=dist/mods/KCDDLSS   # options-menu row (tools/menu-mod/build_menu_mod.py): Mods/KCDDLSS/{mod.manifest,Data/kcddlss_menu.pak}
[ -f "$MENU/mod.manifest" ] && [ -f "$MENU/Data/kcddlss_menu.pak" ] || { echo "$MENU is missing: run tools/menu-mod/build_menu_mod.py first"; exit 1; }
mkdir -p "$S/install/Mods/KCDDLSS/Data"; cp -p "$MENU/Data/kcddlss_menu.pak" "$S/install/Mods/KCDDLSS/Data/"
python3 -I - "$MENU/mod.manifest" "$VER" > "$S/install/Mods/KCDDLSS/mod.manifest" <<'PY'
import re,sys
s=open(sys.argv[1]).read(); s2=re.sub(r'(<version>)[^<]*(</version>)', r'\g<1>'+sys.argv[2]+r'\g<2>', s)
sys.stdout.write(s2.replace('\r\n','\n').replace('\n','\r\n'))
PY
fill() { sed -e "s/@VERSION@/$VER/g; s/@ASI_SHA@/$ASI_SHA/; s/@UAL_SHA@/$UAL_SHA/; s/@DLSS_SHA@/$DLSS_SHA/; s/@ASI_SIZE@/$(stat -c %s "$ASI")/; s/@UAL_SIZE@/$(stat -c %s "$UAL")/; s/@DLSS_SIZE@/$(stat -c %s "$DLSS")/; s/@DLSS_VERSION@/$DLSS_VERSION/g" "$1"; }
for f in Install-Windows.bat Uninstall-Windows.bat README.txt OPTISCALER.txt; do fill "$R/$f" | sed 's/\r$//; s/$/\r/' > "$S/$f"; done
for f in Install-Linux-SteamDeck.sh Uninstall-Linux-SteamDeck.sh; do
  fill "$R/$f" | python3 -I -c 'import sys; s=sys.stdin.read(); py=open(sys.argv[1]).read().rstrip("\n"); assert s.count("@LAUNCH_OPTION_PY@\n")==1; sys.stdout.write(s.replace("@LAUNCH_OPTION_PY@\n", py+"\n"))' "$R/launch_option.py" > "$S/$f"
  chmod 755 "$S/$f"; bash -n "$S/$f"
done
! grep -l '@[A-Z_]*@' "$S"/*.sh "$S"/*.bat "$S"/*.txt
mkdir -p dist; rm -f "$OUT"; (cd dist/single && 7z a -t7z -mx=9 "$OLDPWD/$OUT" KCDDLSS >/dev/null)
7z t "$OUT" >/dev/null && echo "built $OUT $(stat -c %s "$OUT") bytes, sha256 $(sha256sum "$OUT" | cut -c1-12), DLSS $DLSS_VERSION"

#!/usr/bin/env python3
"""Derives release/Install-Linux-SteamDeck.sh and Uninstall-Linux-SteamDeck.sh from the 30 FPS Grass Fix release scripts
(same game-finding, Proton prefix and Steam launch-option logic). usage: gen_linux_scripts.py <grass-release-dir>"""
import sys
g = sys.argv[1]
def make(src, edits, out):
    s = open(f'{g}/{src}').read()
    for old, new, cnt in edits:
        assert (s.count(old) == cnt) if cnt else s.count(old) >= 1, (src, s.count(old), old[:60])
        s = s.replace(old, new)
    open(out, 'w').write(s)
common = [('GAF_TERM', 'KDL_TERM', None), ('grassfix-backup', 'kcddlss-backup', None), ('grassfix-tmp', 'kcddlss-tmp', None)]
make('Install-Linux-SteamDeck.sh', common + [
 ('# 30 FPS Grass Fix 1.0.0 - installer for Steam Deck / Linux (Proton).', '# DLSS for Kingdom Come: Deliverance @VERSION@ - installer for Steam Deck / Linux (Proton).', 1),
 ('''#   2. Copies install/KCDGrassFix.asi and install/version.dll (Ultimate ASI Loader) to Bin/Win64,
#      next to KingdomCome.exe. A version.dll that is already there is left alone.''',
  '''#   2. Copies install/KCDDLSS.asi (the mod), install/KCDDLSS.ini (settings, kept if present),
#      install/nvngx_dlss.dll (NVIDIA DLSS, kept if present) and install/version.dll (Ultimate ASI
#      Loader) to Bin/Win64, next to KingdomCome.exe. A version.dll already there is left alone.
#      A standalone KCDGrassFix.asi (30 FPS Grass Fix) is renamed to .off: this mod contains it.''', 1),
 ('''#   5. Copies the uninstaller to the game folder as 30FPSGrassFix-Uninstall.sh.
# No game file is changed.''',
  '''#   5. Copies the uninstaller to the game folder as KCDDLSS-Uninstall.sh.
# No game file is changed. The mod sets the game up itself at every start (no user.cfg edits).
# NVIDIA: DLSS runs through Proton's NVAPI bridge (on by default in Proton 9+). AMD / Intel: see
# OPTISCALER.txt (FSR / XeSS through OptiScaler, not included here).''', 1),
 ('''ASI_SHA=@ASI_SHA@   # install/KCDGrassFix.asi
UAL_SHA=@UAL_SHA@   # install/version.dll''', '''ASI_SHA=@ASI_SHA@   # install/KCDDLSS.asi
UAL_SHA=@UAL_SHA@   # install/version.dll
DLSS_SHA=@DLSS_SHA@   # install/nvngx_dlss.dll''', 1),
 ('echo "30 FPS Grass Fix 1.0.0 - install"', 'echo "DLSS for Kingdom Come: Deliverance @VERSION@ - install"', 1),
 ('''[ -f "$SELF/install/KCDGrassFix.asi" ] && [ -f "$SELF/install/version.dll" ] || die "The install folder is missing from $SELF."
[ "$(sha "$SELF/install/KCDGrassFix.asi")" = "$ASI_SHA" ] || die "install/KCDGrassFix.asi is damaged. Download the mod again."
[ "$(sha "$SELF/install/version.dll")" = "$UAL_SHA" ] || die "install/version.dll is damaged. Download the mod again."

# 1. The two files next to KingdomCome.exe
cp -f "$SELF/install/KCDGrassFix.asi" "$B/KCDGrassFix.asi" || die "Could not copy KCDGrassFix.asi to $B."
echo "Plugin: Bin/Win64/KCDGrassFix.asi copied."''',
  '''for f in KCDDLSS.asi KCDDLSS.ini nvngx_dlss.dll version.dll; do [ -f "$SELF/install/$f" ] || die "install/$f is missing from $SELF."; done
[ "$(sha "$SELF/install/KCDDLSS.asi")" = "$ASI_SHA" ] || die "install/KCDDLSS.asi is damaged. Download the mod again."
[ "$(sha "$SELF/install/version.dll")" = "$UAL_SHA" ] || die "install/version.dll is damaged. Download the mod again."
[ "$(sha "$SELF/install/nvngx_dlss.dll")" = "$DLSS_SHA" ] || die "install/nvngx_dlss.dll is damaged. Download the mod again."

# 1. The files next to KingdomCome.exe
cp -f "$SELF/install/KCDDLSS.asi" "$B/KCDDLSS.asi" || die "Could not copy KCDDLSS.asi to $B."
rm -f "$B/KCDDLSS.log"
echo "Mod: Bin/Win64/KCDDLSS.asi copied."
if [ -e "$B/KCDDLSS.ini" ]; then echo "Settings: Bin/Win64/KCDDLSS.ini is already there. Kept (delete it to get the defaults)."
else cp -f "$SELF/install/KCDDLSS.ini" "$B/KCDDLSS.ini" || die "Could not copy KCDDLSS.ini to $B."; echo "Settings: Bin/Win64/KCDDLSS.ini copied."; fi
if [ -e "$B/nvngx_dlss.dll" ]; then echo "DLSS: Bin/Win64/nvngx_dlss.dll is already there. Kept."
else cp -f "$SELF/install/nvngx_dlss.dll" "$B/nvngx_dlss.dll" || die "Could not copy nvngx_dlss.dll to $B."
     cp -f "$SELF/install/NVIDIA-DLSS-LICENSE.txt" "$B/NVIDIA-DLSS-LICENSE.txt" 2>/dev/null; echo "DLSS: Bin/Win64/nvngx_dlss.dll copied (NVIDIA DLSS @DLSS_VERSION@)."; fi
if [ -e "$B/KCDGrassFix.asi" ]; then mv -f "$B/KCDGrassFix.asi" "$B/KCDGrassFix.asi.off" && echo "Grass: standalone 30 FPS Grass Fix set aside as KCDGrassFix.asi.off (this mod contains it)."; fi''', 1),
 ('If it is an ASI loader, the fix loads through it. Check Bin/Win64/KCDGrassFix.log after a start.', 'If it is an ASI loader, the mod loads through it. Check Bin/Win64/KCDDLSS.log after a start.', 1),
 ('Steam launch option: not added. The fix still loads through the Proton prefix setting.', 'Steam launch option: not added. The mod still loads through the Proton prefix setting.', 1),
 ('IMPORTANT: the fix will not load yet.', 'IMPORTANT: the mod will not load yet.', 1),
 ('''cp -f "$SELF/Uninstall-Linux-SteamDeck.sh" "$GAME/30FPSGrassFix-Uninstall.sh" &&
  echo "Uninstaller copied to the game folder: 30FPSGrassFix-Uninstall.sh"
echo
echo "Done. Start the game. Bin/Win64/KCDGrassFix.log then says \\"grass fix applied\\"."
echo "If that file does not appear, the loader did not start: see README.txt."''',
  '''cp -f "$SELF/Uninstall-Linux-SteamDeck.sh" "$GAME/KCDDLSS-Uninstall.sh" &&
  echo "Uninstaller copied to the game folder: KCDDLSS-Uninstall.sh"
echo
echo "Done. Start the game. Bin/Win64/KCDDLSS.log then shows \\"dlss: CreateFeature ... result 0x1\\" once the menu is up."
echo "If that file does not appear, the loader did not start: see README.txt. \\"no usable NGX core\\" in the log on an"
echo "NVIDIA card: add PROTON_ENABLE_NVAPI=1 to the launch options. AMD / Intel: see OPTISCALER.txt."
echo "Settings (DLSS mode, preset, sharpness): Bin/Win64/KCDDLSS.ini, read at every start."''', 1),
], 'release/Install-Linux-SteamDeck.sh')
make('Uninstall-Linux-SteamDeck.sh', common + [
 ('''# 30 FPS Grass Fix 1.0.0 - uninstaller for Steam Deck / Linux (Proton).
#   bash 30FPSGrassFix-Uninstall.sh            (in the game folder, put there by the installer)''',
  '''# DLSS for Kingdom Come: Deliverance @VERSION@ - uninstaller for Steam Deck / Linux (Proton).
#   bash KCDDLSS-Uninstall.sh                  (in the game folder, put there by the installer)''', 1),
 ('#   2. Deletes Bin/Win64/KCDGrassFix.asi and KCDGrassFix.log.',
  '''#   2. Deletes Bin/Win64/KCDDLSS.asi, KCDDLSS.ini, KCDDLSS.log and the nvngx_dlss.dll this mod installed;
#      renames KCDGrassFix.asi.off back to KCDGrassFix.asi (standalone 30 FPS Grass Fix).''', 1),
 ('UAL_SHA=@UAL_SHA@   # the version.dll this mod installs', 'UAL_SHA=@UAL_SHA@   # the version.dll this mod installs\nDLSS_SHA=@DLSS_SHA@   # the nvngx_dlss.dll this mod installs', 1),
 ('echo "30 FPS Grass Fix 1.0.0 - uninstall"', 'echo "DLSS for Kingdom Come: Deliverance @VERSION@ - uninstall"', 1),
 ('rm -f "$B/KCDGrassFix.asi" "$B/KCDGrassFix.log" && echo "Plugin: Bin/Win64/KCDGrassFix.asi removed."',
  '''rm -f "$B/KCDDLSS.asi" "$B/KCDDLSS.ini" "$B/KCDDLSS.log" "$B/KCDDLSS.cmd" "$B"/KCDDLSS_*.ppm && echo "Mod: Bin/Win64/KCDDLSS.asi and its settings removed."
if [ -e "$B/nvngx_dlss.dll" ]; then
  if [ "$(sha "$B/nvngx_dlss.dll")" = "$DLSS_SHA" ]; then rm -f "$B/nvngx_dlss.dll" "$B/NVIDIA-DLSS-LICENSE.txt" && echo "DLSS: Bin/Win64/nvngx_dlss.dll removed."
  else echo "DLSS: Bin/Win64/nvngx_dlss.dll is not the file this mod installs. Left alone."; fi
fi
if [ -e "$B/KCDGrassFix.asi.off" ] && [ ! -e "$B/KCDGrassFix.asi" ]; then mv -f "$B/KCDGrassFix.asi.off" "$B/KCDGrassFix.asi" && echo "Grass: standalone 30 FPS Grass Fix restored (KCDGrassFix.asi)."; fi''', 1),
 ('''rm -f "$GAME/30FPSGrassFix-Uninstall.sh"
echo
echo "Done. The game is back to its original grass animation."''',
  '''rm -f "$GAME/KCDDLSS-Uninstall.sh"
echo
echo "Done. The game renders as before (its own TAA and upscaling settings apply again)."''', 1),
], 'release/Uninstall-Linux-SteamDeck.sh')
print('linux scripts written')

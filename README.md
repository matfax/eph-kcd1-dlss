# Native DLSS Support - True Upscaling (BETA)

A plugin for **Kingdom Come: Deliverance** (the first game) that puts NVIDIA DLSS Super Resolution where the game's own "native resolution" stretch is. The scene renders at a lower resolution and DLSS builds the full-resolution picture from it, with the game's camera and object motion vectors, a camera jitter added by the mod and texture detail kept sharp. Two new rows in Options > Advanced Graphics switch it live. Windows, Steam Deck and Linux. On AMD and Intel cards the same hook drives FSR 3.1, FSR 4 or XeSS through [OptiScaler](https://github.com/optiscaler/OptiScaler).

This is a **beta**. It works on the author's machines (RTX 4070 on Windows, RX 9070 XT with OptiScaler FSR 4 on Bazzite, Steam Deck). If something breaks for you, open an issue or reply on Nexus with your setup (GPU, driver, OS or Proton version, other mods), what happened, a screenshot if it is visible and the file `Bin\Win64\KCDDLSS.log`.

How it works in detail: [HOW-IT-WORKS.md](HOW-IT-WORKS.md).

## What it does

- The game has no modern upscaler. Its "native resolution" option renders at 720p or 900p and stretches that to the screen with a plain filter. The mod replaces that stretch with DLSS: at Performance the game renders 1920x1080 and the 4K picture is sharper than the game's own 1080p, with clean edges and no TAA blur.
- Modes: Ultra Quality (0.83 of the screen size, the mod's own), Quality (0.67), Balanced (0.58), Performance (0.5), Ultra Performance (0.33), Off. Render sizes follow NVIDIA's values; Ultra Quality is for DLSS's anti-aliasing with the least upscaling. There is no DLAA mode.
- Models: the DLSS 4 Transformer model (default) or the classic CNN model.
- Both are rows in Options > Advanced Graphics ("DLSS / Upscaling", "DLSS Model") and lines in `Bin\Win64\KCDDLSS.ini`. On a PC without an upscaler (no NVIDIA card and no OptiScaler) both rows read "Unsupported" and the game renders at native size.
- Built in: the [30 FPS Grass Fix](https://github.com/qahtni/kcd1-30fps-grass-fix) (grass moves at your real frame rate) and the removal of the forced sharpening in conversations.
- Nothing on disk is changed. All game settings the mod needs (native-resolution output, game AA off, motion vectors on, full-resolution GI cone tracing) are set in memory at every start and whenever the settings menu puts the game's own values back.

## Download

`KCDDLSS-BETA-2.7z` from the [Releases page](https://github.com/qahtni/kcd1-dlss/releases/latest) or Nexus Mods. It contains:

- `install/KCDDLSS.asi`: the mod. `install/KCDDLSS.ini`: its settings.
- `install/nvngx_dlss.dll`: NVIDIA DLSS 310.9.1 with its licence.
- `install/version.dll`: [Ultimate ASI Loader](https://github.com/ThirteenAG/Ultimate-ASI-Loader) 10.0.2 by ThirteenAG (MIT licence, included). It loads `.asi` plugins.
- `install/Mods/KCDDLSS`: the two menu rows, a small UI mod for the game's `Mods` folder.
- `debug/KCDDLSS.asi`: the same mod with full diagnostics in the log, for bug reports only.
- Installers and uninstallers for Windows and Steam Deck / Linux, plain text. `OPTISCALER.txt` for AMD and Intel cards.

## Requirements

- Kingdom Come: Deliverance, Steam version 1.9.8, 64-bit DX11. On any other version the plugin finds nothing it knows, changes nothing and says so in its log.
- NVIDIA GeForce RTX 20 series or newer with a current driver. Other cards: OptiScaler, see `release/OPTISCALER.txt`.
- Steam Deck / Linux: Proton 9 or newer. DLSS needs the NVIDIA driver; AMD and Intel use OptiScaler, which on Linux is one Proton switch (a GE-Proton or Proton-CachyOS build with OptiScaler), nothing to copy.

## Install

### Windows
1. Extract the archive anywhere, for example to Downloads.
2. Double-click **Install-Windows.bat**.

It finds the game in your Steam libraries (else the GOG / Epic default folders), copies the four files to `Bin\Win64` and the menu rows to `Mods\KCDDLSS`. If it can't find the game, drag the game folder onto the installer. A standalone 30 FPS Grass Fix is set aside (`KCDGrassFix.asi.off`), this mod contains the same fix.

### Steam Deck / Linux
1. Desktop Mode, extract the archive anywhere.
2. Exit Steam (right-click the Steam icon in the taskbar > Exit Steam).
3. Right-click an empty spot in the extracted folder > Open Terminal Here, run `bash Install-Linux-SteamDeck.sh`.

It finds the game in every Steam library (SD card and Flatpak Steam included) and in `~/Games` (Heroic, Lutris), copies the files and tells Proton to load `version.dll` from the game folder (`WINEDLLOVERRIDES="version=n,b"`, in the game's launch options and in the Proton prefix; either one is enough). For a game somewhere else: `bash Install-Linux-SteamDeck.sh "/path/to/KingdomComeDeliverance"`.

### By hand
In the game folder: copy `install\KCDDLSS.asi`, `KCDDLSS.ini`, `nvngx_dlss.dll` and `version.dll` into `Bin\Win64`, and the folder `install\Mods\KCDDLSS` into `Mods` (add a line `KCDDLSS` to `Mods\mod_order.txt` if that file exists). Steam Deck / Linux only: launch options `WINEDLLOVERRIDES="version=n,b" %command%`.

### Check that it works
After the game reaches the menu, `Bin\Win64\KCDDLSS.log` contains a line like `dlss: CreateFeature 1920x1080 -> 3840x2160 Performance ... result 0x1` (your sizes). The 3D main menu is already upscaled.

## Uninstall

`KCDDLSS-Uninstall.bat` (Windows) or `bash KCDDLSS-Uninstall.sh` (Linux, Steam closed) in the game folder, or the uninstallers in the extracted archive. They remove the mod's files, remove `nvngx_dlss.dll` and `version.dll` only if they are the shipped ones, remove `Mods\KCDDLSS` and the launch option, and put a set-aside Grass Fix back.

## Settings (`Bin\Win64\KCDDLSS.ini`, read at every start)

`Mode`, `Preset` (the two menu rows write these), `Sharpness`, `MipBiasOffset` (-1.0; NVIDIA's and AMD's recommendation, Intel 0), `BlackMs` (black out the 3D view for a moment on a mode switch), `Prereq` / `GIFullRes` (the start-up settings, 0 = you manage them), `NgxDll` (a file in `Bin\Win64` to use as the upscaler instead of the NVIDIA driver, e.g. `OptiScaler.dll`). The file's comments explain the rest. `release/README.txt` is the full user manual.

## Known behaviour

- The first start after installing switches the game to native-resolution output; in exclusive fullscreen the picture can go black for a moment, the mod minimizes and restores the window to recover.
- The game's AA option is forced off while the mod runs (`Prereq = 0` in the ini if you really want to manage it).
- The menu rows replace the Advanced Graphics page definition (`Libs/UI/UIActions/MM_AdvancedGraphics.xml`); another mod changing the same page conflicts, the later one in `mod_order.txt` wins. The "Unsupported" choice is visible on every system because that page is static; picking it snaps back. A later version patches the page at run time instead.
- Tested on Windows 11 (RTX 4070: DLSS, and OptiScaler FSR / XeSS) and Linux with Proton (Bazzite with an RX 9070 XT and OptiScaler FSR 4; Steam Deck with OptiScaler). Not tested: GOG and Epic copies, Flatpak Steam and Heroic on real machines.

## Building from source

Needs mingw-w64, python3 and 7z. The plugin builds byte-identical with x86_64-w64-mingw32-gcc 13 and GNU ld 2.45.90.

```sh
tools/asi/build.sh                                   # -> tools/asi/out/KCDDLSS.asi, KCDDLSS-debug.asi, test_asi.exe
tools/asi/build.sh /path/to/WHGame.dll               # same, but first regenerate tools/asi/sig.h from your stock Steam 1.9.8 WHGame.dll
```

The menu rows are a patch against the game's own page definition, which is not stored here. Extract `Libs/UI/UIActions/MM_AdvancedGraphics.xml` (and the other `UIActions` files, used for validation) from `Data/GameData.pak` (a plain zip archive) to a folder, then:

```sh
cp <folder>/GameData/Libs/UI/UIActions/MM_AdvancedGraphics.xml tools/menu-mod/MM_AdvancedGraphics.xml
patch --binary -u tools/menu-mod/MM_AdvancedGraphics.xml tools/menu-mod/MM_AdvancedGraphics.patch
python3 -I tools/menu-mod/build_menu_mod.py --extract-root <folder>   # validates the flowgraph, -> dist/mods/KCDDLSS
python3 -I tools/menu-mod/verify_menu_mod.py                           # checks the rows, choices and reset value
release/build_release.sh BETA-2 /path/to/dinput8.dll /path/to/UAL-LICENSE /path/to/nvngx_dlss.dll /path/to/DLSS-LICENSE.txt   # -> dist/KCDDLSS-BETA-2.7z
```

`build_release.sh` takes `dinput8.dll` from `Ultimate-ASI-Loader-NoPDB_x64.zip` of [Ultimate ASI Loader v10.0.2](https://github.com/ThirteenAG/Ultimate-ASI-Loader/releases/tag/v10.0.2), its licence, `nvngx_dlss.dll` from the [DLSS SDK](https://github.com/NVIDIA/DLSS) and that repository's `LICENSE.txt`. None of them is stored here, see [THIRD_PARTY.md](THIRD_PARTY.md).

`tools/media/` holds the scripts that made the Nexus header, thumbnail and comparison images (not stored here). They draw text in the game's menu font, read from your own copy of the game (`Libs/UI/gfxfontlib_glyphs.gfx` in `Data/GameData.pak`).

## Credits

- By mrtaxerman.
- NVIDIA DLSS (NVIDIA RTX SDKs licence) and [Ultimate ASI Loader](https://github.com/ThirteenAG/Ultimate-ASI-Loader) by ThirteenAG (MIT), see [THIRD_PARTY.md](THIRD_PARTY.md).
- [OptiScaler](https://github.com/optiscaler/OptiScaler) brings FSR and XeSS to the same hook; not included.
- Crysis 3 Remastered's DLSS integration on the same engine was the blueprint. The code here was written from scratch.

## License

The code in this repository is released into the public domain under [The Unlicense](LICENSE). Game files are not included and not covered: `tools/asi/sig.h` holds a short byte pattern of the game's `WHGame.dll` (for the grass fix), and `tools/menu-mod/MM_AdvancedGraphics.patch` holds only the lines the mod adds to the game's Advanced Graphics page.

# Changelog

## BETA 2 (2026-11-09)

Plugin build 0.7.5. Two player reports fixed (details in BUGS.md):

- Black screen at start until an alt-tab, when the profile's anti-aliasing was SMAA 1TX/2TX (`r_AntialiasingMode` 2/3). The plugin's live switch to 0 on the render thread left the game's render-target stack unbalanced, so the native-res stretch drew nothing until a swap-chain rebuild. The AA mode is now forced to 0 before the first frame and pinned there (the cvar's Set/ForceSet entries are hooked), so the profile load and the settings menu can no longer switch it live.
- Crash at the first upscaled frame with ReShade installed as dxgi.dll: the sampler cache created its biased samplers through ReShade's proxy device function but with the real device as `this`. It now uses the device's own vtable entry.
- The render size is computed from the desktop resolution from the first frame; the game saves the plugin's render size as the profile resolution at exit, so a session whose upscale never ran would have shrunk the next one.
- Crashes are logged in KCDDLSS.log (module and stack modules); the minimize/restore fallback kick restores the window from its own thread and reports the result.

## BETA 1 (2026-11-08)

- First public release (beta). Plugin build 0.7.4: DLSS Super Resolution with the game's camera and object motion vectors, camera jitter and mip bias; modes Ultra Quality (0.83, the mod's own), Quality, Balanced, Performance, Ultra Performance, Native; DLSS 4 Transformer or CNN model; two rows in Options > Advanced Graphics; "Unsupported" rows and native rendering on a PC without an upscaler; FSR / XeSS through OptiScaler (not included); the 30 FPS Grass Fix and the conversation-sharpening removal built in; installers for Windows and Steam Deck / Linux.

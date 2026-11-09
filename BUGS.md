# KCDDLSS bug reports (BETA-1 / 0.7.4)

Logged 2026-11-09 from two player reports. Status at the top of each entry; details below.

## BUG-1: stretch keeps failing after the native-res switch, kick did not help (RTX 3080, 1920x1080)

Status: REPRODUCED (run072, 2026-11-09 13:19 UTC: profile r_AntialiasingMode 2, 4K, Performance) and FIXED in 0.7.5 (run073/074).
Root cause (RE agent, FINDINGS_KCD_NATIVERES_SWITCH.md + live tests): the trigger is the plugin's LIVE r_AntialiasingMode change
(profile 2/3 -> 0 at the 6 s tick) on the render thread mid-frame, not the native-res flip: the SMAA path pushes $SceneDiffuse on
the render-target stack for modes 1..7 and CPostAA::Render pops only while the mode is still != 0, so the stack keeps a stale NULL
level and the stretch has no target until a swap-chain rebuild (resize, alt-tab, the kick) runs OnD3D11PostCreateDevice. Fix: the
AA cvar is forced to 0 at device creation (before the first frame) and pinned there by hooking its cvar class's Set(int)/Set(float)/
Set(str)/ForceSet, so the profile load and a settings Apply can no longer switch it live. Extra: mode_apply uses the desktop mode as
the native size before the first upscaled frame (the game saves the plugin's render size as res_x/res_y at exit); the kick's restore
runs on its own thread and logs the window state 2.5 s later; stretch errors are re-armed after the kick.
Original note: symptom not stated by the reporter: the log ends at the minimize/restore kick with no
`dlss: frame 0 evaluated` line, so DLSS never produced a frame (black screen or the game's own stretch at 960x540).
Reporter setup: RTX 3080, display/native 1920x1080, Mode Performance (960x540), debug build, 30 FPS Grass Fix + Disable
Forced Conversation Sharpening, five D3D11CreateDevice calls (3 RTX 3080 devices, 3 context vtables hooked).
Key lines:
- `exec(init): r_FullscreenNativeRes 1: was 0, now 1` (live switch, as on our fresh-profile run060/061)
- `dlss: no render target bound after the stretch` x6 (further errors not logged)
- `bind: record vs live PS SRV mismatch mask at frame 120: 0xff1e`
- `display: stretch failing after the native-res switch: minimize/restore kick (swap chain reset)` <- last line
Questions for the reporter: what did the screen show (black / blurry / game minimized)? Fullscreen mode (exclusive,
borderless, windowed)? Does alt-tab or a settings Apply fix it? Full KCDDLSS.log after a longer session.
Full log: see `work/bugs/bug1-rtx3080-1080p.log`.

## BUG-2: crash at the first DLSS evaluate with ReShade 6.8.0 (add-on build, dxgi.dll)

Status: REPRODUCED 2026-11-09 13:05 UTC on the PC (run068, same log end) and FIXED in 0.7.5 (run069: frames evaluated with ReShade 6.8.0 as dxgi.dll). Cause: `sc_get()` created biased sampler twins through the hooked device vtable's CreateSamplerState (= ReShade's proxy device function) but passed the REAL device it got from the real immediate context -> access violation at the first upscaled frame. Fix: call the device's own vtable entry. Also new: a `CRASH:` log line (module+offset, stack modules) for future reports. Open: the real context's vtable loses our hooks every frame under ReShade (diagnosed in run070).
Reporter: Steam 1.9.8, RTX 5070 Ti Laptop, Windows 11, exclusive fullscreen 2560x1600,
Mode Quality (1707x1067), loaded through an existing Ultimate ASI Loader (winmm.dll). ReShade 6.8.0 add-on build as
dxgi.dll, no add-ons, no effects. Log ends after `dlss: object motion vectors on` / `mv: proj ...`, never reaches
`dlss: frame 0 evaluated and copied to the target`; no crash dialog, the game closes. Without ReShade everything works.
Reporter's hypothesis: NGX gets ReShade's wrapped D3D11 device/context/resources (ReShade proxies ID3D11Device,
ID3D11DeviceContext and all resources; NGX needs the real driver objects).
Full report: `work/bugs/bug2-reshade.txt`.

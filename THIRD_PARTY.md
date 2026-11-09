# Third-party software

None of it is stored in this repository. `release/build_release.sh` takes the files as arguments and puts them, with their licences, into the release archive.

## NVIDIA DLSS

- Project: https://github.com/NVIDIA/DLSS (NVIDIA RTX SDKs)
- Version shipped: 310.9.1 (`nvngx_dlss.dll`, 64-bit)
- Licence: NVIDIA RTX SDKs licence (`LICENSE.txt` of that repository). The release archive ships it as `install/nvngx_dlss.dll` with the licence as `install/NVIDIA-DLSS-LICENSE.txt`.

## Ultimate ASI Loader

- Project: https://github.com/ThirteenAG/Ultimate-ASI-Loader
- Author: ThirteenAG
- Version: 10.0.2, x64 (`dinput8.dll` from `Ultimate-ASI-Loader-NoPDB_x64.zip`), shipped as `install/version.dll`
- Licence: MIT (`install/Ultimate-ASI-Loader-LICENSE.txt` in the archive)

## OptiScaler (only in the OptiScaler download)

- Project: https://github.com/optiscaler/OptiScaler
- The mod talks to the upscaler through NVIDIA's NGX interface; OptiScaler answers that interface with FSR 2.2 / 3.1 / 4 or XeSS on any GPU. The standard download does not include it (users set it up themselves, see `release/OPTISCALER.txt`). The OptiScaler download (`KCDDLSS-<version>-OptiScaler.7z`) ships OptiScaler 0.9.4 from the official release `Optiscaler_0.9.4-final.20260718._MM.7z`: OptiScaler.dll, OptiScaler.ini (one line changed: `Dx11Upscaler=fsr31_12`), libxess.dll, libxess_dx11.dll, libxell.dll (Intel XeSS SDK licence), amd_fidelityfx_dx12.dll, amd_fidelityfx_upscaler_dx12.dll, amd_fidelityfx_vk.dll (AMD FidelityFX SDK licence), with those licence texts and OptiScaler's GPL-3.0 text (tag v0.9.4, commit 7534ad00bf9e590eedb99e8dd9fd8c89dae3654f; source https://github.com/optiscaler/OptiScaler/tree/v0.9.4). Also shipped: D3D12_Optiscaler/D3D12Core.dll (Microsoft DirectX 12 Agility SDK, from the same release, DirectX licence text included; used only with FsrAgilitySDKUpgrade=true, for FSR 4 on Windows 10). Left out: fakenvapi and the frame-generation files (the game has none to replace) and Nukem's dlssg-to-fsr3 (its binary is not licensed for redistribution).

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

## OptiScaler (optional, not shipped)

- Project: https://github.com/optiscaler/OptiScaler
- The mod talks to the upscaler through NVIDIA's NGX interface; OptiScaler answers that interface with FSR 2.2 / 3.1 / 4 or XeSS on any GPU. Users download it themselves, see `release/OPTISCALER.txt`.

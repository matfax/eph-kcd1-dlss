#!/bin/bash
# Build KCDDLSS.asi (release) and KCDDLSS-debug.asi (x64, no C runtime) into tools/asi/out/.
# Needs mingw-w64 (x86_64-w64-mingw32-gcc, -windres, -objdump).
# usage: ./build.sh                     build from the committed sig.h
#        ./build.sh /path/to/WHGame.dll first regenerate sig.h (the grass-fix byte pattern) from your own stock
#                                       Steam 1.9.8 WHGame.dll (also needs python3)
set -eu
cd "$(dirname "$0")"
mkdir -p out
if [ $# -ge 1 ]; then
  python3 -I gen_sig.py "$1" patchb/cave.bin 6d sig.h        # 0x6d = offset of the return jump in cave.bin
fi
CFLAGS="-Os -s -Wall -Wextra -ffreestanding -fno-builtin -fno-stack-protector \
  -fno-asynchronous-unwind-tables -fno-tree-loop-distribute-patterns -fno-ident -mno-stack-arg-probe \
  -shared -nostdlib -nostartfiles -Wl,-e,DllMain -Wl,--dynamicbase,--nxcompat,--high-entropy-va -Wl,--no-insert-timestamp"
# release build (ships): diagnostics compiled out, the game console gets the bare minimum
x86_64-w64-mingw32-windres version.rc -O coff -o out/version.res
x86_64-w64-mingw32-gcc $CFLAGS -o out/KCDDLSS.asi kcd_dlss.c out/version.res -lkernel32 -ladvapi32 -luser32
# debug build (for bug reports: blue-frame probe, NGX log, post-effect tracing in KCDDLSS.log)
x86_64-w64-mingw32-windres -DKCDDLSS_DEBUG version.rc -O coff -o out/version-debug.res
x86_64-w64-mingw32-gcc -DKCDDLSS_DEBUG $CFLAGS -o out/KCDDLSS-debug.asi kcd_dlss.c out/version-debug.res -lkernel32 -ladvapi32 -luser32
# Wine/Windows self-test of the embedded grass fix against a mapped WHGame.dll (see test_asi.c)
x86_64-w64-mingw32-gcc -O1 -Wall -static -o out/test_asi.exe test_asi.c
ls -l out/KCDDLSS.asi out/KCDDLSS-debug.asi; sha256sum out/KCDDLSS.asi out/KCDDLSS-debug.asi
x86_64-w64-mingw32-objdump -p out/KCDDLSS.asi | grep -E "DLL Name|^\s+[0-9a-f]+\s+[0-9]+\s+\w+$" | head -60

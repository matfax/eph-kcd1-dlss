# setres.ps1 <width> <height> [hz] [flags]  - change the primary display mode; runs in the user's desktop session via a schtasks task
# (session 0 / SSH sees a fake 1024x768). width 0 = query only. flags 1 = CDS_UPDATEREGISTRY (the plugin reads the registry mode as
# the native size), 0 = temporary. The DEVMODE work is done in C#: a PowerShell struct copy loses dmSize.
param([int]$w = 1920, [int]$h = 1080, [int]$hz = 60, [int]$flags = 1)
Add-Type @"
using System; using System.Runtime.InteropServices;
public class DM {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
  public struct DEVMODE { [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmDeviceName; public short dmSpecVersion, dmDriverVersion, dmSize, dmDriverExtra; public int dmFields;
    public int dmPositionX, dmPositionY, dmDisplayOrientation, dmDisplayFixedOutput; public short dmColor, dmDuplex, dmYResolution, dmTTOption, dmCollate;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmFormName; public short dmLogPixels; public int dmBitsPerPel, dmPelsWidth, dmPelsHeight, dmDisplayFlags, dmDisplayFrequency;
    public int dmICMMethod, dmICMIntent, dmMediaType, dmDitherType, dmReserved1, dmReserved2, dmPanningWidth, dmPanningHeight; }
  [DllImport("user32.dll", SetLastError=true)] public static extern int EnumDisplaySettings(string n, int i, ref DEVMODE d);
  [DllImport("user32.dll")] public static extern int ChangeDisplaySettings(ref DEVMODE d, int flags);
  public static string Q(int i) { DEVMODE d = new DEVMODE(); d.dmSize = (short)Marshal.SizeOf(d); int r = EnumDisplaySettings(null, i, ref d); return r == 0 ? "(query failed)" : d.dmPelsWidth + "x" + d.dmPelsHeight + "@" + d.dmDisplayFrequency; }
  public static int Set(int w, int h, int hz, int flags) { DEVMODE d = new DEVMODE(); d.dmSize = (short)Marshal.SizeOf(d); EnumDisplaySettings(null, -1, ref d);
    d.dmPelsWidth = w; d.dmPelsHeight = h; d.dmDisplayFrequency = hz; d.dmFields = 0x80000 | 0x100000 | 0x400000; return ChangeDisplaySettings(ref d, flags); }
}
"@
"registry: $([DM]::Q(-2)); current: $([DM]::Q(-1))"
if ($w -eq 0) { exit 0 }
$r = [DM]::Set($w, $h, $hz, $flags)
"result $r (0 = ok), now: $([DM]::Q(-1)); registry: $([DM]::Q(-2))"

"""
Windows DWM Acrylic / Mica blur effect for frameless transparent windows.

Priority:
  1. Win11 22H2+: DwmSetWindowAttribute + DWMWA_SYSTEMBACKDROP_TYPE (Acrylic)
  2. Win10 1803+:  SetWindowCompositionAttribute + ACCENT_ENABLE_ACRYLICBLURBEHIND
  3. Win10:        ACCENT_ENABLE_BLURBEHIND (basic blur, no tint)
"""

import ctypes
from ctypes import wintypes

# ── Win10 Accent API ──────────────────────────────────────────────

ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
WCA_ACCENT_POLICY = 19


class _AccentPolicy(ctypes.Structure):
    _fields_ = [
        ("AccentState", wintypes.DWORD),
        ("AccentFlags", wintypes.DWORD),
        ("GradientColor", wintypes.DWORD),
        ("AnimationId", wintypes.DWORD),
    ]


class _WindowCompositionData(ctypes.Structure):
    _fields_ = [
        ("Attribute", wintypes.DWORD),
        ("Data", ctypes.POINTER(_AccentPolicy)),
        ("SizeOfData", wintypes.DWORD),
    ]


# ── Win11 DwmSetWindowAttribute ───────────────────────────────────

DWMWA_MICA = 1029
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_MAINWINDOW = 2      # Mica
DWMSBT_TABBEDWINDOW = 4    # Acrylic


def apply_acrylic(hwnd: int) -> bool:
    """
    Apply Acrylic blur behind *hwnd* (a Win32 window handle).

    Returns True if at least one method succeeded.
    """
    hwnd_ptr = wintypes.HWND(hwnd)

    # 1) Win11 22H2+ — native Acrylic backdrop
    try:
        dwm = ctypes.windll.dwmapi
        backdrop = wintypes.DWORD(DWMSBT_TABBEDWINDOW)
        hr = dwm.DwmSetWindowAttribute(
            hwnd_ptr,
            DWMWA_SYSTEMBACKDROP_TYPE,
            ctypes.byref(backdrop),
            ctypes.sizeof(backdrop),
        )
        if hr == 0:
            print("[acrylic] Win11 Acrylic backdrop OK")
            return True
        print(f"[acrylic] Win11 backdrop failed, hr={hr}")
    except Exception as e:
        print(f"[acrylic] Win11 backdrop exception: {e}")

    # 2) Win10 1803+ — Acrylic via accent API
    try:
        user32 = ctypes.windll.user32
        accent = _AccentPolicy()
        accent.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND
        # GradientColor: ABGR, alpha=0x90 gives visible tint
        accent.GradientColor = 0x9011111A

        data = _WindowCompositionData()
        data.Attribute = WCA_ACCENT_POLICY
        data.Data = ctypes.pointer(accent)
        data.SizeOfData = ctypes.sizeof(accent)

        result = user32.SetWindowCompositionAttribute(hwnd_ptr, ctypes.byref(data))
        if result:
            print("[acrylic] Win10 Acrylic accent OK")
            return True
        print(f"[acrylic] Win10 Acrylic accent failed, result={result}")
    except Exception as e:
        print(f"[acrylic] Win10 Acrylic accent exception: {e}")

    # 3) Fallback — basic blur behind
    try:
        accent = _AccentPolicy()
        accent.AccentState = ACCENT_ENABLE_BLURBEHIND
        accent.GradientColor = 0x00000000
        data = _WindowCompositionData()
        data.Attribute = WCA_ACCENT_POLICY
        data.Data = ctypes.pointer(accent)
        data.SizeOfData = ctypes.sizeof(accent)
        result = ctypes.windll.user32.SetWindowCompositionAttribute(
            hwnd_ptr, ctypes.byref(data)
        )
        if result:
            print("[acrylic] Win10 basic blur OK")
            return True
        print(f"[acrylic] Win10 blur failed, result={result}")
    except Exception as e:
        print(f"[acrylic] Win10 blur exception: {e}")

    print("[acrylic] ALL methods failed")
    return False

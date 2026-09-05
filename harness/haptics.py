"""Typed SDL2 emergency stop. No device access until stop_all() is called."""
import ctypes


def bind_sdl(sdl):
    declarations = {
        "SDL_Init": (ctypes.c_int, [ctypes.c_uint32]),
        "SDL_NumHaptics": (ctypes.c_int, []),
        "SDL_HapticOpen": (ctypes.c_void_p, [ctypes.c_int]),
        "SDL_HapticStopAll": (ctypes.c_int, [ctypes.c_void_p]),
        "SDL_HapticClose": (None, [ctypes.c_void_p]),
        "SDL_Quit": (None, []),
    }
    for name, (restype, argtypes) in declarations.items():
        function = getattr(sdl, name)
        function.restype, function.argtypes = restype, argtypes
    return sdl


def stop_all(dll_path, *, loader=ctypes.CDLL):
    """Return the count of devices that acknowledged a stop, not just an open.

    SDL owns the pointer; an implicit ctypes c_int return would truncate it on
    x64. The injectable loader supports ABI/lifecycle regression tests without
    loading SDL or actuating a device.
    """
    sdl = bind_sdl(loader(str(dll_path)))
    stopped = 0
    try:
        if sdl.SDL_Init(0x200 | 0x1000) != 0:  # JOYSTICK | HAPTIC
            return 0
        for i in range(max(0, sdl.SDL_NumHaptics())):
            handle = sdl.SDL_HapticOpen(i)
            if handle:
                try:
                    if sdl.SDL_HapticStopAll(handle) == 0:
                        stopped += 1
                finally:
                    sdl.SDL_HapticClose(handle)
    finally:
        sdl.SDL_Quit()
    return stopped

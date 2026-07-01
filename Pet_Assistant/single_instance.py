import ctypes
import ctypes.wintypes


ERROR_ALREADY_EXISTS = 183


class SingleInstance:
    def __init__(self, name):
        self.name = name
        self.handle = None

    def acquire(self):
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = [
            ctypes.wintypes.LPVOID,
            ctypes.wintypes.BOOL,
            ctypes.wintypes.LPCWSTR,
        ]
        kernel32.CreateMutexW.restype = ctypes.wintypes.HANDLE

        self.handle = kernel32.CreateMutexW(None, False, self.name)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

        return ctypes.get_last_error() != ERROR_ALREADY_EXISTS

    def release(self):
        if not self.handle:
            return

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
        kernel32.CloseHandle(self.handle)
        self.handle = None

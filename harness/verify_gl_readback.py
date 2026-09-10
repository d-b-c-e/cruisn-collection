"""Exercise native Windows OpenGL screenshot packing with guarded storage.

Both native renderers allocate tightly packed RGB screenshot buffers. Explicit
pack alignment of one is required when row widths are not multiples of four.
The reproduction overallocates guard storage, so the legacy test does not write
outside the real allocation. No game resources or visible window are required.
"""
import argparse
import ctypes
import os
from pathlib import Path

import moderngl
from verification import write_json


def checks():
    if os.name != 'nt':
        raise OSError('Native Windows OpenGL readback fixture requires Windows')
    ctx = moderngl.create_standalone_context(require=430)
    try:
        gl = ctypes.WinDLL('opengl32')
        gl.glPixelStorei.argtypes = [ctypes.c_uint, ctypes.c_int]
        gl.glReadPixels.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_uint, ctypes.c_uint,
                                   ctypes.c_void_p]
        gl.glGetError.restype = ctypes.c_uint
        results = []
        for width in (1, 2, 3, 512, 513, 1279, 1921, 3825):
            height = 7
            texture = ctx.texture((width, height), 4)
            framebuffer = ctx.framebuffer([texture])
            try:
                framebuffer.use()
                framebuffer.clear(.2, .4, .6, 1)
                tight = width * height * 3
                stride = (width * 3 + 3) & ~3
                padded = stride * height
                cases = []
                for alignment in (4, 1):
                    storage = (ctypes.c_ubyte * (padded + 64))()
                    ctypes.memset(storage, 0xa5, len(storage))
                    gl.glPixelStorei(0x0d05, alignment)
                    gl.glReadPixels(0, 0, width, height, 0x80e0, 0x1401, storage)
                    assert gl.glGetError() == 0, 'OpenGL readback error'
                    raw = bytes(storage)
                    expected = bytes((153, 102, 51)) * (width * height)
                    result = dict(
                        alignment=alignment,
                        bytes_beyond_tight=sum(b != 0xa5 for b in raw[tight:]),
                        different_tight_bytes=sum(a != b for a, b in
                                                  zip(raw[:tight], expected)))
                    assert raw[padded:] == bytes([0xa5]) * 64, 'outer guard changed'
                    if alignment == 4 and width * 3 % 4:
                        assert result['bytes_beyond_tight'] > 0
                        assert result['different_tight_bytes'] > 0
                    else:
                        assert result['bytes_beyond_tight'] == 0
                        assert result['different_tight_bytes'] == 0
                    cases.append(result)
                results.append(dict(width=width, height=height,
                                    tight_bytes=tight, padded_stride=stride,
                                    checks=cases))
            finally:
                framebuffer.release()
                texture.release()
        return dict(passed=True, scope=__doc__.strip(), cases=results)
    finally:
        ctx.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = checks()
    except (AssertionError, OSError, ValueError, ctypes.ArgumentError, moderngl.Error) as error:
        result = dict(passed=False, error=str(error))
    write_json(args.report, result)
    print('PASS' if result['passed'] else 'FAIL', args.report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

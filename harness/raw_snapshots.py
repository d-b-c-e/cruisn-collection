"""Convert retained MAME screen RGB32 pixels after emulation has stopped."""
from pathlib import Path
import re
import struct

from PIL import Image


def read_raw(path):
    data = Path(path).read_bytes()
    if len(data) < 16:
        raise ValueError("truncated raw snapshot header")
    magic, width, height = struct.unpack_from("<8sII", data)
    if magic != b"CRSNRAW1" or not 0 < width <= 16384 or not 0 < height <= 16384:
        raise ValueError("invalid raw snapshot format/dimensions")
    if len(data) != 16 + width * height * 4:
        raise ValueError("raw snapshot pixel count differs from dimensions")
    # MAME's Windows snapshot_pixels() returns little-endian 0xAARRGGBB.
    return Image.frombytes("RGB", (width, height), data[16:], "raw", "BGRX")


def convert_raw_snapshots(runtime):
    runtime = Path(runtime)
    files = sorted((runtime / "raw-snap").glob("*.raw"))
    for source in files:
        if not re.fullmatch(r"frame_\d{8}\.raw", source.name):
            raise ValueError("invalid raw snapshot filename")
        image = read_raw(source)
        target = runtime / "snap" / (source.stem + ".png")
        if target.exists():
            with Image.open(target) as current:
                if current.size != image.size or current.convert("RGB").tobytes() != image.tobytes():
                    raise ValueError("existing PNG differs from raw snapshot; refusing overwrite")
        else:
            image.save(target, compress_level=3)
    return len(files)

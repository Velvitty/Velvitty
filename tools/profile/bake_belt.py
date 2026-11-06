"""Bake the fixed mesh and hero decorations. Requires NumPy, Pillow and FFmpeg with librsvg.

The normal README build uses the checked-in PNGs and the Python standard library.
Run this script again when the source mesh changes. No browser scripting is used.
"""
import base64
import io
import hashlib
import json
import math
import subprocess
import tempfile
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "tools/portfolio/mobius-reference.svg"
OUTPUT = Path(__file__).with_name("belt")
SVG = "{http://www.w3.org/2000/svg}"
X, Y, W, H = -210, -160, 420, 330
SCALE = 2
PERIOD_X, PERIOD_Y = 512, 240
DISPLACEMENT_RANGE = 896


def source_image(element):
    payload = element.get("href").split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(payload))).convert("RGBA")


def polygon_coverage(vertices, x, y):
    inside = np.zeros((len(y), len(x)), dtype=bool)
    for (x1, y1), (x2, y2) in zip(vertices, np.roll(vertices, -1, axis=0)):
        if y1 != y2:
            crossing = (y1 > y) != (y2 > y)
            inside ^= crossing & (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1)
    return inside


def encode_displacement(source_position, output_position, valid):
    # Keep displacement unwrapped inside each face. Wrapping here would cause
    # interpolation across opposite ends of a tile at otherwise smooth pixels.
    shift = (source_position - output_position)[valid]
    if np.any(np.abs(shift) > DISPLACEMENT_RANGE / 2):
        raise ValueError("A visible texture coordinate lies outside the paint plane")
    return np.rint((shift / DISPLACEMENT_RANGE + 0.5) * 255).astype(np.uint8)


def bake_map(solid, definitions):
    pixels = np.zeros((H * SCALE, W * SCALE, 4), dtype=np.uint8)
    faces = [element for element in solid if element.get("data-material-face")]
    if len(faces) != 720:
        raise ValueError(f"Expected all 720 source faces, found {len(faces)}")
    for face in faces:
        clip = definitions[face.get("clip-path")[5:-1]]
        vertices = np.array([list(map(float, pair.split(","))) for pair in
                             re.findall(r"[ML]([-\d.,]+)", clip[0].get("d"))])
        start = np.maximum(np.floor((vertices.min(axis=0) - [X, Y]) * SCALE).astype(int), 0)
        stop = np.minimum(np.ceil((vertices.max(axis=0) - [X, Y]) * SCALE).astype(int), [W*SCALE,H*SCALE])
        x = X + (np.arange(start[0], stop[0]) + 0.5) / SCALE
        y = (Y + (np.arange(start[1], stop[1]) + 0.5) / SCALE)[:, None]
        transform = face[0].get("transform").removeprefix("matrix(").removesuffix(")")
        a, b, c, d, e, f = map(float, transform.split(","))
        det = a * d - b * c
        if det == 0:
            raise ValueError("Degenerate face matrix")
        u = (d * (x - e) - c * (y - f)) / det
        v = (a * (y - f) - b * (x - e)) / det
        valid = polygon_coverage(vertices, x, y) & (v >= 0) & (v < 120)
        edge = face[0][0].get("href") == "#mb-edge-material"
        # Top half of the tile is the face motif. Bottom half is the edge.
        sx = (u / 1200 - 0.5) * PERIOD_X
        sy = (v / 120 + edge - 1) * PERIOD_Y / 2
        tile = pixels[start[1]:stop[1], start[0]:stop[0]]
        tile[..., 0][valid] = encode_displacement(sx, x, valid)
        tile[..., 1][valid] = encode_displacement(sy, y, valid)
        tile[..., 3][valid] = 255
    return Image.fromarray(pixels)


def bake_light(solid, definitions):
    layer = next(e for e in solid if e.get("data-continuous-lighting"))
    image = np.array(source_image(layer), dtype=np.float32)
    matrix_id = layer.get("filter")[5:-1]
    coefficients = np.fromstring(definitions[matrix_id][0].get("values"), sep=" ").reshape(4, 5)
    rgb = image[..., :3] @ coefficients[:3, :3].T + coefficients[:3, 4] * 255
    image[..., :3] = rgb
    image[..., 3] *= float(layer.get("opacity"))
    return Image.fromarray(np.rint(image).clip(0, 255).astype(np.uint8))


def raster_decoration(markup, bounds, target):
    # Only the optional asset-baking step needs FFmpeg's librsvg decoder.
    x, y, width, height = bounds
    source = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width*2}" height="{height*2}" '
              f'viewBox="{x} {y} {width} {height}">{markup}</svg>')
    with tempfile.TemporaryDirectory() as directory:
        svg = Path(directory) / "decoration.svg"
        svg.write_text(source)
        rendered = Path(directory) / "decoration.png"
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(svg),
             "-frames:v", "1", "-threads", "1", "-pix_fmt", "rgba", str(rendered)],
            check=True,
        )
        with Image.open(rendered) as decoration:
            if target.suffix == ".webp":
                decoration.save(target, quality=90, method=6)
            else:
                decoration.save(target, optimize=True)


def bake_decorations(model, definitions):
    # Reuse the profile's original geometry, photographic crop and shadow.
    from portfolio import SVG as ProfileSVG, backdrop, photo_print, xml

    for name in ("coast", "botanical"):
        scene = ProfileSVG("en", 268, 252, name)
        backdrop(scene)
        print_group = photo_print(scene, name, 0, 0, 128, 88)
        markup = "<defs>" + "".join(scene.defs) + "</defs>" + print_group
        raster_decoration(markup, (-70,-70,268,252), OUTPUT / f"{name}.webp")

    for axis in (e for e in model.iter() if e.get("data-axis-layer")):
        for child in list(axis):
            if child.get("class") == "mobius-axes-motion":
                axis.remove(child)
        markup = "<defs>" + xml(definitions["axis-focus"]) + "</defs>" + xml(axis)
        raster_decoration(markup, (-254,-254,508,508), OUTPUT / ("axis-" + axis.get("data-axis-layer") + ".png"))


def main():
    model = ET.parse(MODEL).getroot()
    definitions = {e.get("id"): e for e in model.find(SVG + "defs")}
    solid = next(e for e in model.iter() if e.get("class") == "mobius-solid")
    OUTPUT.mkdir(exist_ok=True)
    bake_map(solid, definitions).save(OUTPUT / "displacement.png", optimize=True)
    bake_light(solid, definitions).save(OUTPUT / "lighting.png", optimize=True)
    bake_decorations(model, definitions)
    left, top, right, bottom = source_image(definitions["mb-smooth-outline"][0]).getbbox()
    left = math.floor(X + left / SCALE) - 1
    top = math.floor(Y + top / SCALE) - 1
    right = math.ceil(X + right / SCALE) + 1
    bottom = math.ceil(Y + bottom / SCALE) + 1
    layout = {
        "model_sha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        "tile_width": PERIOD_X, "tile_height": PERIOD_Y,
        "displacement_scale": DISPLACEMENT_RANGE,
        "paint_bounds": [left, top, right-left, bottom-top],
    }
    (OUTPUT / "layout.json").write_text(json.dumps(layout, indent=2) + "\n")


if __name__ == "__main__":
    main()

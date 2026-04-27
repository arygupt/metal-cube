"""Generate a small animated GIF of a rotating metallic cube.

Run with:
    python animation.py
"""

from __future__ import annotations

import math
import struct
from pathlib import Path


WIDTH = 180
HEIGHT = 180
FRAMES = 64
BACKGROUND = 248


def rotate(point: tuple[float, float, float], ax: float, ay: float, az: float) -> tuple[float, float, float]:
    x, y, z = point
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)

    y, z = y * cx - z * sx, y * sx + z * cx
    x, z = x * cy + z * sy, -x * sy + z * cy
    x, y = x * cz - y * sz, x * sz + y * cz
    return x, y, z


def project(point: tuple[float, float, float]) -> tuple[float, float]:
    x, y, z = point
    scale = 68 / (z + 4.1)
    return WIDTH / 2 + x * scale, HEIGHT / 2 - y * scale


def normal(a: tuple[float, float, float], b: tuple[float, float, float], c: tuple[float, float, float]) -> tuple[float, float, float]:
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
    return nx / length, ny / length, nz / length


def fill_polygon(frame: bytearray, points: list[tuple[float, float]], shade: int, t: float) -> None:
    min_y = max(0, int(math.floor(min(y for _, y in points))))
    max_y = min(HEIGHT - 1, int(math.ceil(max(y for _, y in points))))
    min_x = max(0, int(math.floor(min(x for x, _ in points))))
    max_x = min(WIDTH - 1, int(math.ceil(max(x for x, _ in points))))
    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)

    for y in range(min_y, max_y + 1):
        intersections: list[float] = []
        for i, (x1, y1) in enumerate(points):
            x2, y2 = points[(i + 1) % len(points)]
            if (y1 <= y < y2) or (y2 <= y < y1):
                intersections.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        intersections.sort()

        for start, end in zip(intersections[0::2], intersections[1::2]):
            x_start = max(min_x, int(math.ceil(start)))
            x_end = min(max_x, int(math.floor(end)))
            for x in range(x_start, x_end + 1):
                u = (x - min_x) / span_x
                v = (y - min_y) / span_y
                brushed = math.sin((u * 26 + v * 9 + t) * math.pi) * 9
                gleam = max(0, 1 - abs(u - 0.34) * 5 - abs(v - 0.22) * 3) * 42
                edge = min(u, v, 1 - u, 1 - v)
                bevel = max(0, 0.08 - edge) * 360
                value = int(max(22, min(246, shade + brushed + gleam + bevel)))
                frame[y * WIDTH + x] = value


def draw_frame(frame_index: int) -> bytes:
    frame = bytearray([BACKGROUND] * (WIDTH * HEIGHT))
    t = frame_index / FRAMES
    ax = -0.55 + math.sin(t * math.tau) * 0.22
    ay = t * math.tau
    az = math.sin(t * math.tau * 0.7) * 0.18

    vertices = [
        (-1, -1, -1),
        (1, -1, -1),
        (1, 1, -1),
        (-1, 1, -1),
        (-1, -1, 1),
        (1, -1, 1),
        (1, 1, 1),
        (-1, 1, 1),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    rotated = [rotate(vertex, ax, ay, az) for vertex in vertices]
    light = (-0.45, 0.65, 0.62)
    face_data = []

    for face in faces:
        points_3d = [rotated[index] for index in face]
        n = normal(points_3d[0], points_3d[1], points_3d[2])
        facing = n[2]
        if facing < -0.08:
            continue
        diffuse = max(0, n[0] * light[0] + n[1] * light[1] + n[2] * light[2])
        specular = max(0, n[2]) ** 7
        shade = int(68 + diffuse * 112 + specular * 58)
        depth = sum(point[2] for point in points_3d) / 4
        face_data.append((depth, [project(point) for point in points_3d], shade))

    for depth, points, shade in sorted(face_data):
        fill_polygon(frame, points, shade, frame_index * 0.14 + depth)

    return bytes(frame)


def lzw_encode(indices: bytes, min_code_size: int = 8) -> bytes:
    clear = 1 << min_code_size
    end = clear + 1
    dictionary = {bytes([i]): i for i in range(clear)}
    next_code = end + 1
    code_size = min_code_size + 1
    packed: list[int] = []
    bit_buffer = 0
    bit_count = 0

    def emit(code: int) -> None:
        nonlocal bit_buffer, bit_count
        bit_buffer |= code << bit_count
        bit_count += code_size
        while bit_count >= 8:
            packed.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

    emit(clear)
    word = bytes([indices[0]])
    for value in indices[1:]:
        candidate = word + bytes([value])
        if candidate in dictionary:
            word = candidate
            continue
        emit(dictionary[word])
        if next_code < 4096:
            dictionary[candidate] = next_code
            next_code += 1
            if next_code == (1 << code_size) and code_size < 12:
                code_size += 1
        else:
            emit(clear)
            dictionary = {bytes([i]): i for i in range(clear)}
            next_code = end + 1
            code_size = min_code_size + 1
        word = bytes([value])

    emit(dictionary[word])
    emit(end)
    if bit_count:
        packed.append(bit_buffer & 0xFF)
    return bytes(packed)


def gif_subblocks(data: bytes) -> bytes:
    chunks = bytearray()
    for index in range(0, len(data), 255):
        chunk = data[index : index + 255]
        chunks.append(len(chunk))
        chunks.extend(chunk)
    chunks.append(0)
    return bytes(chunks)


def write_gif(path: str | Path = "metallic_cube.gif") -> Path:
    output = Path(path)
    palette = bytearray()
    for value in range(256):
        palette.extend((value, value, value))

    data = bytearray(b"GIF89a")
    data.extend(struct.pack("<HH", WIDTH, HEIGHT))
    data.extend(bytes([0xF7, 0, 0]))
    data.extend(palette)
    data.extend(b"!\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00")

    for frame_index in range(FRAMES):
        data.extend(b"!\xf9\x04\x04\x04\x00\x00\x00")
        data.extend(b",")
        data.extend(struct.pack("<HHHH", 0, 0, WIDTH, HEIGHT))
        data.append(0)
        data.append(8)
        data.extend(gif_subblocks(lzw_encode(draw_frame(frame_index))))

    data.extend(b";")
    output.write_bytes(data)
    return output


if __name__ == "__main__":
    result = write_gif()
    print(f"Wrote {result}")

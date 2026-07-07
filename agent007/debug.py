"""Game diagnostics — run this to check for bugs in the 007 engine."""
from __future__ import annotations

import math
import sys
import time

import numpy as np

from engine.map import FACILITY_MAP
from engine.player import Player
from engine.raycaster import Raycaster


def check_map():
    issues = []
    g = FACILITY_MAP

    # Check bounds
    if g.width < 3 or g.height < 3:
        issues.append(f"Map too small: {g.width}x{g.height}")

    # Verify all border tiles are walls
    for y in range(g.height):
        if g.grid[y][0] == 0:
            issues.append(f"Left border not wall at y={y}")
        if g.grid[y][g.width - 1] == 0:
            issues.append(f"Right border not wall at y={y}")

    for x in range(g.width):
        if g.grid[0][x] == 0:
            issues.append(f"Top border not wall at x={x}")
        if g.grid[g.height - 1][x] == 0:
            issues.append(f"Bottom border not wall at x={x}")

    # Check for disconnected rooms (BFS)
    visited = set()
    stack = [(1, 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in visited:
            continue
        if not (0 <= x < g.width and 0 <= y < g.height):
            continue
        if g.grid[y][x] != 0:
            continue
        visited.add((x, y))
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            stack.append((x + dx, y + dy))

    open_tiles = sum(row.count(0) for row in g.grid)
    reachable_pct = len(visited) / max(open_tiles, 1) * 100
    if reachable_pct < 80:
        issues.append(f"Map has disconnected rooms — only {reachable_pct:.0f}% reachable")

    print(f"Map: {g.width}x{g.height}, {open_tiles} open tiles, {reachable_pct:.0f}% reachable")
    for issue in issues:
        print(f"  ⚠ {issue}")
    return len(issues) == 0


def check_player():
    issues = []
    p = Player()

    # Check direction/plane orthogonality + unit length
    dot = p.dir_x * p.plane_x + p.dir_y * p.plane_y
    if abs(dot) > 0.01:
        issues.append(f"Dir/plane not perpendicular (dot={dot:.3f})")

    dir_len = math.sqrt(p.dir_x ** 2 + p.dir_y ** 2)
    if abs(dir_len - 1.0) > 0.001:
        issues.append(f"Direction not unit length ({dir_len:.3f})")

    # FOV sanity
    fov = 2 * math.atan2(abs(p.plane_y), abs(p.dir_x))
    fov_deg = math.degrees(fov)
    if fov_deg < 30 or fov_deg > 150:
        issues.append(f"FOV extreme: {fov_deg:.0f}°")

    print(f"Player: dir_len={dir_len:.3f}, dot={dot:.3f}, FOV={fov_deg:.0f}°")
    for issue in issues:
        print(f"  ⚠ {issue}")
    return len(issues) == 0


def check_raycaster():
    issues = []
    r = Raycaster(FACILITY_MAP, 640, 480)
    p = Player(x=2.5, y=7.5)
    p.dir_x, p.dir_y = 1.0, 0.0
    p.plane_x, p.plane_y = 0.0, 0.66

    fb = r.render(p)

    # Check frame properties
    if fb.shape != (480, 640, 3):
        issues.append(f"Frame shape wrong: {fb.shape}")
    if fb.dtype != np.uint8:
        issues.append(f"Frame dtype wrong: {fb.dtype}")

    # Check sky is present (should have blue values in top half)
    sky_r, sky_g, sky_b = fb[50, 320].tolist()
    if sky_b < sky_r or sky_b < sky_g:
        issues.append(f"Sky not blue enough: RGB=({sky_r},{sky_g},{sky_b})")
    if sky_b < 50:
        issues.append(f"Sky too dark: B={sky_b}")

    # Check floor is present (should have gray in bottom half)
    floor = fb[450, 320].tolist()
    if not (floor[0] == floor[1] == floor[2]):
        issues.append(f"Floor not grayscale: {floor}")

    # Check walls rendered (should have non-sky, non-floor in center)
    center = fb[240, 320].tolist()
    if center == [sky_r, sky_g, sky_b] or center == floor:
        print(f"  Note: center pixel is {center} (no wall at center of screen)")

    # Edge cases
    # Player at (0.5, 0.5) - corner
    p.x, p.y = 0.5, 0.5
    try:
        r.render(p)
    except Exception as e:
        issues.append(f"Corner position crash: {e}")

    # Player at center + rotated each way
    p.x, p.y = 8.0, 8.0
    for angle in [0, math.pi / 2, math.pi, -math.pi / 2]:
        p.dir_x, p.dir_y = math.cos(angle), math.sin(angle)
        p.plane_x = -p.dir_y * 0.66
        p.plane_y = p.dir_x * 0.66
        fb = r.render(p)
        wall = np.count_nonzero(fb[:, 320, :] > 50)
        if wall < 10:
            issues.append(f"Facing {math.degrees(angle):.0f}°: only {wall} wall pixels")

    # Performance check (> 5 FPS on reasonable hardware)
    p.x, p.y = 2.5, 7.5
    p.dir_x, p.dir_y = 1.0, 0.0
    p.plane_x, p.plane_y = 0.0, 0.66

    t0 = time.perf_counter_ns()
    for _ in range(10):
        r.render(p)
    dt = (time.perf_counter_ns() - t0) / 1e9
    fps = 10 / dt
    if fps < 5:
        issues.append(f"Low performance: {fps:.1f} FPS (10 frames in {dt:.2f}s)")

    print(f"Raycaster: 10 frames in {dt:.2f}s ({fps:.1f} FPS)")
    for issue in issues:
        print(f"  ⚠ {issue}")
    return len(issues) == 0


def check_collision():
    issues = []
    p = Player(x=2.5, y=7.5)

    # Move into wall — shouldn't clip
    old_x, old_y = p.x, p.y
    p.move(-1, 0, 0.1, FACILITY_MAP)  # face left (default) and try to move left
    if p.x < 1.5:
        issues.append(f"Player clipped through left wall: {p.x:.2f}")
    p.x, p.y = old_x, old_y

    # Move into floor — shouldn't change
    p.move(0, 0, 1.0, FACILITY_MAP)
    if (p.x, p.y) != (old_x, old_y):
        issues.append(f"Player moved with no input: ({p.x:.2f}, {p.y:.2f})")

    print("Collision: OK" if not issues else f"Collision: {len(issues)} issues")
    for issue in issues:
        print(f"  ⚠ {issue}")
    return len(issues) == 0


if __name__ == "__main__":
    print("╔══ GAME DIAGNOSTICS ═══════════════╗")
    print()

    checks = [
        ("Map Integrity", check_map),
        ("Player Geometry", check_player),
        ("Raycaster Engine", check_raycaster),
        ("Collision Detection", check_collision),
    ]

    all_pass = True
    for name, fn in checks:
        print(f"── {name} ──")
        try:
            ok = fn()
            if not ok:
                all_pass = False
        except Exception as e:
            print(f"  ✗ CRASHED: {e}")
            import traceback
            traceback.print_exc()
            all_pass = False
        print()

    print("╚════════════════════════════════════╝")
    sys.exit(0 if all_pass else 1)
"""DDA (Digital Differential Analyzer) raycasting engine."""

from __future__ import annotations

import math
import numpy as np

from .map import Map, WALL_COLORS


class Raycaster:
    """Performs DDA raycasting and produces a framebuffer for each frame."""

    def __init__(self, map_obj: Map, screen_w: int, screen_h: int):
        self.map_obj = map_obj
        self.w = screen_w
        self.h = screen_h
        self.framebuffer = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)

    def render(self, player, targets: list | None = None) -> np.ndarray:
        """Raycast from player POV, return RGB framebuffer."""
        fb = self.framebuffer
        fb.fill(0)

        # Sky gradient (dark blue to lighter blue)
        sky_h = self.h // 2
        for y in range(sky_h):
            t = y / sky_h
            r = int(20 + 30 * (1 - t))
            g = int(20 + 40 * (1 - t))
            b = int(60 + 80 * (1 - t))
            fb[y, :, 0] = r
            fb[y, :, 1] = g
            fb[y, :, 2] = b

        # Floor gradient (dark to medium gray)
        floor_h = self.h // 2
        for y in range(self.h - 1, self.h // 2 - 1, -1):
            t = (y - self.h // 2) / floor_h
            v = int(30 + 40 * (1 - t))
            fb[y, :] = [v, v, v]

        # Raycast each vertical strip
        for x in range(self.w):
            # Normalized screen coordinate [-1, 1]
            camera_x = 2.0 * x / self.w - 1.0

            # Ray direction
            ray_dir_x = player.dir_x + player.plane_x * camera_x
            ray_dir_y = player.dir_y + player.plane_y * camera_x

            # Which box we're in
            map_x = int(player.x)
            map_y = int(player.y)

            # Length of ray from one x-side or y-side to next
            delta_dist_x = abs(1.0 / ray_dir_x) if ray_dir_x != 0 else 1e30
            delta_dist_y = abs(1.0 / ray_dir_y) if ray_dir_y != 0 else 1e30

            # Step direction and initial side distances
            if ray_dir_x < 0:
                step_x = -1
                side_dist_x = (player.x - map_x) * delta_dist_x
            else:
                step_x = 1
                side_dist_x = (map_x + 1.0 - player.x) * delta_dist_x

            if ray_dir_y < 0:
                step_y = -1
                side_dist_y = (player.y - map_y) * delta_dist_y
            else:
                step_y = 1
                side_dist_y = (map_y + 1.0 - player.y) * delta_dist_y

            # DDA loop
            hit = False
            side = 0  # 0 = x-side, 1 = y-side
            while not hit:
                if side_dist_x < side_dist_y:
                    side_dist_x += delta_dist_x
                    map_x += step_x
                    side = 0
                else:
                    side_dist_y += delta_dist_y
                    map_y += step_y
                    side = 1

                if map_x < 0 or map_x >= self.map_obj.width or map_y < 0 or map_y >= self.map_obj.height:
                    hit = True
                elif self.map_obj.get_tile(map_x, map_y) > 0:
                    hit = True

            # Perpendicular distance (avoids fish-eye)
            if side == 0:
                perp_dist = (map_x - player.x + (1 - step_x) / 2) / ray_dir_x
            else:
                perp_dist = (map_y - player.y + (1 - step_y) / 2) / ray_dir_y

            if perp_dist < 0.001:
                perp_dist = 0.001

            # Wall strip height
            line_height = int(self.h / perp_dist)
            draw_start = max(0, -line_height // 2 + self.h // 2)
            draw_end = min(self.h - 1, line_height // 2 + self.h // 2)

            # Wall color based on facing
            if side == 0:
                key = "east" if step_x > 0 else "west"
            else:
                key = "south" if step_y > 0 else "north"

            base_color = WALL_COLORS.get(key, (128, 128, 128))

            # Darken y-sides for depth perception
            if side == 1:
                base_color = tuple(int(c * 0.7) for c in base_color)

            # Distance-based shading (fog)
            shade = max(0.3, min(1.0, 1.0 - perp_dist * 0.04))
            color = tuple(int(c * shade) for c in base_color)

            # Draw the wall strip
            fb[draw_start:draw_end, x] = color

            # Draw targets (guards, etc.) — stub for now
            if targets:
                self._render_targets(fb, x, targets, player, perp_dist, draw_start, draw_end)

        # Draw minimap
        self._draw_minimap(fb, player)

        return fb

    def _draw_minimap(self, fb: np.ndarray, player) -> None:
        """Draw a small overhead map in the top-right corner."""
        mm_size = 120  # minimap pixel size
        mm_scale = 6   # pixels per tile
        mm_x = self.w - mm_size - 10
        mm_y = 10

        # Center the minimap on the player
        cx = int(player.x * mm_scale)
        cy = int(player.y * mm_scale)
        offset_x = cx - mm_size // 2
        offset_y = cy - mm_size // 2

        for my in range(mm_size):
            for mx in range(mm_size):
                px = mx + offset_x
                py = my + offset_y
                tile_x = px // mm_scale
                tile_y = py // mm_scale

                screen_x = mx + mm_x
                screen_y = my + mm_y

                if screen_x >= self.w or screen_y >= self.h:
                    continue

                if self.map_obj.is_solid(tile_x, tile_y):
                    fb[screen_y, screen_x] = (60, 60, 60)
                else:
                    fb[screen_y, screen_x] = (20, 20, 20)

        # Draw player on minimap (bright green dot + direction)
        px = cx - offset_x
        py = cy - offset_y
        if 0 <= px < mm_size and 0 <= py < mm_size:
            sx = px + mm_x
            sy = py + mm_y
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if dx * dx + dy * dy <= 4:
                        pyy = sy + dy
                        pxx = sx + dx
                        if 0 <= pyy < self.h and 0 <= pxx < self.w:
                            fb[pyy, pxx] = (0, 255, 0)

            # Direction line
            for i in range(1, 8):
                dx = int(player.dir_x * i)
                dy = int(player.dir_y * i)
                pyy = sy + dy
                pxx = sx + dx
                if 0 <= pyy < self.h and 0 <= pxx < self.w:
                    fb[pyy, pxx] = (0, 200, 100)

        # Minimap border
        fb[mm_y-1, mm_x:mm_x+mm_size+1] = (100, 100, 100)
        fb[mm_y+mm_size, mm_x:mm_x+mm_size+1] = (100, 100, 100)
        fb[mm_y:mm_y+mm_size+1, mm_x-1] = (100, 100, 100)
        fb[mm_y:mm_y+mm_size+1, mm_x+mm_size] = (100, 100, 100)

    def _render_targets(self, fb, x: int, targets: list, player, perp_dist: float,
                        draw_start: int, draw_end: int) -> None:
        """Placeholder for rendering enemy sprites."""
        # Will be implemented in Phase 2
        pass
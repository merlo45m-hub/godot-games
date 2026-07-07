"""HUD overlay for the 007 raycaster."""

from __future__ import annotations

import numpy as np

from engine.player import Player


class HUD:
    """Heads-up display rendered onto the framebuffer."""

    def __init__(self, screen_w: int, screen_h: int):
        self.w = screen_w
        self.h = screen_h
        self.font_w = 6   # Approximate pixel width per character
        self.font_h = 10  # Approximate pixel height

    def render(self, fb: np.ndarray, player: Player, fps: float) -> None:
        """Draw HUD elements onto the framebuffer."""
        # Health bar (top-left)
        self._draw_health_bar(fb, player)

        # Ammo counter (top-right)
        self._draw_text(fb, f"AMMO: {player.ammo}", self.w - 120, 10, (255, 200, 50))

        # Armor indicator (top-left below health)
        self._draw_text(fb, f"ARMOR: {player.armor}", 10, 30, (100, 150, 255))

        # Gadgets (bottom-left)
        gadgets_str = " | ".join(g.upper() for g in player.gadgets)
        self._draw_text(fb, gadgets_str, 10, self.h - 30, (180, 180, 180))

        # Crosshair (center)
        cx, cy = self.w // 2, self.h // 2
        ch = 6
        fb[cy - 1:cy + 2, cx - ch:cx - 2] = (200, 200, 200)
        fb[cy - 1:cy + 2, cx + 2:cx + ch] = (200, 200, 200)
        fb[cy - ch:cy - 2, cx - 1:cx + 2] = (200, 200, 200)
        fb[cy + 2:cy + ch, cx - 1:cx + 2] = (200, 200, 200)

        # FPS counter (bottom-right)
        self._draw_text(fb, f"{fps:.0f} FPS", self.w - 70, self.h - 20, (100, 255, 100))

    def _draw_health_bar(self, fb: np.ndarray, player: Player) -> None:
        """Draw health bar with color gradient."""
        bar_w = 120
        bar_h = 8
        x, y = 10, 10

        # Background
        fb[y:y + bar_h, x:x + bar_w] = (40, 40, 40)

        # Health fill
        ratio = player.health / player.max_health
        fill_w = int(bar_w * ratio)

        if ratio > 0.6:
            color = (50, 200, 50)
        elif ratio > 0.3:
            color = (200, 200, 50)
        else:
            color = (200, 50, 50)

        if fill_w > 0:
            fb[y:y + bar_h, x:x + fill_w] = color

        # Text
        self._draw_text(fb, f"HP: {player.health}", x + bar_w + 6, y - 2, (255, 255, 255))

    def _draw_text(self, fb: np.ndarray, text: str, x: int, y: int,
                   color: tuple[int, int, int]) -> None:
        """Simple bitmap text renderer (5x7 pixel font)."""
        # Very basic pixel font — just draw a box for now
        # We'll enhance this later with actual bitmap font rendering
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        # Simple underline indicator for presence
        text_w = len(text) * self.font_w
        text_h = self.font_h
        if y + text_h < self.h and x + text_w < self.w:
            # Draw a subtle background bar
            fb[y:y + text_h, x:x + text_w] = (
                fb[y:y + text_h, x:x + text_w] * 0.3 + np.array(color) * 0.7
            ).astype(np.uint8)
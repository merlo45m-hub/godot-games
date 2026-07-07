"""Enemy guard AI — patrol, detect, shoot."""

from __future__ import annotations

import math
import random
import numpy as np


class Enemy:
    """A guard with patrol route, vision cone, and combat behavior."""

    def __init__(self, x: float, y: float, patrol_route: list[tuple[float, float]] | None = None):
        self.x = x
        self.y = y
        self.health = 50
        self.max_health = 50
        self.state = "patrol"  # patrol | alert | combat | dead
        self.speed = 1.8

        # Patrol
        self.patrol_route = patrol_route or [(x, y)]
        self.patrol_index = 0
        self.wait_timer = 0.0

        # Detection
        self.detection_range = 10.0
        self.detection_fov = math.radians(45)  # 45 degree cone
        self.detection_timer = 0.0
        self.alert_duration = 3.0  # seconds before returning to patrol

        # Shooting
        self.shoot_timer = 0.0
        self.shoot_cooldown = 0.5
        self.damage = 9
        self.shoot_range = 12.0

        # Visual
        self.color = (180, 60, 60)
        self.alert_color = (255, 80, 80)
        self.height = 0.8
        self.angle = 0.0  # facing direction

    def update(self, dt: float, player_x: float, player_y: float,
               map_obj, sneak_level: float) -> tuple[bool, float, float]:
        """Update AI. Returns (player_hit, hit_x, hit_y)."""
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        self.shoot_timer = max(0.0, self.shoot_timer - dt)

        match self.state:
            case "patrol":
                self._patrol(dt, map_obj)
                if dist < self.detection_range:
                    self._check_detection(dx, dy, dist, map_obj, player_x, player_y)

            case "alert":
                self.detection_timer -= dt
                self.angle = math.atan2(dy, dx)
                if self.detection_timer <= 0:
                    self.state = "combat" if dist < self.detection_range else "patrol"

            case "combat":
                self.angle = math.atan2(dy, dx)
                if dist < self.shoot_range:
                    return self._try_shoot(player_x, player_y, map_obj)
                if dist > self.detection_range * 1.5:
                    self.state = "patrol"

        return False, 0, 0

    def _patrol(self, dt: float, map_obj):
        """Move along patrol route."""
        if self.wait_timer > 0:
            self.wait_timer -= dt
            return

        tx, ty = self.patrol_route[self.patrol_index]
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 0.3:
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_route)
            self.wait_timer = random.uniform(0.5, 2.0)
            return

        self.angle = math.atan2(dy, dx)
        move = self.speed * 0.3 * dt
        nx = self.x + math.cos(self.angle) * move
        ny = self.y + math.sin(self.angle) * move
        if not map_obj.is_solid(nx, ny):
            self.x, self.y = nx, ny

    def _check_detection(self, dx: float, dy: float, dist: float,
                         map_obj, px: float, py: float):
        """Trigger alert if player is in FOV and line of sight."""
        angle_to_player = math.atan2(dy, dx)
        diff = abs(math.atan2(math.sin(angle_to_player - self.angle),
                              math.cos(angle_to_player - self.angle)))
        if diff < self.detection_fov:
            # Check line of sight via DDA-style ray
            if self._has_los(px, py, map_obj):
                self.state = "alert"
                self.detection_timer = self.alert_duration

    def _has_los(self, tx: float, ty: float, map_obj) -> bool:
        """Simple ray check between enemy and target."""
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        steps = int(dist / 0.5)
        for i in range(1, steps):
            px = self.x + dx * i / steps
            py = self.y + dy * i / steps
            if map_obj.is_solid(px, py):
                return False
        return True

    def _try_shoot(self, px: float, py: float, map_obj) -> tuple[bool, float, float]:
        """Shoot at player if cooldown ready and LOS clear."""
        if self.shoot_timer > 0:
            return False, 0, 0
        if not self._has_los(px, py, map_obj):
            return False, 0, 0

        self.shoot_timer = self.shoot_cooldown
        # Accuracy spread
        spread = random.uniform(-0.05, 0.05)
        return True, px + spread, py + spread

    def take_damage(self, amount: int, from_x: float, from_y: float) -> bool:
        """Return True if killed."""
        self.health -= amount
        if self.health <= 0:
            self.state = "dead"
            return True
        self.state = "combat"
        self.angle = math.atan2(from_y - self.y, from_x - self.x)
        return False

    def is_alive(self) -> bool:
        return self.state != "dead"

    def get_screen_pos(self, player_x: float, player_y: float,
                       player_dir_x: float, player_dir_y: float,
                       plane_x: float, plane_y: float, w: int, h: int):
        """Return (screen_x, sprite_size) for sprite rendering."""
        dx = self.x - player_x
        dy = self.y - player_y

        # Inverse camera transform
        inv_det = 1.0 / (plane_x * player_dir_y - player_dir_x * plane_y)
        transform_x = inv_det * (player_dir_y * dx - player_dir_x * dy)
        transform_y = inv_det * (-plane_y * dx + plane_x * dy)

        if transform_y <= 0:
            return None  # behind player

        screen_x = int((w / 2) * (1 + transform_x / transform_y))
        sprite_height = abs(int(h / transform_y))
        return screen_x, sprite_height, transform_y
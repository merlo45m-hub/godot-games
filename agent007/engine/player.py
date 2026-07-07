"""Player state and movement for the 007 raycaster."""

from __future__ import annotations

import math


class Player:
    """First-person player with position, direction, and FOV."""

    def __init__(self, x: float = 2.0, y: float = 2.0):
        # Position in map coordinates
        self.x = x
        self.y = y

        # Direction vector (unit length)
        self.dir_x = -1.0  # facing left by default
        self.dir_y = 0.0

        # Camera plane (perpendicular to dir, length = FOV factor)
        # FOV = ~90 degrees -> plane length = 0.66
        self.plane_x = 0.0
        self.plane_y = 0.66

        # Movement parameters
        self.move_speed = 3.0   # tiles per second
        self.rot_speed = 2.0    # radians per second
        self.mouse_sensitivity = 0.003

        # Player state
        self.health = 100
        self.max_health = 100
        self.armor = 0
        self.ammo = 30
        self.max_ammo = 60
        self.gadgets = ["watch", "silencer"]
        self.stealth = True  # currently hidden

    def rotate(self, angle: float) -> None:
        """Rotate the player by `angle` radians."""
        old_dir_x = self.dir_x
        self.dir_x = self.dir_x * math.cos(angle) - self.dir_y * math.sin(angle)
        self.dir_y = old_dir_x * math.sin(angle) + self.dir_y * math.cos(angle)

        old_plane_x = self.plane_x
        self.plane_x = self.plane_x * math.cos(angle) - self.plane_y * math.sin(angle)
        self.plane_y = old_plane_x * math.sin(angle) + self.plane_y * math.cos(angle)

    def move(self, forward: float, strafe: float, dt: float, map_obj) -> None:
        """Move forward/backward and strafe, with collision detection."""
        speed = self.move_speed * dt

        # Forward/backward along direction vector
        dx = self.dir_x * forward * speed
        dy = self.dir_y * forward * speed

        # Strafe perpendicular to direction
        if strafe != 0:
            # Perpendicular = (self.dir_y, -self.dir_x) for right, negate for left
            dx += -self.dir_y * strafe * speed * 0.7
            dy += self.dir_x * strafe * speed * 0.7

        # Collision detection — slide along walls
        new_x = self.x + dx
        new_y = self.y + dy

        # Check X movement independently
        if not map_obj.is_solid(new_x, self.y):
            self.x = new_x
        # Check Y movement independently
        if not map_obj.is_solid(self.x, new_y):
            self.y = new_y

    def take_damage(self, amount: int) -> None:
        """Apply damage, armor absorbs 30%."""
        if self.armor > 0:
            armor_damage = min(self.armor, int(amount * 0.3))
            self.armor -= armor_damage
            amount -= armor_damage
        self.health = max(0, self.health - amount)

    def is_alive(self) -> bool:
        return self.health > 0

    def __repr__(self) -> str:
        return f"Player(pos=({self.x:.1f}, {self.y:.1f}), dir=({self.dir_x:.2f}, {self.dir_y:.2f}))"
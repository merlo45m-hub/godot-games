"""Stealth mechanics — visibility, noise, detection."""

from __future__ import annotations

from engine.player import Player


class StealthSystem:
    """Manages stealth state and enemy detection."""

    def __init__(self):
        self.player_visible = False
        self.noise_level = 0.0  # 0.0 = silent, 1.0 = loud
        self.alert_level = 0.0  # 0.0 = unaware, 1.0 = fully alerted
        self.light_level = 0.5  # 0.0 = dark, 1.0 = bright

    def update(self, player: Player, dt: float) -> None:
        """Update stealth state based on player actions."""
        # Decay noise
        self.noise_level = max(0.0, self.noise_level - dt * 2.0)

        # Decay alert
        self.alert_level = max(0.0, self.alert_level - dt * 0.5)

        # Player is stealthed if moving slowly and in darkness
        player.stealth = self.alert_level < 0.3 and self.noise_level < 0.2

    def make_noise(self, amount: float) -> None:
        """Add noise (footsteps, gunshots, etc.)."""
        self.noise_level = min(1.0, self.noise_level + amount)

    def set_alert(self, amount: float) -> None:
        """Trigger alert from enemy sight."""
        self.alert_level = min(1.0, self.alert_level + amount)

    def detection_roll(self) -> bool:
        """Check if player is detected. Called by enemy AI."""
        detection_chance = (
            self.alert_level * 0.3 +
            self.noise_level * 0.2 +
            (1.0 - self.light_level) * 0.1
        )
        # Future: add random roll
        return detection_chance > 0.5
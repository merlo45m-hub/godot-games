"""
Agent 007 — Stealth FPS (Playable)

WASD = move, Mouse = look (G to grab), SPACE = shoot, Esc = quit.
"""
from __future__ import annotations

import math
import sys
import time

import sdl2
import numpy as np

from engine.map import FACILITY_MAP, WALL_COLORS
from engine.player import Player
from engine.raycaster import Raycaster
from engine.renderer import Renderer
from game.hud import HUD
from game.enemy_ai import Enemy
from game.stealth import StealthSystem

SCREEN_W, SCREEN_H = 640, 480


def spawn_enemies(map_obj) -> list[Enemy]:
    """Place patrol routes for each guard."""
    enemies = []
    routes = [
        [(2.5, 2.5), (4.5, 2.5), (4.5, 4.5), (2.5, 4.5)],  # NW room
        [(12.5, 2.5), (14.5, 2.5), (14.5, 4.5), (12.5, 4.5)],  # NE room
        [(2.5, 12.5), (4.5, 12.5), (4.5, 14.5), (2.5, 14.5)],  # SW room
        [(8.5, 5.5), (8.5, 7.5), (10.5, 7.5), (10.5, 5.5)],  # Center patrol
        [(14.5, 12.5), (12.5, 12.5), (12.5, 14.5), (14.5, 14.5)],  # SE room
    ]
    for r in routes:
        e = Enemy(r[0][0], r[0][1], patrol_route=r)
        enemies.append(e)
    return enemies


def render_enemies(fb: np.ndarray, enemies: list[Enemy], player,
                   w: int, h: int):
    """Draw enemy sprites using painter's algorithm (back to front)."""
    player_dir_x = player.dir_x
    player_dir_y = player.dir_y
    plane_x = player.plane_x
    plane_y = player.plane_y

    # Sort enemies by distance (far to near = painter's algorithm for sprites)
    sorted_enemies = sorted(
        [(e, (e.x - player.x)**2 + (e.y - player.y)**2) for e in enemies if e.is_alive()],
        key=lambda x: -x[1]
    )

    for enemy, _ in sorted_enemies:
        dx = enemy.x - player.x
        dy = enemy.y - player.y

        inv_det = 1.0 / (plane_x * player_dir_y - player_dir_x * plane_y)
        tx = inv_det * (player_dir_y * dx - player_dir_x * dy)
        ty = inv_det * (-plane_y * dx + plane_x * dy)

        if ty <= 0.001:
            continue

        sx = int((w / 2) * (1 + tx / ty))
        sh = abs(int(h / ty))
        sw = sh // 2

        if sx + sw < 0 or sx - sw >= w:
            continue

        draw_start_y = max(0, h // 2 - sh // 2)
        draw_end_y = min(h, h // 2 + sh // 2)
        draw_start_x = max(0, sx - sw // 2)
        draw_end_x = min(w, sx + sw // 2)

        # Color based on state
        if enemy.state == "combat":
            color = (255, 60, 40)
        elif enemy.state == "alert":
            color = (255, 200, 40)
        else:
            color = (140, 50, 50)

        # Distance fog
        fog = max(0.3, min(1.0, 1.0 - ty * 0.02))
        color = tuple(int(c * fog) for c in color)

        # Draw enemy as box sprite
        for sy in range(draw_start_y, draw_end_y):
            for sx2 in range(draw_start_x, draw_end_x):
                if 0 <= sy < h and 0 <= sx2 < w:
                    # Simple body shape
                    rel_y = (sy - (h // 2 - sh // 2)) / sh
                    rel_x = (sx2 - (sx - sw // 2)) / sw
                    if 0.05 < rel_x < 0.95 and 0.05 < rel_y < 0.95:
                        fb[sy, sx2] = color

        # Draw health bar above enemy
        if enemy.health < enemy.max_health and enemy.health > 0:
            bar_w = max(sw, 20)
            bar_h = 4
            bar_y = draw_start_y - 8
            ratio = enemy.health / enemy.max_health
            if 0 < bar_y < h:
                start_x = max(0, sx - bar_w // 2)
                end_x = min(w, sx + bar_w // 2)
                fb[bar_y:bar_y + bar_h, start_x:start_x + int(bar_w * ratio)] = (255, 60, 40)
                fb[bar_y:bar_y + bar_h, start_x + int(bar_w * ratio):end_x] = (60, 20, 20)


def main():
    renderer = Renderer("Agent 007 — Stealth FPS", SCREEN_W, SCREEN_H)
    game_map = FACILITY_MAP
    player = Player(x=2.5, y=2.5)
    raycaster = Raycaster(game_map, SCREEN_W, SCREEN_H)
    hud = HUD(SCREEN_W, SCREEN_H)
    stealth = StealthSystem()
    enemies = spawn_enemies(game_map)

    clock = sdl2.SDL_GetPerformanceCounter()
    frequency = sdl2.SDL_GetPerformanceFrequency()
    fps = 0.0
    frame_count = 0
    fps_timer = time.time()

    shoot_cooldown = 0.0
    shoot_recovery = 0.25
    game_over = False
    mission_complete = False
    kill_count = 0
    total_enemies = len(enemies)
    ammo = 30
    max_ammo = 60
    stealth_indicator = "HIDDEN"
    alert_timer = 0.0
    messages = []
    msg_timers = []

    def add_msg(text: str):
        messages.append(text)
        msg_timers.append(2.0)

    add_msg("MISSION: Eliminate all targets")

    while renderer.running:
        new_clock = sdl2.SDL_GetPerformanceCounter()
        dt = (new_clock - clock) / frequency
        clock = new_clock
        dt = min(dt, 0.05)

        frame_count += 1
        if time.time() - fps_timer > 0.5:
            fps = frame_count / (time.time() - fps_timer)
            frame_count = 0
            fps_timer = time.time()

        shoot_cooldown = max(0.0, shoot_cooldown - dt)

        renderer.handle_events()

        # --- INPUT ---
        forward = 0
        strafe = 0

        if renderer.is_key_down(sdl2.SDLK_w): forward += 1
        if renderer.is_key_down(sdl2.SDLK_s): forward -= 1
        if renderer.is_key_down(sdl2.SDLK_a): strafe -= 1
        if renderer.is_key_down(sdl2.SDLK_d): strafe += 1

        if renderer.mouse_dx != 0:
            player.rotate(renderer.mouse_dx * player.mouse_sensitivity)
        if renderer.is_key_down(sdl2.SDLK_LEFT):
            player.rotate(-player.rot_speed * dt)
        if renderer.is_key_down(sdl2.SDLK_RIGHT):
            player.rotate(player.rot_speed * dt)

        if renderer.is_key_down(sdl2.SDLK_SPACE) and shoot_cooldown <= 0 and ammo > 0 and not game_over:
            ammo -= 1
            shoot_cooldown = shoot_recovery
            stealth.make_noise(0.8)
            # Raycheck for hit
            hit_enemy = None
            hit_dist = float("inf")
            for e in enemies:
                if not e.is_alive():
                    continue
                dx = e.x - player.x
                dy = e.y - player.y
                angle_to = math.atan2(dy, dx)
                player_angle = math.atan2(player.dir_y, player.dir_x)
                diff = abs(math.atan2(math.sin(angle_to - player_angle),
                                      math.cos(angle_to - player_angle)))
                dist = math.sqrt(dx * dx + dy * dy)
                if diff < 0.15 and dist < hit_dist:
                    # Check LOS
                    hit = e.take_damage(35, player.x, player.y)
                    if hit:
                        kill_count += 1
                        add_msg(f"TARGET ELIMINATED ({kill_count}/{total_enemies})")
                        if kill_count >= total_enemies:
                            mission_complete = True
                            add_msg("★ MISSION COMPLETE ★")
                    hit_enemy = e
                    hit_dist = dist

        if renderer.is_key_down(sdl2.SDLK_r) and ammo < max_ammo:
            ammo = min(max_ammo, ammo + 8)

        # --- MOVE ---
        if not game_over and not mission_complete:
            player.move(forward, strafe, dt, game_map)

        # --- ENEMY AI ---
        sneak_level = 0.0
        if hasattr(player, 'stealth'):
            sneak_level = 1.0 if player.stealth else 0.0

        for e in enemies:
            if not e.is_alive():
                continue
            hit, hx, hy = e.update(dt, player.x, player.y, game_map, sneak_level)
            if hit:
                player.take_damage(e.damage)

        # --- STEALTH ---
        stealth.update(player, dt)
        if forward != 0 or strafe != 0:
            stealth.make_noise(0.1)

        if stealth.alert_level > 0.3:
            stealth_indicator = "ALERT!" if stealth.alert_level > 0.6 else "CAUTION"
        else:
            stealth_indicator = "HIDDEN" if player.stealth else "VISIBLE"
        alert_timer = stealth.alert_level

        # --- GAME OVER CHECK ---
        if not player.is_alive():
            game_over = True

        # --- UPDATE MESSAGES ---
        for i in range(len(msg_timers) - 1, -1, -1):
            msg_timers[i] -= dt
            if msg_timers[i] <= 0:
                msg_timers.pop(i)
                messages.pop(i)

        # --- RENDER ---
        fb = raycaster.render(player, targets=enemies)
        render_enemies(fb, enemies, player, SCREEN_W, SCREEN_H)

        # HUD overlay
        hud.render(fb, player, fps)

        # Ammo
        hud._draw_text(fb, f"AMMO: {ammo}", SCREEN_W - 140, 10, (255, 200, 50))

        # Stealth indicator
        if stealth_indicator == "HIDDEN":
            si_color = (0, 255, 0)
        elif stealth_indicator == "CAUTION":
            si_color = (255, 255, 0)
        elif stealth_indicator == "VISIBLE":
            si_color = (255, 180, 0)
        else:
            si_color = (255, 0, 0)
        hud._draw_text(fb, f"◆ {stealth_indicator}", SCREEN_W - 200, SCREEN_H - 40, si_color)

        # Kill count
        hud._draw_text(fb, f"KILLS: {kill_count}/{total_enemies}", 10, 50, (255, 120, 40))

        # Messages
        for i, msg in enumerate(messages):
            alpha = min(1.0, msg_timers[i] * 2)
            c = tuple(int(255 * alpha) for _ in range(3))
            hud._draw_text(fb, msg, SCREEN_W // 2 - 100, SCREEN_H // 2 - 40 + i * 20, c)

        # Game over overlay
        if game_over:
            hud._draw_text(fb, "★ MISSION FAILED ★", SCREEN_W // 2 - 100, SCREEN_H // 2, (255, 50, 50))
            hud._draw_text(fb, "Press ESC to exit", SCREEN_W // 2 - 80, SCREEN_H // 2 + 20, (200, 200, 200))

        if mission_complete:
            hud._draw_text(fb, "★ MISSION COMPLETE ★", SCREEN_W // 2 - 120, SCREEN_H // 2, (50, 255, 50))

        renderer.present(fb)
        sdl2.SDL_Delay(1)

    renderer.cleanup()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
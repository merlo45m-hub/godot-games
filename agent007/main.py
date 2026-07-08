"""Main entry point for Android app — adapts the raycaster for touch + portrait."""
from __future__ import annotations

import sys
import time

import sdl2
import numpy as np

from agent007.engine.map import FACILITY_MAP
from agent007.engine.player import Player
from agent007.engine.raycaster import Raycaster
from agent007.engine.renderer import Renderer

SCREEN_W, SCREEN_H = 640, 480


def main():
    renderer = Renderer("Agent 007", SCREEN_W, SCREEN_H)
    game_map = FACILITY_MAP
    player = Player(x=2.5, y=2.5)
    raycaster = Raycaster(game_map, SCREEN_W, SCREEN_H)

    clock = sdl2.SDL_GetPerformanceCounter()
    frequency = sdl2.SDL_GetPerformanceFrequency()

    while renderer.running:
        new_clock = sdl2.SDL_GetPerformanceCounter()
        dt = (new_clock - clock) / frequency
        clock = new_clock
        dt = min(dt, 0.05)

        renderer.handle_events()

        forward = 0
        strafe = 0
        if renderer.is_key_down(sdl2.SDLK_w):
            forward += 1
        if renderer.is_key_down(sdl2.SDLK_s):
            forward -= 1
        if renderer.is_key_down(sdl2.SDLK_a):
            strafe -= 1
        if renderer.is_key_down(sdl2.SDLK_d):
            strafe += 1
        if renderer.mouse_dx != 0:
            player.rotate(renderer.mouse_dx * player.mouse_sensitivity)
        if renderer.is_key_down(sdl2.SDLK_LEFT):
            player.rotate(-player.rot_speed * dt)
        if renderer.is_key_down(sdl2.SDLK_RIGHT):
            player.rotate(player.rot_speed * dt)

        player.move(forward, strafe, dt, game_map)

        fb = raycaster.render(player)
        renderer.present(fb)
        sdl2.SDL_Delay(1)

    renderer.cleanup()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

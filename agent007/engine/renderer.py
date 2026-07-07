"""SDL2-based display and input handling."""

from __future__ import annotations

import ctypes
import os
import numpy as np
import sdl2
import sdl2.ext

# Force software rendering — SDL2's OpenGL/EGL fails on Termux
# DON'T force SDL_VIDEODRIVER — let SDL auto-detect (x11 on Termux:X11, offscreen on Xvfb)
os.environ.setdefault("SDL_RENDER_DRIVER", "software")
# Force Mesa to use softpipe instead of trying Zink (Vulkan→OpenGL) which fails on Termux
os.environ.setdefault("GALLIUM_DRIVER", "softpipe")

from .map import Map
from .player import Player
from .raycaster import Raycaster


class Renderer:
    """Manages the SDL2 window, input, and display loop."""

    def __init__(self, title: str = "Agent 007", width: int = 640, height: int = 480):
        self.width = width
        self.height = height

        # Initialize SDL2
        sdl2.ext.init()

        # Create window
        self.window = sdl2.ext.Window(title, size=(width, height))
        self.window.show()

        # Get the SDL renderer — force software mode for Termux/Xvfb compat
        self.sdl_renderer = sdl2.ext.Renderer(
            self.window, flags=sdl2.SDL_RENDERER_SOFTWARE
        )
        self.sdl_renderer.clear(0x000000)

        # Software surface for our framebuffer
        self.surface = sdl2.SDL_CreateRGBSurface(
            0, width, height, 32,
            0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000
        )

        # SDL texture for hardware blitting
        self.texture = sdl2.SDL_CreateTexture(
            self.sdl_renderer.sdlrenderer,
            sdl2.SDL_PIXELFORMAT_ARGB8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            width, height
        )

        # Input state
        self.keys = set()
        self.running = True
        self.mouse_grabbed = False
        self.mouse_dx = 0

    def handle_events(self) -> None:
        """Process SDL event queue."""
        self.mouse_dx = 0
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                self.running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                self.keys.add(event.key.keysym.sym)
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    self.running = False
                elif event.key.keysym.sym == sdl2.SDLK_g:
                    self.mouse_grabbed = not self.mouse_grabbed
                    sdl2.SDL_SetRelativeMouseMode(
                        sdl2.SDL_TRUE if self.mouse_grabbed else sdl2.SDL_FALSE
                    )
            elif event.type == sdl2.SDL_KEYUP:
                self.keys.discard(event.key.keysym.sym)
            elif event.type == sdl2.SDL_MOUSEMOTION and self.mouse_grabbed:
                self.mouse_dx += event.motion.xrel

    def is_key_down(self, key: int) -> bool:
        return key in self.keys

    def present(self, framebuffer: np.ndarray) -> None:
        """Blit numpy framebuffer to SDL window."""
        # Ensure framebuffer is contiguous
        fb = np.ascontiguousarray(framebuffer, dtype=np.uint8)

        # Convert RGB to ARGB (SDL expects 4 bytes per pixel)
        argb = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        argb[:, :, 0] = fb[:, :, 2]  # B
        argb[:, :, 1] = fb[:, :, 1]  # G
        argb[:, :, 2] = fb[:, :, 0]  # R
        argb[:, :, 3] = 255          # A

        # Update texture
        pixels = ctypes.cast(argb.ctypes.data, ctypes.POINTER(ctypes.c_void_p))
        pitch = self.width * 4
        sdl2.SDL_UpdateTexture(self.texture, None, argb.ctypes.data, pitch)

        # Copy texture to renderer and present
        sdl2.SDL_RenderCopy(self.sdl_renderer.sdlrenderer, self.texture, None, None)
        sdl2.SDL_RenderPresent(self.sdl_renderer.sdlrenderer)

    def cleanup(self) -> None:
        """Free SDL resources."""
        sdl2.SDL_DestroyTexture(self.texture)
        sdl2.SDL_FreeSurface(self.surface)
        sdl2.ext.quit()
"""SDL2 probe — test different configurations."""
import os
import subprocess
import sys

configs = [
    {"SDL_RENDER_DRIVER": "software", "SDL_VIDEODRIVER": "x11"},
    {"SDL_RENDER_DRIVER": "software"},
    {"SDL_RENDER_DRIVER": "software", "SDL_AUDIODRIVER": "dummy"},
    {"SDL_RENDER_DRIVER": "software", "SDL_VIDEODRIVER": "x11",
     "LIBGL_ALWAYS_SOFTWARE": "1", "GALLIUM_DRIVER": "softpipe"},
    {"SDL_RENDER_DRIVER": "software", "SDL_VIDEODRIVER": "x11",
     "SDL_HINT_RENDER_DRIVER": "software", "SDL_HINT_VIDEO_X11_NET_WM_PING": "0"},
    {},
]

test_code = """
import os, sys
import sdl2, sdl2.ext
sdl2.ext.init()
try:
    win = sdl2.ext.Window("test", size=(200, 200))
    win.show()
    r = sdl2.ext.Renderer(win, flags=sdl2.SDL_RENDERER_SOFTWARE)
    r.clear(0x0000FF)
    sdl2.SDL_Delay(50)
    sdl2.ext.quit()
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
    sdl2.ext.quit()
"""

for i, cfg in enumerate(configs):
    env = os.environ.copy()
    env.update(cfg)
    env["DISPLAY"] = ":0"
    r = subprocess.run(
        [sys.executable, "-c", test_code],
        env=env, capture_output=True, text=True, timeout=10
    )
    stderr_short = r.stderr.strip().split("\n")[-1] if r.stderr else ""
    print(f"Config {i+1}: {cfg}")
    print(f"  stdout: {r.stdout.strip()}")
    if stderr_short and "OK" not in r.stdout:
        print(f"  stderr: {stderr_short[:120]}")
    print()
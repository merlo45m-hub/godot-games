# Agent 007 — Stealth FPS

A first-person stealth FPS built in Python with SDL2 for Android.

## Tech Stack

- **Engine**: Custom DDA raycaster (Wolfenstein-style)
- **Display**: SDL2 via `python-sdl2` (Kivy fork)
- **Build**: python-for-android (p4a) for APK generation
- **CI**: GitHub Actions builds APK on push to `main`

## Setup (Local)

```bash
# Requires Python + SDL2 libraries
pip install sdl2 numpy

# Run desktop version
python agent007/main.py
```

## Controls (Desktop)

| Input | Action |
|-------|--------|
| WASD | Move |
| Mouse | Look |
| Shift | Sprint |
| Ctrl | Crouch |
| R | Reload |
| Escape | Unlock mouse |

## CI Build

Push to `main` — GitHub Actions builds an APK automatically via p4a.

Download from Actions workflow artifacts:
https://github.com/merlo45m-hub/agent007-godot/actions

## Project Structure

```
agent007/
├── main.py           # Entry point
├── engine/          # Core systems
│   ├── raycaster.py  # DDA renderer
│   ├── player.py     # Movement/physics
│   ├── map.py        # Level data
│   └── renderer.py   # SDL2 wrapper
└── game/            # Gameplay
    ├── stealth.py    # Visibility/noise
    ├── enemies.py    # Enemy data
    └── hud.py        # UI overlay
```

## Phase Status

- **Phase 1**: Core rendering + movement ✓
- **Phase 2**: Enemy AI + stealth mechanics (in progress)
- **Phase 3**: Mobile touch controls + APK build
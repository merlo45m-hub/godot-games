"""Enemy guards with patrol, detection, and combat — fully integrated."""
from __future__ import annotations

import math
import random

# ============================================================
# FIXED: enemy_ai.py was correct but never wired into main.py.
# This file is an alias so main.py can import it.
# ============================================================

from .enemy_ai import Enemy  # noqa: F401

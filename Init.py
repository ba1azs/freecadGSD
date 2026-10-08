# SPDX-License-Identifier: LGPL-2.1-or-later
"""FreeCAD manual Mod-folder loader for freecadGSD."""

import os
import sys

ROOT = os.path.dirname(__file__)
FREECAD_DIR = os.path.join(ROOT, "freecad")
if FREECAD_DIR not in sys.path:
    sys.path.insert(0, FREECAD_DIR)

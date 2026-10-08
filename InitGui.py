# SPDX-License-Identifier: LGPL-2.1-or-later
"""FreeCAD GUI loader for manual Mod-folder installs of freecadGSD."""

import os
import sys

ROOT = os.path.dirname(__file__)
FREECAD_DIR = os.path.join(ROOT, "freecad")
if FREECAD_DIR not in sys.path:
    sys.path.insert(0, FREECAD_DIR)

# Registers the workbench via Gui.addWorkbench(...)
from freecad.Curves import init_gui  # noqa: F401,E402

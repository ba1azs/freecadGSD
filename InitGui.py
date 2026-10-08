# SPDX-License-Identifier: LGPL-2.1-or-later
"""FreeCAD GUI loader for manual Mod-folder installs of freecadGSD."""

import os
import sys
import traceback

import FreeCAD as App

ROOT = os.path.dirname(__file__)
PARENT = os.path.dirname(ROOT)
FREECAD_DIR = os.path.join(ROOT, "freecad")

# CurvesWB upstream uses a namespace package layout: freecad/Curves/...
# Manual Mod-folder installs do not always add these paths early enough,
# especially on macOS. Add both root and bundled freecad directory.
for path in (ROOT, PARENT, FREECAD_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    # Registers the workbench via Gui.addWorkbench(...)
    from freecad.Curves import init_gui  # noqa: F401,E402
except Exception:
    App.Console.PrintError("freecadGSD failed to load:\n{}\n".format(traceback.format_exc()))
    raise

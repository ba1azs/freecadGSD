# SPDX-License-Identifier: LGPL-2.1-or-later
"""FreeCAD GUI loader for manual Mod-folder installs of freecadGSD."""

import os
import sys
import traceback

import FreeCAD as App


# FreeCAD/macOS may execute InitGui.py without defining __file__, and some
# startup paths have odd exec scopes. Keep this loader as simple top-level
# code: no helper functions required before the import below.
ROOT = None
_MARKER = os.path.join("freecad", "Curves", "init_gui.py")
_CANDIDATES = []
_MODULE_FILE = globals().get("__file__")
if _MODULE_FILE:
    _CANDIDATES.append(os.path.dirname(os.path.abspath(_MODULE_FILE)))
_SPEC = globals().get("__spec__")
_SPEC_ORIGIN = getattr(_SPEC, "origin", None)
if _SPEC_ORIGIN:
    _CANDIDATES.append(os.path.dirname(os.path.abspath(_SPEC_ORIGIN)))
try:
    _CANDIDATES.append(os.path.join(App.getUserAppDataDir(), "Mod", "freecadGSD"))
except Exception:
    pass
_CANDIDATES.append(os.getcwd())
for _candidate in _CANDIDATES:
    if _candidate and os.path.exists(os.path.join(_candidate, _MARKER)):
        ROOT = os.path.abspath(_candidate)
        break
if ROOT is None:
    ROOT = os.path.dirname(os.path.abspath(_MODULE_FILE)) if _MODULE_FILE else os.getcwd()
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

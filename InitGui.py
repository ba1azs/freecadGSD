# SPDX-License-Identifier: LGPL-2.1-or-later
"""FreeCAD GUI loader for manual Mod-folder installs of freecadGSD."""

import os
import sys
import traceback

import FreeCAD as App


def _candidate_roots():
    """Return likely roots for manual FreeCAD Mod-folder loading.

    Some FreeCAD/macOS command paths execute InitGui.py without defining
    ``__file__``. Prefer the module file when available, then fall back to
    FreeCAD's user app data Mod path and the process cwd.
    """
    module_file = globals().get("__file__")
    if module_file:
        yield os.path.dirname(os.path.abspath(module_file))
    spec = globals().get("__spec__")
    spec_origin = getattr(spec, "origin", None)
    if spec_origin:
        yield os.path.dirname(os.path.abspath(spec_origin))
    try:
        yield os.path.join(App.getUserAppDataDir(), "Mod", "freecadGSD")
    except Exception:
        pass
    yield os.getcwd()


def _find_root():
    marker = os.path.join("freecad", "Curves", "init_gui.py")
    for root in _candidate_roots():
        if root and os.path.exists(os.path.join(root, marker)):
            return os.path.abspath(root)
    # Last-resort fallback keeps older behavior for unusual launchers.
    module_file = globals().get("__file__")
    if module_file:
        return os.path.dirname(os.path.abspath(module_file))
    return os.getcwd()


ROOT = _find_root()
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

# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import FreeCADGui as Gui
import FreeCAD as App
from . import ICONPATH


class CurvesWorkbench(Gui.Workbench):
    """freecadGSD workbench: CATIA GSD-like curves and surface helpers for FreeCAD."""
    MenuText = "freecadGSD"
    ToolTip = "CATIA GSD-like curves and surface helpers for FreeCAD"
    Icon = os.path.join(ICONPATH, "blendSurf.svg")
    toolbox = []

    def Initialize(self):
        """This function is executed when FreeCAD starts"""
        # TODO changes module names to lower_with_underscore

        try:
            from . import graphics
            graphics.Marker([App.Vector()])
            # App.Console.PrintMessage("Pivy.graphics interaction library enabled\n")
        except Exception as exc:
            App.Console.PrintWarning(str(exc) + "\nPivy.graphics interaction library is not available on this computer\n")

        from . import lineFP # cleaned
        from . import gordon_profile_FP
        from . import curveExtendFP # TODO use basisSpline
        from . import JoinCurves
        from . import splitCurves_2 # cleaned
        from . import Discretize # cleaned
        from . import approximate
        from . import ParametricBlendCurve # cleaned
        from . import ParametricComb
        from . import ZebraTool
        from . import TrimFace
        from . import GeomInfo
        from . import ExtractShapes # cleaned
        from . import IsoCurve
        from . import Sketch_On_Surface
        from . import Sweep2Rails
        from . import curveOnSurfaceFP
        from . import blendSurfaceFP
        from . import parametricSolid # cleaned
        from . import ProfileSketch
        from . import pasteSVG
        from . import pipeshellProfileFP
        from . import pipeshellFP
        from . import gordonFP
        from . import toConsole
        from . import mixed_curve
        from . import curve_to_script
        from . import sublink_edit
        from . import adjacent_faces
        from . import interpolate
        from . import comp_spring
        from . import ReflectLinesFP
        from . import segmentSurfaceFP
        from . import multiLoftFP
        from . import blendSurfaceFP_new
        from . import blendSolidFP
        from . import FlattenFP
        from . import RotationSweepFP
        from . import SurfaceAnalysisFP
        from . import DraftAnalysisFP
        from . import Truncate_Extend_FP
        from . import WaterLineFP
        from . import MapOnFaceFP
        from . import joinSurfacesFP
        from . import SurfaceLab
        try:
            from gensurf.ui import commands as gensurf_commands, observers as gensurf_observers
            self.__class__._gensurf_commands = gensurf_commands.register_all()
            gensurf_observers.install()
        except Exception as exc:
            App.Console.PrintError("freecadGSD: GenSurf command registration failed: {}\n".format(exc))
            gensurf_commands = None
        silklist = []
        try:
            import importlib
            import sys

            def _find_addon_root():
                module_file = globals().get("__file__")
                candidates = []
                if module_file:
                    candidates.append(os.path.abspath(os.path.join(os.path.dirname(module_file), "..", "..", "..")))
                try:
                    candidates.append(os.path.join(App.getUserAppDataDir(), "Mod", "freecadGSD"))
                except Exception:
                    pass
                for path in sys.path:
                    if path:
                        candidates.append(path)
                for candidate in candidates:
                    if candidate and os.path.isdir(os.path.join(candidate, "Silk")):
                        return os.path.abspath(candidate)
                return os.path.abspath(os.getcwd())

            addon_root = _find_addon_root()
            silk_dir = os.path.join(addon_root, "Silk")
            if silk_dir not in sys.path:
                sys.path.insert(0, silk_dir)
            silk_modules = [
                "ArachNURBS",
                "ControlPoly4",
                "CubicCurve_4",
                "Point_onCurve",
                "ControlPoly4_segment",
                "ControlGrid44",
                "ControlGrid44_Rotate",
                "ControlGrid44_flow",
                "CubicSurface_44",
                "ControlGrid44_EdgeSegment",
                "ControlGrid44_2EdgeSegments",
                "ControlPoly6",
                "CubicCurve_6",
                "ControlGrid66",
                "CubicSurface_66",
                "ControlGrid64",
                "CubicSurface_64",
                "ControlGrid64_2Grid44",
                "ControlGrid64_3_1Grid44",
                "ControlGrid64_normal",
                "ControlGrid64_Surf44",
                "SubGrid33_2Grid64",
                "ControlGrid66_4Sub",
                "SubGrid63_2Surf64",
                "ControlGridNStar66",
                "ControlGridNStar66_NSub",
                "ControlGrid3Star66_3Sub",
                "ControlGrid5Star66_5Sub",
                "CubicNStarSurface_NStar66",
                "StarTrim_CubicNStar",
                "SilkPose",
                "Reload_Silk",
            ]
            for module_name in silk_modules:
                importlib.import_module(module_name)
            silklist = [
                "ControlPoly4",
                "CubicCurve_4",
                "Point_onCurve",
                "ControlPoly4_segment",
                "ControlGrid44",
                "ControlGrid44_Rotate",
                "ControlGrid44_flow",
                "CubicSurface_44",
                "ControlGrid44_EdgeSegment",
                "ControlGrid44_2EdgeSegments",
                "ControlPoly6",
                "CubicCurve_6",
                "ControlGrid66",
                "CubicSurface_66",
                "ControlGrid64",
                "CubicSurface_64",
                "ControlGrid64_2Grid44",
                "ControlGrid64_3_1Grid44",
                "ControlGrid64_normal",
                "ControlGrid64_Surf44",
                "SubGrid33_2Grid64",
                "ControlGrid66_4Sub",
                "SubGrid63_2Surf64",
                "ControlGridNStar66",
                "ControlGridNStar66_NSub",
                "ControlGrid3Star66_3Sub",
                "ControlGrid5Star66_5Sub",
                "CubicNStarSurface_NStar66",
                "StarTrim_CubicNStar",
                "SilkPose",
                "Reload_Silk",
            ]
        except Exception as exc:
            App.Console.PrintError("freecadGSD: Silk command registration failed: {}\n".format(exc))
        # from . import ProfileSupportFP
        # from . import Sweep2RailsFP
        # from . import HQRuledSurfaceFP
        # from . import HelicalSweepFP
        # import sectionSketch

        curvelist = ["Curves_line", "gordon_profile", "mixed_curve", "extend", "join", "split",
                     "Discretize", "Approximate", "Interpolate", "ParametricBlendCurve",
                     "ParametricComb", "cos"]

        surflist = ["ZebraTool", "Trim", "IsoCurve", "SoS", "Curves_MapOnFace", "sw2r", "profileSupportCmd",
                    "profile", "pipeshell", "gordon", "segment_surface", "Curves_JoinSurface", "comp_spring",
                    "ReflectLines", "MultiLoft", "Curves_BlendSurf2", "Curves_BlendSolid",
                    "Curves_FlattenFace", "Curves_RotationSweep", 'Curves_SurfaceAnalysis',
                    'Curves_DraftAnalysis', "Curve_TruncateExtendCmd", "Curves_WaterlineCurves",]
        surfacelablist = ["SurfaceLab_PositionedSketch", "SurfaceLab_CreateLinkedPositionedSketch", "SurfaceLab_SyncLinkedPositionedSketches", "SurfaceLab_BSplineFromPoints", "SurfaceLab_LoftSurface", "SurfaceLab_BoundarySurface"]  # ,"Curves_ProfileSupport", "Curves_Sweep2Rails"]
        misclist = ["GeomInfo", "extract", "solid", "pasteSVG", "to_console", "Curves_adjacent_faces",
                    "Curves_bspline_to_console"]

        self.appendToolbar("freecadGSD Curves", curvelist)
        self.appendToolbar("Surfaces", surflist)
        self.appendToolbar("SurfaceLab", surfacelablist)
        if gensurf_commands is not None:
            for title, items in gensurf_commands.TOOLBARS:
                self.appendToolbar(title, items)
        if silklist:
            self.appendToolbar("Silk Commands", silklist)
        self.appendToolbar("Misc.", misclist)
        self.appendMenu("freecadGSD", curvelist)
        self.appendMenu("Surfaces", surflist)
        self.appendMenu("SurfaceLab", surfacelablist)
        if gensurf_commands is not None:
            self.appendMenu("GenSurf", gensurf_commands.MENU)
        if silklist:
            self.appendMenu("Silk", silklist)
        self.appendMenu("Misc.", misclist)

    def Activated(self):
        """This function is executed when the workbench is activated"""
        if App.GuiUp:
            self.isObserving = True
            self.Selection = []
            self.View_Directions = []
            Gui.Selection.addObserver(self)
        try:
            from gensurf.ui.view_provider import ensure_view_providers
            ensure_view_providers(App.ActiveDocument)
        except Exception as exc:
            App.Console.PrintWarning("freecadGSD: GenSurf view-provider activation skipped: {}\n".format(exc))
        return

    def Deactivated(self):
        """This function is executed when the workbench is deactivated"""
        if self.isObserving:
            Gui.Selection.removeObserver(self)
            self.isObserving = False
        return

    def addSelection(self, doc, obj, sub, pnt):
        """Custom selection observer that keeps selection order."""
        try:
            rot = Gui.getDocument(doc).ActiveView.getCameraOrientation()
            direction = rot.multVec(App.Vector(0, 0, -1))
            self.View_Directions.append(direction)
        except AttributeError:  # When ActiveView has no camera (TechDraw)
            pass
        self.Selection.append(Gui.Selection.getSelectionObject(doc, obj, sub, pnt))

    def removeSelection(self, doc, obj, sub):
        nl = []
        cl = []
        for i in range(len(self.Selection)):
            doc_match = (doc == self.Selection[i].Document.Name)
            obj_match = (obj == self.Selection[i].Object.Name)
            sub_match = (len(sub) == 0) or (sub in self.Selection[i].SubElementNames)
            if doc_match and obj_match and sub_match:
                continue
            nl.append(self.Selection[i])
            cl.append(self.View_Directions[i])
        self.Selection = nl

    def clearSelection(self, doc):
        self.Selection = []
        self.View_Directions = []

    def ContextMenu(self, recipient):
        """This is executed whenever the user right-clicks on screen.
        recipient" will be either 'view' or 'tree'"""
        if recipient == "View":
            contextlist = ["Curves_adjacent_faces", "Curves_bspline_to_console"]  # list of commands
            self.appendContextMenu("Curves", contextlist)
        elif recipient == "Tree":
            contextlist = ["join", "split", "Discretize", "Approximate", "Interpolate"]  # list of commands
            self.appendContextMenu("Curves", contextlist)

    def GetClassName(self):
        """This function is mandatory if this is a full python workbench"""
        return "Gui::PythonWorkbench"


Gui.addWorkbench(CurvesWorkbench())

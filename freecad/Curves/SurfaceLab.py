# SPDX-License-Identifier: LGPL-2.1-or-later

"""Small CATIA-like helper commands added on top of Curves Workbench.

These are intentionally simple starter tools. They create ordinary Part shapes so
we can iterate quickly before turning the useful ones into full parametric
FeaturePython objects.
"""

__title__ = "SurfaceLab helpers"
__author__ = "Balazs / Ovadclaw"
__license__ = "LGPL 2.1"

import os

import FreeCAD
import FreeCADGui
import Part

from freecad.Curves import ICONPATH

TOOL_ICON = os.path.join(ICONPATH, "blendSurf.svg")


def _active_doc():
    doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument("SurfaceLab")
    return doc


def _selection_shapes():
    shapes = []
    for sel in FreeCADGui.Selection.getSelectionEx('', 0):
        if sel.SubElementNames:
            for path in sel.SubElementNames:
                shape = sel.Object.getSubObject(path)
                if shape is not None:
                    shapes.append(shape)
        elif hasattr(sel.Object, "Shape"):
            shapes.append(sel.Object.Shape)
    return shapes


def _selected_points():
    points = []
    for shape in _selection_shapes():
        if getattr(shape, "ShapeType", None) == "Vertex":
            points.append(shape.Point)
        elif hasattr(shape, "Vertexes"):
            points.extend(vertex.Point for vertex in shape.Vertexes)
    return points


def _selected_edges_or_wires():
    items = []
    for shape in _selection_shapes():
        shape_type = getattr(shape, "ShapeType", None)
        if shape_type in ("Edge", "Wire"):
            items.append(shape)
        elif hasattr(shape, "Wires") and shape.Wires:
            items.extend(shape.Wires)
        elif hasattr(shape, "Edges") and shape.Edges:
            items.extend(shape.Edges)
    return items


def _message(text):
    FreeCAD.Console.PrintMessage("SurfaceLab: {}\n".format(text))


def _error(title, usage):
    FreeCAD.Console.PrintError("{} :\n{}\n".format(title, usage))


class SurfaceLabBSplineFromPointsCommand:
    """Create a BSpline curve through selected vertices/points."""

    title = "SurfaceLab BSpline From Points"
    doc = "Create a BSpline curve through selected vertices/points."
    usage = "Select at least two vertices/points in order, then run the command."

    def Activated(self):
        points = _selected_points()
        if len(points) < 2:
            _error(self.title, self.usage)
            return

        curve = Part.BSplineCurve()
        curve.interpolate(points)

        obj = _active_doc().addObject("Part::Feature", "SurfaceLab_BSpline")
        obj.Shape = curve.toShape()
        FreeCAD.ActiveDocument.recompute()
        _message("Created BSpline through {} points.".format(len(points)))

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {
            'Pixmap': TOOL_ICON,
            'MenuText': self.title,
            'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(self.doc, self.usage),
        }


class SurfaceLabLoftSurfaceCommand:
    """Loft selected sections into a surface."""

    title = "SurfaceLab Loft Surface"
    doc = "Loft selected edges or wires into an open surface."
    usage = "Select at least two section edges/wires, then run the command."

    def Activated(self):
        sections = _selected_edges_or_wires()
        if len(sections) < 2:
            _error(self.title, self.usage)
            return

        loft_sections = []
        try:
            for section in sections:
                if getattr(section, "ShapeType", None) == "Edge":
                    loft_sections.append(Part.Wire([section]))
                else:
                    loft_sections.append(section)
            shape = Part.makeLoft(loft_sections, False, False, False)
        except Exception as exc:
            FreeCAD.Console.PrintError("SurfaceLab loft failed: {}\n".format(exc))
            return

        obj = _active_doc().addObject("Part::Feature", "SurfaceLab_Loft")
        obj.Shape = shape
        FreeCAD.ActiveDocument.recompute()
        _message("Created loft from {} sections.".format(len(loft_sections)))

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {
            'Pixmap': TOOL_ICON,
            'MenuText': self.title,
            'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(self.doc, self.usage),
        }


class SurfaceLabBoundarySurfaceCommand:
    """Create a planar filled face from selected boundary edges."""

    title = "SurfaceLab Boundary Surface"
    doc = "Create a filled face from selected closed boundary edges."
    usage = "Select at least three boundary edges forming one closed wire, then run the command."

    def Activated(self):
        edges = []
        for item in _selected_edges_or_wires():
            if getattr(item, "ShapeType", None) == "Wire":
                edges.extend(item.Edges)
            else:
                edges.append(item)

        if len(edges) < 3:
            _error(self.title, self.usage)
            return

        try:
            wire = Part.Wire(edges)
            if not wire.isClosed():
                FreeCAD.Console.PrintError("SurfaceLab: selected boundary is not closed.\n")
                return
            face = Part.Face(wire)
        except Exception as exc:
            FreeCAD.Console.PrintError("SurfaceLab boundary surface failed: {}\n".format(exc))
            return

        obj = _active_doc().addObject("Part::Feature", "SurfaceLab_BoundarySurface")
        obj.Shape = face
        FreeCAD.ActiveDocument.recompute()
        _message("Created boundary surface from {} edges.".format(len(edges)))

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {
            'Pixmap': TOOL_ICON,
            'MenuText': self.title,
            'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(self.doc, self.usage),
        }


FreeCADGui.addCommand('SurfaceLab_BSplineFromPoints', SurfaceLabBSplineFromPointsCommand())
FreeCADGui.addCommand('SurfaceLab_LoftSurface', SurfaceLabLoftSurfaceCommand())
FreeCADGui.addCommand('SurfaceLab_BoundarySurface', SurfaceLabBoundarySurfaceCommand())

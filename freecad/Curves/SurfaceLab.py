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


# CATIA Positioned Sketch notes used for this command:
# CATIA lets the user define a sketch support/reference plane plus the sketch
# absolute-axis origin and orientation. The horizontal H direction can be made
# parallel to a selected line and can be swapped/reversed. FreeCAD exposes the
# same practical result by creating a Sketcher object whose Placement basis is
# local X/H, local Y/V, local Z/normal.


def _selection_subshapes_with_owner():
    items = []
    for sel in FreeCADGui.Selection.getSelectionEx('', 0):
        if sel.SubElementNames:
            for path in sel.SubElementNames:
                shape = sel.Object.getSubObject(path)
                if shape is not None:
                    items.append((sel.Object, path, shape))
        elif hasattr(sel.Object, "Shape"):
            items.append((sel.Object, "", sel.Object.Shape))
    return items


def _point_from_shape(shape):
    if getattr(shape, "ShapeType", None) == "Vertex":
        return shape.Point
    if hasattr(shape, "Point"):
        return shape.Point
    vertexes = getattr(shape, "Vertexes", None)
    if vertexes and len(vertexes) == 1:
        return vertexes[0].Point
    return None


def _edge_direction(edge):
    try:
        if hasattr(edge, "Curve") and hasattr(edge.Curve, "Direction"):
            return FreeCAD.Vector(edge.Curve.Direction)
    except Exception:
        pass
    try:
        vertexes = edge.Vertexes
        if len(vertexes) >= 2:
            direction = vertexes[-1].Point - vertexes[0].Point
            if direction.Length > 1e-9:
                return direction
    except Exception:
        pass
    try:
        first = edge.firstParameter()
        last = edge.lastParameter()
        mid = 0.5 * (first + last)
        direction = edge.tangentAt(mid)
        if direction.Length > 1e-9:
            return direction
    except Exception:
        pass
    return None


def _plane_normal(face):
    try:
        surface = face.Surface
        if hasattr(surface, "Axis"):
            normal = FreeCAD.Vector(surface.Axis)
            if normal.Length > 1e-9:
                return normal
    except Exception:
        pass
    try:
        umin, umax, vmin, vmax = face.ParameterRange
        u = 0.5 * (umin + umax)
        v = 0.5 * (vmin + vmax)
        normal = face.normalAt(u, v)
        if normal.Length > 1e-9:
            return normal
    except Exception:
        pass
    return None


def _first_positioned_sketch_inputs():
    """Return (face_owner, face_path, origin, line_direction, plane_normal)."""
    face_owner = None
    face_path = ""
    origin = None
    line_direction = None
    plane_normal = None

    for owner, path, shape in _selection_subshapes_with_owner():
        shape_type = getattr(shape, "ShapeType", None)
        if shape_type == "Face" and plane_normal is None:
            normal = _plane_normal(shape)
            if normal is not None:
                face_owner = owner
                face_path = path
                plane_normal = normal
        elif shape_type == "Edge" and line_direction is None:
            line_direction = _edge_direction(shape)
        elif shape_type == "Vertex" and origin is None:
            origin = shape.Point
        elif origin is None:
            origin = _point_from_shape(shape)

    return face_owner, face_path, origin, line_direction, plane_normal


def _make_rotation_from_axes(x_axis, y_axis, z_axis):
    """Create a FreeCAD Rotation whose local XYZ axes map to the supplied axes."""
    try:
        return FreeCAD.Rotation(x_axis, y_axis, z_axis, "XYZ")
    except Exception:
        matrix = FreeCAD.Matrix()
        matrix.A11, matrix.A21, matrix.A31 = x_axis.x, x_axis.y, x_axis.z
        matrix.A12, matrix.A22, matrix.A32 = y_axis.x, y_axis.y, y_axis.z
        matrix.A13, matrix.A23, matrix.A33 = z_axis.x, z_axis.y, z_axis.z
        matrix.A44 = 1.0
        return FreeCAD.Placement(matrix).Rotation


def _object_label(owner, path):
    label = getattr(owner, "Label", None) or getattr(owner, "Name", "Selection")
    if path:
        return "{}.{}".format(label, path)
    return label


def _create_positioned_sketch(doc, origin, line_direction, plane_normal, reverse_h=False, reverse_v=False, swap_hv=False):
    z_axis = FreeCAD.Vector(plane_normal)
    if z_axis.Length <= 1e-9:
        raise ValueError("plane normal is zero")
    z_axis.normalize()

    # CATIA's H direction is constrained parallel to the selected line. If the
    # selected line is not exactly on the plane, use its projection onto the
    # sketch plane so local X lies in the sketch plane.
    x_axis = FreeCAD.Vector(line_direction)
    x_axis = x_axis - FreeCAD.Vector(z_axis).multiply(x_axis.dot(z_axis))
    if x_axis.Length <= 1e-9:
        raise ValueError("selected line is normal to the plane, so it cannot define H/X")
    x_axis.normalize()

    y_axis = z_axis.cross(x_axis)
    if y_axis.Length <= 1e-9:
        raise ValueError("could not compute V/Y axis")
    y_axis.normalize()
    x_axis = y_axis.cross(z_axis)
    x_axis.normalize()

    if reverse_h:
        x_axis = x_axis.multiply(-1.0)
    if reverse_v:
        y_axis = y_axis.multiply(-1.0)
    if swap_hv:
        x_axis, y_axis = y_axis, x_axis

    # Keep the basis orthogonal. If a single direction was reversed or H/V were
    # swapped, this deliberately flips the sketch side like CATIA's reverse
    # direction controls can do.
    z_axis = x_axis.cross(y_axis)
    if z_axis.Length <= 1e-9:
        raise ValueError("invalid H/V orientation")
    z_axis.normalize()
    y_axis = z_axis.cross(x_axis)
    y_axis.normalize()

    try:
        sketch = doc.addObject("Sketcher::SketchObject", "PositionedSketch")
    except Exception as exc:
        raise RuntimeError("could not create Sketcher::SketchObject: {}".format(exc))

    sketch.Placement = FreeCAD.Placement(origin, _make_rotation_from_axes(x_axis, y_axis, z_axis))
    try:
        sketch.addProperty("App::PropertyString", "SurfaceLabPositioning", "SurfaceLab", "CATIA-like positioned sketch reference summary")
        sketch.SurfaceLabPositioning = "Origin from selected point; H/X parallel to selected line projected onto selected plane."
    except Exception:
        pass
    try:
        sketch.addProperty("App::PropertyVector", "SurfaceLabHDirection", "SurfaceLab", "World H/X direction used at creation")
        sketch.SurfaceLabHDirection = x_axis
        sketch.addProperty("App::PropertyVector", "SurfaceLabVDirection", "SurfaceLab", "World V/Y direction used at creation")
        sketch.SurfaceLabVDirection = y_axis
        sketch.addProperty("App::PropertyVector", "SurfaceLabNormal", "SurfaceLab", "World sketch plane normal used at creation")
        sketch.SurfaceLabNormal = z_axis
    except Exception:
        pass
    return sketch, x_axis, y_axis, z_axis


class _PositionedSketchDialog:
    """Small CATIA-like Sketch Positioning popup."""

    def __init__(self, command):
        self.command = command
        self.face_owner = None
        self.face_path = ""
        self.origin = None
        self.line_direction = None
        self.plane_normal = None
        self._build()
        self.read_selection()

    def _qt_modules(self):
        try:
            from PySide import QtCore, QtGui
            return QtCore, QtGui, QtGui
        except Exception:
            from PySide2 import QtCore, QtWidgets
            return QtCore, QtWidgets, QtWidgets

    def _build(self):
        self.QtCore, self.QtGui, self.QtWidgets = self._qt_modules()
        self.dialog = self.QtWidgets.QDialog()
        self.dialog.setWindowTitle("Positioned Sketch")
        layout = self.QtWidgets.QVBoxLayout(self.dialog)

        info = self.QtWidgets.QLabel(
            "Create a CATIA-like positioned sketch: choose support plane, origin, and H direction."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        form = self.QtWidgets.QFormLayout()
        self.support_label = self.QtWidgets.QLabel("not selected")
        self.origin_label = self.QtWidgets.QLabel("not selected")
        self.direction_label = self.QtWidgets.QLabel("not selected")
        form.addRow("Support / plane", self.support_label)
        form.addRow("Origin", self.origin_label)
        form.addRow("Orientation H", self.direction_label)
        layout.addLayout(form)

        read_btn = self.QtWidgets.QPushButton("Read current selection")
        read_btn.clicked.connect(self.read_selection)
        layout.addWidget(read_btn)

        options = self.QtWidgets.QGroupBox("Orientation")
        option_layout = self.QtWidgets.QVBoxLayout(options)
        self.reverse_h = self.QtWidgets.QCheckBox("Reverse H direction")
        self.reverse_v = self.QtWidgets.QCheckBox("Reverse V direction")
        self.swap_hv = self.QtWidgets.QCheckBox("Swap H and V")
        option_layout.addWidget(self.reverse_h)
        option_layout.addWidget(self.reverse_v)
        option_layout.addWidget(self.swap_hv)
        layout.addWidget(options)

        hint = self.QtWidgets.QLabel(
            "Tip: select one face/plane, one point/vertex, and one edge/line before opening, "
            "or change selection and press Read current selection."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = self.QtWidgets.QDialogButtonBox(
            self.QtWidgets.QDialogButtonBox.Ok | self.QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.dialog.reject)
        layout.addWidget(buttons)

    def read_selection(self):
        self.face_owner, self.face_path, self.origin, self.line_direction, self.plane_normal = _first_positioned_sketch_inputs()
        if self.plane_normal is None:
            self.support_label.setText("not selected")
        else:
            self.support_label.setText(_object_label(self.face_owner, self.face_path))
        if self.origin is None:
            self.origin_label.setText("not selected")
        else:
            self.origin_label.setText("{:.3f}, {:.3f}, {:.3f}".format(self.origin.x, self.origin.y, self.origin.z))
        if self.line_direction is None:
            self.direction_label.setText("not selected")
        else:
            direction = FreeCAD.Vector(self.line_direction)
            if direction.Length > 1e-9:
                direction.normalize()
            self.direction_label.setText("H parallel to {:.3f}, {:.3f}, {:.3f}".format(direction.x, direction.y, direction.z))

    def accept(self):
        if self.origin is None or self.line_direction is None or self.plane_normal is None:
            self.QtWidgets.QMessageBox.warning(
                self.dialog,
                "Positioned Sketch",
                "Select one planar face/plane, one vertex/point for Origin, and one edge/line for H direction."
            )
            return
        try:
            sketch, x_axis, y_axis, z_axis = _create_positioned_sketch(
                _active_doc(),
                self.origin,
                self.line_direction,
                self.plane_normal,
                self.reverse_h.isChecked(),
                self.reverse_v.isChecked(),
                self.swap_hv.isChecked(),
            )
        except Exception as exc:
            self.QtWidgets.QMessageBox.critical(self.dialog, "Positioned Sketch", str(exc))
            return
        FreeCAD.ActiveDocument.recompute()
        try:
            FreeCADGui.ActiveDocument.setEdit(sketch.Name)
        except Exception:
            pass
        _message("Created positioned sketch from popup.")
        self.dialog.accept()

    def exec_(self):
        return self.dialog.exec_()


class SurfaceLabPositionedSketchCommand:
    """Create a CATIA-like positioned sketch from a plane, point, and line."""

    title = "SurfaceLab Positioned Sketch"
    doc = "Create a sketch whose origin is a selected point and whose horizontal H/X axis follows a selected line on a selected plane."
    usage = (
        "Select one planar face/plane, one vertex/point for the origin, and one edge/line for the H/X direction, "
        "then run the command. A CATIA-like positioning popup opens."
    )

    def Activated(self):
        if getattr(FreeCAD, "GuiUp", False):
            try:
                dialog = _PositionedSketchDialog(self)
                dialog.exec_()
                return
            except Exception as exc:
                FreeCAD.Console.PrintWarning("SurfaceLab positioned sketch popup unavailable, using direct mode: {}\n".format(exc))

        doc = _active_doc()
        face_owner, face_path, origin, line_direction, plane_normal = _first_positioned_sketch_inputs()
        if origin is None or line_direction is None or plane_normal is None:
            _error(self.title, self.usage)
            return
        try:
            sketch, x_axis, y_axis, z_axis = _create_positioned_sketch(doc, origin, line_direction, plane_normal)
        except Exception as exc:
            FreeCAD.Console.PrintError("SurfaceLab positioned sketch failed: {}\n".format(exc))
            return
        doc.recompute()
        try:
            FreeCADGui.ActiveDocument.setEdit(sketch.Name)
        except Exception:
            pass
        _message("Created positioned sketch: origin at selected point, H/X parallel to selected line.")

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
FreeCADGui.addCommand('SurfaceLab_PositionedSketch', SurfaceLabPositionedSketchCommand())

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
POSITIONED_SKETCH_ICON = os.path.join(ICONPATH, "surfacelab_positioned_sketch.svg")
LINKED_POSITIONED_SKETCH_ICON = os.path.join(ICONPATH, "surfacelab_linked_positioned_sketch.svg")
MANAGE_LINKED_SKETCH_ICON = os.path.join(ICONPATH, "surfacelab_manage_linked_sketch.svg")
SYNC_LINKED_SKETCH_ICON = os.path.join(ICONPATH, "surfacelab_sync_linked_sketches.svg")
SKETCH_VISIBLE_SPACE_ICON = os.path.join(ICONPATH, "surfacelab_switch_visible_space.svg")
SKETCH_ISOLATE_ICON = os.path.join(ICONPATH, "surfacelab_isolate_sketch_geometry.svg")


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


def _selected_positioned_sketch():
    for sel in FreeCADGui.Selection.getSelectionEx('', 0):
        obj = getattr(sel, "Object", None)
        if obj is None:
            continue
        if getattr(obj, "TypeId", "") == "Sketcher::SketchObject" and getattr(obj, "Name", "").startswith("PositionedSketch"):
            return obj
        if getattr(obj, "TypeId", "") == "Sketcher::SketchObject" and hasattr(obj, "SurfaceLabPositioning"):
            return obj
    return None


def _placement_axes(sketch):
    placement = sketch.Placement
    rotation = placement.Rotation
    x_axis = rotation.multVec(FreeCAD.Vector(1, 0, 0))
    y_axis = rotation.multVec(FreeCAD.Vector(0, 1, 0))
    z_axis = rotation.multVec(FreeCAD.Vector(0, 0, 1))
    for axis in (x_axis, y_axis, z_axis):
        if axis.Length > 1e-9:
            axis.normalize()
    return FreeCAD.Vector(placement.Base), x_axis, y_axis, z_axis


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


def _create_positioned_sketch(
    doc,
    origin,
    line_direction,
    plane_normal,
    reverse_h=False,
    reverse_v=False,
    swap_hv=False,
    existing_sketch=None,
    v_direction=None,
):
    z_axis = FreeCAD.Vector(plane_normal)
    if z_axis.Length <= 1e-9:
        raise ValueError("plane normal is zero")
    z_axis.normalize()

    x_axis = FreeCAD.Vector(line_direction)
    x_axis = x_axis - FreeCAD.Vector(z_axis).multiply(x_axis.dot(z_axis))
    if x_axis.Length <= 1e-9:
        raise ValueError("selected line is normal to the plane, so it cannot define H/X")
    x_axis.normalize()

    if v_direction is None:
        y_axis = z_axis.cross(x_axis)
    else:
        y_axis = FreeCAD.Vector(v_direction)
        y_axis = y_axis - FreeCAD.Vector(z_axis).multiply(y_axis.dot(z_axis))
        y_axis = y_axis - FreeCAD.Vector(x_axis).multiply(y_axis.dot(x_axis))
    if y_axis.Length <= 1e-9:
        raise ValueError("could not compute V/Y axis")
    y_axis.normalize()
    x_axis = y_axis.cross(z_axis)
    if x_axis.dot(line_direction) < 0:
        x_axis = x_axis.multiply(-1.0)
        y_axis = y_axis.multiply(-1.0)
    x_axis.normalize()

    if reverse_h:
        x_axis = x_axis.multiply(-1.0)
    if reverse_v:
        y_axis = y_axis.multiply(-1.0)
    if swap_hv:
        x_axis, y_axis = y_axis, x_axis

    z_axis = x_axis.cross(y_axis)
    if z_axis.Length <= 1e-9:
        raise ValueError("invalid H/V orientation")
    z_axis.normalize()
    y_axis = z_axis.cross(x_axis)
    y_axis.normalize()

    if existing_sketch is None:
        try:
            sketch = doc.addObject("Sketcher::SketchObject", "PositionedSketch")
        except Exception as exc:
            raise RuntimeError("could not create Sketcher::SketchObject: {}".format(exc))
    else:
        sketch = existing_sketch

    sketch.Placement = FreeCAD.Placement(origin, _make_rotation_from_axes(x_axis, y_axis, z_axis))
    try:
        if not hasattr(sketch, "SurfaceLabPositioning"):
            sketch.addProperty("App::PropertyString", "SurfaceLabPositioning", "SurfaceLab", "CATIA-like positioned sketch reference summary")
        sketch.SurfaceLabPositioning = "Origin from selected point; H/X parallel to selected line projected onto selected plane."
    except Exception:
        pass
    try:
        if not hasattr(sketch, "SurfaceLabHDirection"):
            sketch.addProperty("App::PropertyVector", "SurfaceLabHDirection", "SurfaceLab", "World H/X direction used at creation")
        sketch.SurfaceLabHDirection = x_axis
        if not hasattr(sketch, "SurfaceLabVDirection"):
            sketch.addProperty("App::PropertyVector", "SurfaceLabVDirection", "SurfaceLab", "World V/Y direction used at creation")
        sketch.SurfaceLabVDirection = y_axis
        if not hasattr(sketch, "SurfaceLabNormal"):
            sketch.addProperty("App::PropertyVector", "SurfaceLabNormal", "SurfaceLab", "World sketch plane normal used at creation")
        sketch.SurfaceLabNormal = z_axis
    except Exception:
        pass
    return sketch, x_axis, y_axis, z_axis


_SURFACELAB_POSITIONED_SKETCH_DIALOG = None


class _PositionedSketchDialog:
    """Small CATIA-like Sketch Positioning popup."""

    def __init__(self, command, sketch=None):
        self.command = command
        self.sketch = sketch
        self.face_owner = None
        self.face_path = ""
        self.origin = None
        self.line_direction = None
        self.v_direction = None
        self.plane_normal = None
        self.pick_mode = None
        self.preview_objects = []
        self.preview_length = 20.0
        if self.sketch is not None:
            self.origin, self.line_direction, self.v_direction, self.plane_normal = _placement_axes(self.sketch)
        self._build()
        if self.sketch is None:
            self.read_selection()
        else:
            self.update_labels()
            self.update_preview()
        try:
            FreeCADGui.Selection.addObserver(self)
        except Exception:
            pass

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
        self.dialog.setWindowTitle("Edit Positioned Sketch" if self.sketch is not None else "Positioned Sketch")
        try:
            self.dialog.setModal(False)
        except Exception:
            pass
        layout = self.QtWidgets.QVBoxLayout(self.dialog)

        info = self.QtWidgets.QLabel(
            "Edit CATIA-like sketch positioning: change H/V direction or read a new support/origin/H selection." if self.sketch is not None else
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

        pick_group = self.QtWidgets.QGroupBox("Pick after click")
        pick_layout = self.QtWidgets.QVBoxLayout(pick_group)
        self.pick_status = self.QtWidgets.QLabel("Select a plane, point, or line directly; or use pick buttons to force one input type.")
        self.pick_status.setWordWrap(True)
        pick_layout.addWidget(self.pick_status)
        pick_buttons = self.QtWidgets.QHBoxLayout()
        self.pick_support_btn = self.QtWidgets.QPushButton("Pick support")
        self.pick_origin_btn = self.QtWidgets.QPushButton("Pick origin")
        self.pick_h_btn = self.QtWidgets.QPushButton("Pick H direction")
        self.pick_support_btn.clicked.connect(lambda: self.arm_pick("support"))
        self.pick_origin_btn.clicked.connect(lambda: self.arm_pick("origin"))
        self.pick_h_btn.clicked.connect(lambda: self.arm_pick("h"))
        pick_buttons.addWidget(self.pick_support_btn)
        pick_buttons.addWidget(self.pick_origin_btn)
        pick_buttons.addWidget(self.pick_h_btn)
        pick_layout.addLayout(pick_buttons)
        read_btn = self.QtWidgets.QPushButton("Read current selection")
        read_btn.clicked.connect(self.read_selection)
        pick_layout.addWidget(read_btn)
        layout.addWidget(pick_group)

        options = self.QtWidgets.QGroupBox("Orientation")
        option_layout = self.QtWidgets.QVBoxLayout(options)
        self.reverse_h = self.QtWidgets.QCheckBox("Reverse H direction")
        self.reverse_v = self.QtWidgets.QCheckBox("Reverse V direction")
        self.swap_hv = self.QtWidgets.QCheckBox("Swap H and V")
        for checkbox in (self.reverse_h, self.reverse_v, self.swap_hv):
            try:
                checkbox.stateChanged.connect(lambda _state: self.update_preview())
            except Exception:
                pass
        option_layout.addWidget(self.reverse_h)
        option_layout.addWidget(self.reverse_v)
        option_layout.addWidget(self.swap_hv)
        layout.addWidget(options)

        hint = self.QtWidgets.QLabel(
            "Tip: you can simply select geometry: planar face/plane = Support, vertex/point = Origin, edge/line = H direction. "
            "Use Pick support / Pick origin / Pick H direction only when you want to force the next selection type."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = self.QtWidgets.QDialogButtonBox(
            self.QtWidgets.QDialogButtonBox.Ok | self.QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        try:
            self.dialog.finished.connect(lambda _code: self.cleanup())
        except Exception:
            pass

    def arm_pick(self, mode):
        self.pick_mode = mode
        labels = {
            "support": "Now select a planar face/plane for the sketch support.",
            "origin": "Now select a vertex/point for the sketch origin.",
            "h": "Now select an edge/line for the horizontal H direction.",
        }
        self.pick_status.setText(labels.get(mode, "Select geometry."))

    def _selection_event_shape(self, doc_name, obj_name, sub_name):
        try:
            doc = FreeCAD.getDocument(doc_name)
            obj = doc.getObject(obj_name)
            if obj is None:
                return None, "", None
            if sub_name:
                shape = obj.getSubObject(sub_name)
            elif hasattr(obj, "Shape"):
                shape = obj.Shape
            else:
                shape = None
            return obj, sub_name or "", shape
        except Exception:
            return None, "", None

    def _apply_auto_pick(self, owner, path, shape):
        shape_type = getattr(shape, "ShapeType", None)
        if shape_type == "Face":
            normal = _plane_normal(shape)
            if normal is not None:
                self.face_owner = owner
                self.face_path = path
                self.plane_normal = normal
                self.pick_status.setText("Support selected automatically. Select point/origin or H line next.")
                self.update_labels()
                self.update_preview()
                return True
        if shape_type == "Vertex":
            point = _point_from_shape(shape)
            if point is not None:
                self.origin = point
                self.pick_status.setText("Origin selected automatically. Select support plane or H line next.")
                self.update_labels()
                self.update_preview()
                return True
        if shape_type == "Edge":
            direction = _edge_direction(shape)
            if direction is not None:
                self.line_direction = direction
                self.v_direction = None
                self.pick_status.setText("H direction selected automatically. Press OK or continue selecting.")
                self.update_labels()
                self.update_preview()
                return True
        point = _point_from_shape(shape)
        if point is not None:
            self.origin = point
            self.pick_status.setText("Origin selected automatically. Select support plane or H line next.")
            self.update_labels()
            self.update_preview()
            return True
        self.pick_status.setText("Selection not recognized as plane, point, or line.")
        return False

    def _apply_pick(self, owner, path, shape):
        if self.pick_mode == "support":
            normal = _plane_normal(shape)
            if normal is None:
                self.pick_status.setText("That is not a planar face/plane. Pick support again.")
                return
            self.face_owner = owner
            self.face_path = path
            self.plane_normal = normal
            self.pick_status.setText("Support selected. Now pick origin or H direction.")
        elif self.pick_mode == "origin":
            point = _point_from_shape(shape)
            if point is None:
                self.pick_status.setText("That is not a point/vertex. Pick origin again.")
                return
            self.origin = point
            self.pick_status.setText("Origin selected. Now pick support or H direction.")
        elif self.pick_mode == "h":
            if getattr(shape, "ShapeType", None) != "Edge":
                self.pick_status.setText("That is not an edge/line. Pick H direction again.")
                return
            direction = _edge_direction(shape)
            if direction is None:
                self.pick_status.setText("Could not read edge direction. Pick H direction again.")
                return
            self.line_direction = direction
            self.v_direction = None
            self.pick_status.setText("H direction selected. Press OK or continue picking.")
        else:
            return
        self.pick_mode = None
        self.update_labels()
        self.update_preview()

    def addSelection(self, doc, obj, sub, pnt):
        owner, path, shape = self._selection_event_shape(doc, obj, sub)
        if shape is None:
            return
        if self.pick_mode is None:
            self._apply_auto_pick(owner, path, shape)
        else:
            self._apply_pick(owner, path, shape)

    def _clear_preview(self):
        for obj in list(getattr(self, "preview_objects", [])):
            try:
                if obj.Document is not None:
                    obj.Document.removeObject(obj.Name)
            except Exception:
                pass
        self.preview_objects = []

    def update_preview(self):
        self._clear_preview()
        if self.origin is None or self.line_direction is None or self.plane_normal is None:
            return
        try:
            doc = _active_doc()
            # Reuse the same math as final creation, but create no sketch.
            z_axis = FreeCAD.Vector(self.plane_normal)
            if z_axis.Length <= 1e-9:
                return
            z_axis.normalize()
            x_axis = FreeCAD.Vector(self.line_direction)
            x_axis = x_axis - FreeCAD.Vector(z_axis).multiply(x_axis.dot(z_axis))
            if x_axis.Length <= 1e-9:
                return
            x_axis.normalize()
            if self.v_direction is None:
                y_axis = z_axis.cross(x_axis)
            else:
                y_axis = FreeCAD.Vector(self.v_direction)
                y_axis = y_axis - FreeCAD.Vector(z_axis).multiply(y_axis.dot(z_axis))
                y_axis = y_axis - FreeCAD.Vector(x_axis).multiply(y_axis.dot(x_axis))
            if y_axis.Length <= 1e-9:
                return
            y_axis.normalize()
            x_axis = y_axis.cross(z_axis)
            if x_axis.dot(self.line_direction) < 0:
                x_axis = x_axis.multiply(-1.0)
                y_axis = y_axis.multiply(-1.0)
            x_axis.normalize()
            if self.reverse_h.isChecked():
                x_axis = x_axis.multiply(-1.0)
            if self.reverse_v.isChecked():
                y_axis = y_axis.multiply(-1.0)
            if self.swap_hv.isChecked():
                x_axis, y_axis = y_axis, x_axis

            length = max(float(getattr(self, "preview_length", 20.0)), 1.0)
            h_obj = doc.addObject("Part::Feature", "PositionedSketchPreview_H")
            h_obj.Label = "H axis preview"
            h_obj.Shape = Part.makeLine(self.origin, self.origin + x_axis.multiply(length))
            v_obj = doc.addObject("Part::Feature", "PositionedSketchPreview_V")
            v_obj.Label = "V axis preview"
            v_obj.Shape = Part.makeLine(self.origin, self.origin + y_axis.multiply(length))
            try:
                h_obj.ViewObject.LineColor = (1.0, 0.0, 0.0)
                h_obj.ViewObject.LineWidth = 4.0
                v_obj.ViewObject.LineColor = (0.0, 0.8, 0.0)
                v_obj.ViewObject.LineWidth = 4.0
            except Exception:
                pass
            self.preview_objects = [h_obj, v_obj]
            doc.recompute()
            self.pick_status.setText("Preview shown: red = H, green = V. Press OK or continue picking.")
        except Exception as exc:
            try:
                self.pick_status.setText("Could not show H/V preview: {}".format(exc))
            except Exception:
                pass

    def cleanup(self):
        self._clear_preview()
        try:
            FreeCADGui.Selection.removeObserver(self)
        except Exception:
            pass

    def reject(self):
        self.cleanup()
        self.dialog.reject()

    def show(self):
        self.dialog.show()
        try:
            self.dialog.raise_()
            self.dialog.activateWindow()
        except Exception:
            pass

    def update_labels(self):
        if self.plane_normal is None:
            self.support_label.setText("not selected")
        elif self.face_owner is not None:
            self.support_label.setText(_object_label(self.face_owner, self.face_path))
        else:
            self.support_label.setText("current sketch plane")
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

    def read_selection(self):
        face_owner, face_path, origin, line_direction, plane_normal = _first_positioned_sketch_inputs()
        if plane_normal is not None:
            self.face_owner = face_owner
            self.face_path = face_path
            self.plane_normal = plane_normal
        if origin is not None:
            self.origin = origin
        if line_direction is not None:
            self.line_direction = line_direction
            self.v_direction = None
        self.update_labels()
        self.update_preview()

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
                existing_sketch=self.sketch,
                v_direction=self.v_direction,
            )
        except Exception as exc:
            self.QtWidgets.QMessageBox.critical(self.dialog, "Positioned Sketch", str(exc))
            return
        FreeCAD.ActiveDocument.recompute()
        try:
            FreeCADGui.ActiveDocument.setEdit(sketch.Name)
        except Exception:
            pass
        _message(("Updated" if self.sketch is not None else "Created") + " positioned sketch from popup.")
        self.cleanup()
        self.dialog.accept()

    def exec_(self):
        self.show()
        return 0


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
                global _SURFACELAB_POSITIONED_SKETCH_DIALOG
                if _SURFACELAB_POSITIONED_SKETCH_DIALOG is not None:
                    try:
                        _SURFACELAB_POSITIONED_SKETCH_DIALOG.cleanup()
                    except Exception:
                        pass
                _SURFACELAB_POSITIONED_SKETCH_DIALOG = _PositionedSketchDialog(self, _selected_positioned_sketch())
                _SURFACELAB_POSITIONED_SKETCH_DIALOG.show()
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
            'Pixmap': POSITIONED_SKETCH_ICON,
            'MenuText': self.title,
            'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(self.doc, self.usage),
        }


def _is_sketch(obj):
    return getattr(obj, "TypeId", "") == "Sketcher::SketchObject"


def _is_positioned_sketch(obj):
    return _is_sketch(obj) and (getattr(obj, "Name", "").startswith("PositionedSketch") or hasattr(obj, "SurfaceLabPositioning"))


def _is_linked_positioned_sketch(obj):
    if not _is_sketch(obj):
        return False
    try:
        return bool(getattr(obj, "SurfaceLabLinkedPositionedSketch", False)) and getattr(obj, "SourceSketch", None) is not None
    except Exception:
        return False


def _selected_linked_positioned_sketch():
    for obj in FreeCADGui.Selection.getSelection():
        if _is_linked_positioned_sketch(obj):
            return obj
    return None


def _selected_positioned_sketch_excluding(excluded):
    for obj in FreeCADGui.Selection.getSelection():
        if obj is excluded:
            continue
        if _is_positioned_sketch(obj) and not _is_linked_positioned_sketch(obj):
            return obj
    return None


def _object_display_name(obj):
    if obj is None:
        return "not linked"
    return "{} ({})".format(getattr(obj, "Label", getattr(obj, "Name", "?")), getattr(obj, "Name", "?"))


def _qt_modules():
    try:
        from PySide import QtCore, QtGui
        return QtCore, QtGui, QtGui
    except Exception:
        from PySide2 import QtCore, QtWidgets
        return QtCore, QtWidgets, QtWidgets


def _selected_body_and_source_sketch():
    source = None
    body = None
    for sel in FreeCADGui.Selection.getSelectionEx('', 0):
        obj = getattr(sel, "Object", None)
        if obj is None:
            continue
        if _is_positioned_sketch(obj) and source is None:
            source = obj
        elif getattr(obj, "TypeId", "") == "PartDesign::Body" and body is None:
            body = obj
    if body is None:
        try:
            active = FreeCADGui.ActiveDocument.ActiveView.getActiveObject("pdbody")
            if getattr(active, "TypeId", "") == "PartDesign::Body":
                body = active
        except Exception:
            pass
    return source, body


def _add_link_properties(target, source):
    try:
        if not hasattr(target, "SourceSketch"):
            target.addProperty("App::PropertyLink", "SourceSketch", "SurfaceLab", "Master positioned sketch driving this linked copy")
        target.SourceSketch = source
    except Exception:
        pass
    try:
        if not hasattr(target, "SurfaceLabLinkedPositionedSketch"):
            target.addProperty("App::PropertyBool", "SurfaceLabLinkedPositionedSketch", "SurfaceLab", "True if this sketch is synchronized from SourceSketch")
        target.SurfaceLabLinkedPositionedSketch = True
    except Exception:
        pass


def _copy_sketch_contents(source, target):
    if source is None or target is None or source == target:
        return False
    try:
        target.deleteAllConstraints()
    except Exception:
        try:
            for index in reversed(range(len(target.Constraints))):
                target.delConstraint(index)
        except Exception:
            pass
    try:
        target.deleteAllGeometry()
    except Exception:
        try:
            for index in reversed(range(len(target.Geometry))):
                target.delGeometry(index)
        except Exception:
            pass

    for index, geometry in enumerate(source.Geometry):
        try:
            copied = geometry.copy()
        except Exception:
            copied = geometry
        construction = False
        try:
            construction = bool(source.getConstruction(index))
        except Exception:
            pass
        target.addGeometry(copied, construction)

    for constraint in source.Constraints:
        try:
            target.addConstraint(constraint)
        except Exception as exc:
            FreeCAD.Console.PrintWarning("SurfaceLab: skipped linked sketch constraint {}: {}\n".format(constraint, exc))

    target.Placement = source.Placement
    try:
        source_label = getattr(source, "Label", getattr(source, "Name", "PositionedSketch"))
        target.Label = "Linked " + source_label
    except Exception:
        pass
    for name in ("SurfaceLabHDirection", "SurfaceLabVDirection", "SurfaceLabNormal", "SurfaceLabPositioning"):
        try:
            if hasattr(source, name):
                if not hasattr(target, name):
                    value = getattr(source, name)
                    if name == "SurfaceLabPositioning":
                        target.addProperty("App::PropertyString", name, "SurfaceLab", "CATIA-like positioned sketch reference summary")
                    else:
                        target.addProperty("App::PropertyVector", name, "SurfaceLab", "Positioned sketch axis copied from source")
                setattr(target, name, getattr(source, name))
        except Exception:
            pass
    return True


def _linked_positioned_sketches(doc=None, source=None):
    doc = doc or FreeCAD.ActiveDocument
    if doc is None:
        return []
    result = []
    for obj in doc.Objects:
        if not _is_sketch(obj):
            continue
        try:
            if _is_linked_positioned_sketch(obj):
                if source is None or obj.SourceSketch == source:
                    result.append(obj)
        except Exception:
            pass
    return result


def _sync_linked_positioned_sketches(doc=None, source=None):
    count = 0
    for target in _linked_positioned_sketches(doc, source):
        src = getattr(target, "SourceSketch", None)
        if src is not None and _copy_sketch_contents(src, target):
            count += 1
    return count


class _SurfaceLabLinkedSketchObserver:
    syncing = False

    def _maybe_sync(self, obj):
        if self.syncing or not _is_positioned_sketch(obj):
            return
        try:
            linked = _linked_positioned_sketches(obj.Document, obj)
            if not linked:
                return
            self.syncing = True
            _sync_linked_positioned_sketches(obj.Document, obj)
        except Exception as exc:
            FreeCAD.Console.PrintWarning("SurfaceLab linked sketch auto-sync skipped: {}\n".format(exc))
        finally:
            self.syncing = False

    def slotChangedObject(self, obj, prop):
        if prop in ("Geometry", "Constraints", "Placement", "Support", "MapMode", "AttachmentOffset"):
            self._maybe_sync(obj)

    def slotRecomputedObject(self, obj):
        self._maybe_sync(obj)


_SURFACELAB_LINKED_SKETCH_OBSERVER = None


def _install_linked_sketch_observer():
    global _SURFACELAB_LINKED_SKETCH_OBSERVER
    if _SURFACELAB_LINKED_SKETCH_OBSERVER is None:
        try:
            _SURFACELAB_LINKED_SKETCH_OBSERVER = _SurfaceLabLinkedSketchObserver()
            FreeCAD.addDocumentObserver(_SURFACELAB_LINKED_SKETCH_OBSERVER)
        except Exception:
            _SURFACELAB_LINKED_SKETCH_OBSERVER = None


class _LinkedPositionedSketchDialog:
    """Small manager for a linked positioned sketch."""

    def __init__(self, linked):
        self.linked = linked
        self.QtCore, self.QtGui, self.QtWidgets = _qt_modules()
        self._build()
        self.update_labels()

    def _build(self):
        self.dialog = self.QtWidgets.QDialog()
        self.dialog.setWindowTitle("Linked Positioned Sketch")
        try:
            self.dialog.setModal(False)
        except Exception:
            pass
        layout = self.QtWidgets.QVBoxLayout(self.dialog)

        info = self.QtWidgets.QLabel(
            "This sketch is a Body-local copy driven by a master PositionedSketch. "
            "Edit the master; then sync/recompute to update this linked sketch."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        form = self.QtWidgets.QFormLayout()
        self.linked_label = self.QtWidgets.QLabel("")
        self.source_label = self.QtWidgets.QLabel("")
        self.status_label = self.QtWidgets.QLabel("")
        self.status_label.setWordWrap(True)
        form.addRow("Linked sketch", self.linked_label)
        form.addRow("Master source", self.source_label)
        form.addRow("Status", self.status_label)
        layout.addLayout(form)

        buttons_layout = self.QtWidgets.QVBoxLayout()
        self.select_source_btn = self.QtWidgets.QPushButton("Select master source")
        self.select_linked_btn = self.QtWidgets.QPushButton("Select this linked sketch")
        self.sync_btn = self.QtWidgets.QPushButton("Sync now from master")
        self.relink_btn = self.QtWidgets.QPushButton("Relink to currently selected master")
        self.select_source_btn.clicked.connect(self.select_source)
        self.select_linked_btn.clicked.connect(self.select_linked)
        self.sync_btn.clicked.connect(self.sync_now)
        self.relink_btn.clicked.connect(self.relink_to_selection)
        for button in (self.select_source_btn, self.select_linked_btn, self.sync_btn, self.relink_btn):
            buttons_layout.addWidget(button)
        layout.addLayout(buttons_layout)

        hint = self.QtWidgets.QLabel(
            "Relink: select another normal PositionedSketch in the tree/3D view, then press Relink. "
            "Do not manually edit linked copies; edit the master source instead."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        close_buttons = self.QtWidgets.QDialogButtonBox(self.QtWidgets.QDialogButtonBox.Close)
        close_buttons.rejected.connect(self.dialog.reject)
        try:
            close_buttons.button(self.QtWidgets.QDialogButtonBox.Close).clicked.connect(self.dialog.reject)
        except Exception:
            pass
        layout.addWidget(close_buttons)

    def update_labels(self, status=""):
        source = getattr(self.linked, "SourceSketch", None)
        self.linked_label.setText(_object_display_name(self.linked))
        self.source_label.setText(_object_display_name(source))
        if not status:
            if source is None:
                status = "No source stored. Select a master PositionedSketch and press Relink."
            else:
                status = "Linked to {}.".format(getattr(source, "Label", source.Name))
        self.status_label.setText(status)

    def select_source(self):
        source = getattr(self.linked, "SourceSketch", None)
        if source is None:
            self.update_labels("No source sketch stored on this linked sketch.")
            return
        try:
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(source)
            self.update_labels("Selected master source: {}.".format(source.Label))
        except Exception as exc:
            self.update_labels("Could not select source: {}".format(exc))

    def select_linked(self):
        try:
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(self.linked)
            self.update_labels("Selected linked sketch: {}.".format(self.linked.Label))
        except Exception as exc:
            self.update_labels("Could not select linked sketch: {}".format(exc))

    def sync_now(self):
        source = getattr(self.linked, "SourceSketch", None)
        if source is None:
            self.update_labels("No source to sync from.")
            return
        try:
            if _copy_sketch_contents(source, self.linked):
                if self.linked.Document is not None:
                    self.linked.Document.recompute()
                self.update_labels("Synced from {}.".format(source.Label))
            else:
                self.update_labels("Nothing synced.")
        except Exception as exc:
            self.update_labels("Sync failed: {}".format(exc))

    def relink_to_selection(self):
        source = _selected_positioned_sketch_excluding(self.linked)
        if source is None:
            self.update_labels("Select a normal/master PositionedSketch first, then press Relink.")
            return
        try:
            _add_link_properties(self.linked, source)
            _copy_sketch_contents(source, self.linked)
            if self.linked.Document is not None:
                self.linked.Document.recompute()
            self.update_labels("Relinked and synced from {}.".format(source.Label))
        except Exception as exc:
            self.update_labels("Relink failed: {}".format(exc))

    def show(self):
        self.dialog.show()
        try:
            self.dialog.raise_()
            self.dialog.activateWindow()
        except Exception:
            pass


_SURFACELAB_LINKED_SKETCH_DIALOG = None


class SurfaceLabManageLinkedPositionedSketchCommand:
    title = "SurfaceLab Manage Linked Positioned Sketch"
    doc = "Show and edit the master SourceSketch link of a linked positioned sketch."
    usage = "Select a LinkedPositionedSketch, then run the command."

    def Activated(self):
        linked = _selected_linked_positioned_sketch()
        if linked is None:
            _error(self.title, self.usage)
            return
        if getattr(FreeCAD, "GuiUp", False):
            try:
                global _SURFACELAB_LINKED_SKETCH_DIALOG
                _SURFACELAB_LINKED_SKETCH_DIALOG = _LinkedPositionedSketchDialog(linked)
                _SURFACELAB_LINKED_SKETCH_DIALOG.show()
                return
            except Exception as exc:
                FreeCAD.Console.PrintWarning("SurfaceLab linked sketch dialog unavailable: {}\n".format(exc))
        source = getattr(linked, "SourceSketch", None)
        _message("{} is linked to {}.".format(linked.Label, _object_display_name(source)))

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': MANAGE_LINKED_SKETCH_ICON, 'MenuText': self.title, 'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(self.doc, self.usage)}


class SurfaceLabCreateLinkedPositionedSketchCommand:
    title = "SurfaceLab Linked Positioned Sketch"
    doc = "Create a Body-local sketch linked to a master positioned sketch."
    usage = "Select a master PositionedSketch and a target Body, or activate a Body and select the master sketch, then run the command."

    def Activated(self):
        linked = _selected_linked_positioned_sketch()
        if linked is not None:
            SurfaceLabManageLinkedPositionedSketchCommand().Activated()
            return
        doc = _active_doc()
        source, body = _selected_body_and_source_sketch()
        if source is None:
            _error(self.title, self.usage)
            return
        try:
            linked = doc.addObject("Sketcher::SketchObject", "LinkedPositionedSketch")
            linked.Label = "Linked " + getattr(source, "Label", source.Name)
            _copy_sketch_contents(source, linked)
            _add_link_properties(linked, source)
            if body is not None:
                try:
                    body.addObject(linked)
                except Exception as exc:
                    FreeCAD.Console.PrintWarning("SurfaceLab: could not move linked sketch into Body: {}\n".format(exc))
            doc.recompute()
            _install_linked_sketch_observer()
            _message("Created linked positioned sketch{} from {}.".format(" in " + body.Label if body is not None else "", source.Label))
        except Exception as exc:
            FreeCAD.Console.PrintError("SurfaceLab linked positioned sketch failed: {}\n".format(exc))

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': LINKED_POSITIONED_SKETCH_ICON, 'MenuText': self.title, 'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(self.doc, self.usage)}


class SurfaceLabSyncLinkedPositionedSketchesCommand:
    title = "SurfaceLab Sync Linked Positioned Sketches"
    doc = "Synchronize all linked positioned sketches from their master SourceSketch."
    usage = "Run after editing a master sketch if linked copies did not update automatically."

    def Activated(self):
        count = _sync_linked_positioned_sketches(FreeCAD.ActiveDocument)
        if FreeCAD.ActiveDocument is not None:
            FreeCAD.ActiveDocument.recompute()
        _message("Synchronized {} linked positioned sketch(es).".format(count))

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': SYNC_LINKED_SKETCH_ICON, 'MenuText': self.title, 'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(self.doc, self.usage)}


_SKETCH_VISIBLE_SPACE_STATES = {}


def _active_or_selected_sketch():
    try:
        in_edit = FreeCADGui.ActiveDocument.getInEdit()
        if _is_sketch(in_edit):
            return in_edit
    except Exception:
        pass
    for obj in FreeCADGui.Selection.getSelection():
        if _is_sketch(obj):
            return obj
    return None


def _view_object(obj):
    try:
        return obj.ViewObject
    except Exception:
        return None


def _external_shape(owner, subname):
    try:
        if owner is not None and subname:
            shape = owner.getSubObject(subname)
            if shape is not None:
                return shape
    except Exception:
        pass
    try:
        if owner is not None and hasattr(owner, "Shape"):
            return owner.Shape
    except Exception:
        pass
    return None


def _geometry_from_edge_in_sketch(edge, sketch):
    try:
        curve = edge.Curve.copy()
    except Exception:
        return None
    try:
        first = edge.FirstParameter
        last = edge.LastParameter
        if hasattr(curve, "trim"):
            curve = curve.trim(first, last)
    except Exception:
        pass
    try:
        curve.transform(sketch.Placement.inverse().toMatrix())
    except Exception:
        pass
    return curve


def _geometry_from_vertex_in_sketch(vertex, sketch):
    try:
        point = sketch.Placement.inverse().multVec(vertex.Point)
        return Part.Point(point)
    except Exception:
        return None


def _isolate_sketch_external_geometry(sketch, delete_external=True):
    if sketch is None or not _is_sketch(sketch):
        return 0
    added = 0
    externals = list(getattr(sketch, "ExternalGeometry", []) or [])
    for owner, subnames in externals:
        for subname in subnames:
            shape = _external_shape(owner, subname)
            if shape is None:
                continue
            shape_type = getattr(shape, "ShapeType", None)
            geometries = []
            if shape_type == "Edge":
                geom = _geometry_from_edge_in_sketch(shape, sketch)
                if geom is not None:
                    geometries.append(geom)
            elif shape_type == "Vertex":
                geom = _geometry_from_vertex_in_sketch(shape, sketch)
                if geom is not None:
                    geometries.append(geom)
            else:
                for edge in getattr(shape, "Edges", []) or []:
                    geom = _geometry_from_edge_in_sketch(edge, sketch)
                    if geom is not None:
                        geometries.append(geom)
                for vertex in getattr(shape, "Vertexes", []) or []:
                    geom = _geometry_from_vertex_in_sketch(vertex, sketch)
                    if geom is not None:
                        geometries.append(geom)
            for geom in geometries:
                try:
                    sketch.addGeometry(geom, False)
                    added += 1
                except Exception as exc:
                    FreeCAD.Console.PrintWarning("SurfaceLab: could not isolate sketch geometry {}: {}\n".format(subname, exc))
    if delete_external:
        try:
            for index in reversed(range(len(externals))):
                sketch.delExternal(index)
        except Exception as exc:
            FreeCAD.Console.PrintWarning("SurfaceLab: isolated geometry but could not remove all external links: {}\n".format(exc))
    return added


class SurfaceLabSwitchVisibleSpaceCommand:
    title = "SurfaceLab Switch Visible Space"
    doc = "Toggle CATIA-like sketch visible space: hide/show the 3D model around the active sketch."
    usage = "Edit or select a sketch, then run the command. Run again to restore previous visibility."

    def Activated(self):
        sketch = _active_or_selected_sketch()
        if sketch is None:
            _error(self.title, self.usage)
            return
        doc = sketch.Document or FreeCAD.ActiveDocument
        key = (doc.Name if doc else "", sketch.Name)
        if key in _SKETCH_VISIBLE_SPACE_STATES:
            states = _SKETCH_VISIBLE_SPACE_STATES.pop(key)
            for name, visible in states.items():
                obj = doc.getObject(name) if doc is not None else None
                vo = _view_object(obj) if obj is not None else None
                if vo is not None:
                    try:
                        vo.Visibility = visible
                    except Exception:
                        pass
            _message("Restored visible space around {}.".format(sketch.Label))
            return
        states = {}
        hidden = 0
        for obj in list(getattr(doc, "Objects", []) or []):
            if obj == sketch:
                continue
            vo = _view_object(obj)
            if vo is None:
                continue
            try:
                states[obj.Name] = bool(vo.Visibility)
                if vo.Visibility:
                    vo.Visibility = False
                    hidden += 1
            except Exception:
                pass
        _SKETCH_VISIBLE_SPACE_STATES[key] = states
        try:
            sketch.ViewObject.Visibility = True
        except Exception:
            pass
        _message("Switched visible space for {}; hidden {} object(s). Run again to restore.".format(sketch.Label, hidden))

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': SKETCH_VISIBLE_SPACE_ICON, 'MenuText': self.title, 'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(self.doc, self.usage)}


class SurfaceLabIsolateSketchGeometryCommand:
    title = "SurfaceLab Isolate Sketch Projections"
    doc = "Copy projected/external sketch geometry into the sketch as normal editable geometry, then remove the external links."
    usage = "Edit or select a sketch containing projected external geometry, then run the command."

    def Activated(self):
        sketch = _active_or_selected_sketch()
        if sketch is None:
            _error(self.title, self.usage)
            return
        try:
            added = _isolate_sketch_external_geometry(sketch, delete_external=True)
            if sketch.Document is not None:
                sketch.Document.recompute()
            _message("Isolated {} projected geometries in {}.".format(added, sketch.Label))
        except Exception as exc:
            FreeCAD.Console.PrintError("SurfaceLab isolate sketch projections failed: {}\n".format(exc))

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': SKETCH_ISOLATE_ICON, 'MenuText': self.title, 'ToolTip': "{}<br><br><b>Usage :</b><br>{}".format(self.doc, self.usage)}


FreeCADGui.addCommand('SurfaceLab_BSplineFromPoints', SurfaceLabBSplineFromPointsCommand())
FreeCADGui.addCommand('SurfaceLab_LoftSurface', SurfaceLabLoftSurfaceCommand())
FreeCADGui.addCommand('SurfaceLab_BoundarySurface', SurfaceLabBoundarySurfaceCommand())
FreeCADGui.addCommand('SurfaceLab_PositionedSketch', SurfaceLabPositionedSketchCommand())
FreeCADGui.addCommand('SurfaceLab_CreateLinkedPositionedSketch', SurfaceLabCreateLinkedPositionedSketchCommand())
FreeCADGui.addCommand('SurfaceLab_ManageLinkedPositionedSketch', SurfaceLabManageLinkedPositionedSketchCommand())
FreeCADGui.addCommand('SurfaceLab_SyncLinkedPositionedSketches', SurfaceLabSyncLinkedPositionedSketchesCommand())
FreeCADGui.addCommand('SurfaceLab_SwitchVisibleSpace', SurfaceLabSwitchVisibleSpaceCommand())
FreeCADGui.addCommand('SurfaceLab_IsolateSketchGeometry', SurfaceLabIsolateSketchGeometryCommand())
_install_linked_sketch_observer()

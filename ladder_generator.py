"""
DayZ Geometry Maker - Ladder Generator (Type 1 - straight ladder)
=================================================================
Coordinate system:  Z = up,  X = width,  Y = depth.

DayZ standard reference values (checkmark in UI if matched, warning if not):
  GROUND_OFFSET_STD  = 0.340 m   (first rung from ground)
  RUNG_SPACING_STD   = 0.320 m   (rung centre-to-centre)
  TUBE_DIAMETER_STD  = 0.042 m   (42 mm diameter)
  TOP_EXT_STD        = 0.700 m   (stringer extension above last rung)
  VALID_WIDTHS_MM    = 440 or 480 mm (centre-to-centre)

All values are editable. Checkmark = DayZ standard, exclamation = deviation.
"""

import bpy
import bmesh
import math
from mathutils import Vector


# ---------------------------------------------------------------------------
#  DayZ standard reference values
# ---------------------------------------------------------------------------

GROUND_OFFSET_STD = 0.340
RUNG_SPACING_STD  = 0.320
TUBE_DIAMETER_STD = 0.042   # displayed and stored as diameter
TOP_EXT_STD       = 0.700
VALID_WIDTHS_MM   = (440, 480)

_TOL = 1e-4


def _std_icon(value, reference):
    return 'CHECKMARK' if abs(value - reference) < _TOL else 'ERROR'


# ---------------------------------------------------------------------------
#  Geometry primitive — closed manifold tube
# ---------------------------------------------------------------------------

def _make_tube(bm, p0, p1, radius, segs):
    """
    Build a closed (manifold) cylinder from p0 to p1 with the given radius.
    Geometry is added directly into bm.
    """
    p0 = Vector(p0)
    p1 = Vector(p1)
    axis = p1 - p0
    if axis.length < 1e-6:
        return

    axis_n = axis.normalized()
    ref = Vector((0.0, 0.0, 1.0))
    if abs(axis_n.dot(ref)) > 0.99:
        ref = Vector((1.0, 0.0, 0.0))
    tang = axis_n.cross(ref).normalized()
    btan = axis_n.cross(tang).normalized()

    def ring(c):
        verts = []
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            verts.append(bm.verts.new(
                c + tang * math.cos(a) * radius + btan * math.sin(a) * radius))
        return verts

    ra = ring(p0)
    rb = ring(p1)

    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new([ra[i], ra[j], rb[j], rb[i]])

    ca = bm.verts.new(p0)
    cb = bm.verts.new(p1)
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new([ca, ra[j], ra[i]])
        bm.faces.new([cb, rb[i], rb[j]])


# ---------------------------------------------------------------------------
#  Type 1 ladder builder
# ---------------------------------------------------------------------------

def build_ladder_type1(params):
    """
    Build a Type 1 (straight) ladder bmesh.
    Returns (bm, rung_count, total_height).
    Caller must call bm.free() after use.

    Z = up. Ladder base at Z=0, extends upward.
    Stringers run along Z. Rungs are horizontal along X.

    params:
        width           float  - stringer centre-to-centre (m)
        tube_diameter   float  - diameter of all tubes (m)
        rung_count      int    - number of rungs
        rung_spacing    float  - rung centre-to-centre spacing (m)
        ground_offset   float  - first rung height from base (m)
        top_extension   float  - stringer length above last rung (m)
        resolution      int    - tube cross-section segment count
    """
    bm = bmesh.new()

    segs   = max(4, int(params['resolution']))
    r      = float(params['tube_diameter']) / 2.0
    width  = float(params['width'])
    sx     = width / 2.0

    rung_count    = max(1, int(params['rung_count']))
    rung_spacing  = float(params['rung_spacing'])
    ground_offset = float(params['ground_offset'])
    top_ext       = float(params['top_extension'])

    last_rung_z  = ground_offset + (rung_count - 1) * rung_spacing
    total_height = last_rung_z + top_ext

    # Stringers — vertical along Z
    _make_tube(bm, (-sx, 0.0, 0.0), (-sx, 0.0, total_height), r, segs)
    _make_tube(bm,  (sx, 0.0, 0.0),  (sx, 0.0, total_height), r, segs)

    # Rungs — horizontal along X
    for i in range(rung_count):
        z = ground_offset + i * rung_spacing
        _make_tube(bm, (-sx, 0.0, z), (sx, 0.0, z), r, segs)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=5e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    return bm, rung_count, total_height



def _count_scene_ladders():
    """Count DZ_Ladder objects in the current scene."""
    return sum(1 for o in bpy.data.objects
               if o.get('dgm_ladder') is True
               and o.users_scene)

def _is_active_ladder(obj):
    """True if obj is a tracked ladder object."""
    return (obj is not None
            and obj.type == 'MESH'
            and obj.get('dgm_ladder') is True)

# ---------------------------------------------------------------------------
#  Main operator — Type 1
# ---------------------------------------------------------------------------

class DGM_OT_ladder_type1(bpy.types.Operator):
    bl_idname      = "dgm.ladder_type1"
    bl_label       = "Add Ladder"
    bl_description = "DayZ ladder with correct animation dimensions (440/480 mm wide, 320 mm rung spacing, 42 mm tube diameter)."
    bl_options = {'REGISTER', 'UNDO'}

    width: bpy.props.FloatProperty(
        name="Width",
        description=(
            "Stringer centre-to-centre distance.\n"
            "DayZ standard: 440 mm or 480 mm.\n"
            "Other values will trigger a warning icon."
        ),
        default=0.440, min=0.100, max=2.000, step=1,
        unit='LENGTH',
    )
    tube_diameter: bpy.props.FloatProperty(
        name="Tube Diameter",
        description=(
            "Outer diameter of all tubes (stringers and rungs).\n"
            "DayZ standard: 42 mm (radius 21 mm).\n"
            "Changing this affects collision thickness."
        ),
        default=TUBE_DIAMETER_STD, min=0.002, max=0.400, step=0.1,
        unit='LENGTH',
    )
    rung_count: bpy.props.IntProperty(
        name="Rung Count",
        description=(
            "Total number of rungs (steps).\n"
            "Total ladder height is calculated automatically:\n"
            "  height = first_rung + (count - 1) x spacing + top_extension"
        ),
        default=16, min=1, max=120,
    )
    rung_spacing: bpy.props.FloatProperty(
        name="Rung Spacing",
        description=(
            "Centre-to-centre distance between rungs.\n"
            "DayZ standard: 320 mm.\n"
            "Must match the animation controller spacing for correct climbing."
        ),
        default=RUNG_SPACING_STD, min=0.050, max=1.000, step=1,
        unit='LENGTH',
    )
    ground_offset: bpy.props.FloatProperty(
        name="First Rung Height",
        description=(
            "Height of the first rung above the ladder base (Z=0).\n"
            "DayZ standard: 340 mm minimum.\n"
            "Too low and the player animation will clip the ground."
        ),
        default=GROUND_OFFSET_STD, min=0.010, max=2.000, step=1,
        unit='LENGTH',
    )
    top_extension: bpy.props.FloatProperty(
        name="Top Extension",
        description=(
            "Stringer length extending above the last rung.\n"
            "DayZ standard: 700 mm.\n"
            "Used as grab rail when player reaches the top."
        ),
        default=TOP_EXT_STD, min=0.0, max=5.000, step=1,
        unit='LENGTH',
    )
    resolution: bpy.props.IntProperty(
        name="Tube Segments",
        description=(
            "Number of sides on each tube cross-section.\n"
            "4 = square, 8 = octagon, 16+ = visually round.\n"
            "Higher values produce smoother tubes but heavier meshes."
        ),
        default=10, min=4, max=24,
    )

    def _get_params(self):
        return dict(
            width=self.width,
            tube_diameter=self.tube_diameter,
            rung_count=self.rung_count,
            rung_spacing=self.rung_spacing,
            ground_offset=self.ground_offset,
            top_extension=self.top_extension,
            resolution=self.resolution,
        )

    def _rebuild(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH' or not obj.get('dgm_ladder'):
            return
        params = self._get_params()
        bm, rung_count, total_height = build_ladder_type1(params)
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
        obj['dgm_ladder_rungs']            = rung_count
        obj['dgm_ladder_height']           = round(total_height, 4)
        obj['dgm_ladder_expected_height']  = round(total_height, 4)
        obj['dgm_ladder_expected_width']   = round(params['width'] + params['tube_diameter'], 4)
        obj['dgm_ladder_expected_depth']   = round(params['tube_diameter'], 4)
        # Always persist params so panel integrity check works from first creation
        obj['dgm_p_width']         = params['width']
        obj['dgm_p_tube_diameter'] = params['tube_diameter']
        obj['dgm_p_rung_count']    = params['rung_count']
        obj['dgm_p_rung_spacing']  = params['rung_spacing']
        obj['dgm_p_ground_offset'] = params['ground_offset']
        obj['dgm_p_top_extension'] = params['top_extension']
        obj['dgm_p_resolution']    = params['resolution']

    @classmethod
    def poll(cls, context):
        return _count_scene_ladders() < 3

    def invoke(self, context, event):
        # Always create a brand new ladder object — never reuse existing
        # Name based on how many ladders already exist (1, 2, 3)
        ladder_num = _count_scene_ladders() + 1
        obj_name = "DZ_Ladder_{}".format(ladder_num)
        mesh = bpy.data.meshes.new(obj_name)
        obj  = bpy.data.objects.new(obj_name, mesh)
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        for o in bpy.context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        obj['dgm_ladder']      = True
        obj['dgm_ladder_type'] = 1
        self._rebuild(context)
        return context.window_manager.invoke_props_dialog(self, width=400)

    def check(self, context):
        self._rebuild(context)
        return True

    def draw(self, context):
        layout = self.layout
        params = self._get_params()

        box = layout.box()
        box.label(text="Straight Ladder", icon='MESH_CYLINDER')

        col = box.column(align=True)

        def prop_row(prop_name, std_value):
            row = col.row(align=True)
            row.prop(self, prop_name)
            row.label(text="", icon=_std_icon(getattr(self, prop_name), std_value))

        # Width — valid if 440 or 480 mm
        row_w = col.row(align=True)
        row_w.prop(self, 'width')
        w_icon = 'CHECKMARK' if round(self.width * 1000) in VALID_WIDTHS_MM else 'ERROR'
        row_w.label(text="", icon=w_icon)

        col.separator()
        prop_row('tube_diameter',  TUBE_DIAMETER_STD)
        col.separator()
        prop_row('rung_spacing',   RUNG_SPACING_STD)
        prop_row('ground_offset',  GROUND_OFFSET_STD)
        prop_row('top_extension',  TOP_EXT_STD)
        col.separator()
        col.prop(self, 'rung_count')

        # Info
        bm_info, rung_count, total_height = build_ladder_type1(params)
        bm_info.free()
        last_rung_z = params['ground_offset'] + (rung_count - 1) * params['rung_spacing']

        info_box = layout.box()
        icol = info_box.column(align=True)
        icol.label(text="Rungs: {}".format(rung_count), icon='INFO')
        icol.label(text="Total height:  {:.3f} m".format(total_height))
        icol.label(text="Last rung at:  {:.3f} m".format(last_rung_z))
        icol.label(text="Width:  {:.0f} mm".format(params['width'] * 1000))

        # Mesh quality — compact single row
        q_row = layout.row(align=True)
        q_row.label(text="Tube Segments:", icon='MESH_CIRCLE')
        q_row.prop(self, 'resolution', text="")

    def execute(self, context):
        self._rebuild(context)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Edit operator — edits the currently selected ladder object
# ---------------------------------------------------------------------------

class DGM_OT_ladder_edit(bpy.types.Operator):
    bl_idname      = "dgm.ladder_edit"
    bl_label       = "Edit Ladder"
    bl_description = "Edit parameters of the selected ladder object"
    bl_options     = {'REGISTER', 'UNDO'}

    # Same properties as Type 1 operator — identical descriptions for consistent tooltips
    width: bpy.props.FloatProperty(
        name="Width",
        description=(
            "Stringer centre-to-centre distance.\n"
            "DayZ standard: 440 mm or 480 mm.\n"
            "Other values will trigger a warning icon."
        ),
        default=0.440, min=0.100, max=2.000, step=1, unit='LENGTH')
    tube_diameter: bpy.props.FloatProperty(
        name="Tube Diameter",
        description=(
            "Outer diameter of all tubes (stringers and rungs).\n"
            "DayZ standard: 42 mm (radius 21 mm).\n"
            "Changing this affects collision thickness."
        ),
        default=TUBE_DIAMETER_STD, min=0.002, max=0.400, step=0.1, unit='LENGTH')
    rung_count: bpy.props.IntProperty(
        name="Rung Count",
        description=(
            "Total number of rungs (steps).\n"
            "Total ladder height is calculated automatically:\n"
            "  height = first_rung + (count - 1) x spacing + top_extension"
        ),
        default=16, min=1, max=120)
    rung_spacing: bpy.props.FloatProperty(
        name="Rung Spacing",
        description=(
            "Centre-to-centre distance between rungs.\n"
            "DayZ standard: 320 mm.\n"
            "Must match the animation controller spacing for correct climbing."
        ),
        default=RUNG_SPACING_STD, min=0.050, max=1.000, step=1, unit='LENGTH')
    ground_offset: bpy.props.FloatProperty(
        name="First Rung Height",
        description=(
            "Height of the first rung above the ladder base (Z=0).\n"
            "DayZ standard: 340 mm minimum.\n"
            "Too low and the player animation will clip the ground."
        ),
        default=GROUND_OFFSET_STD, min=0.010, max=2.000, step=1, unit='LENGTH')
    top_extension: bpy.props.FloatProperty(
        name="Top Extension",
        description=(
            "Stringer length extending above the last rung.\n"
            "DayZ standard: 700 mm.\n"
            "Used as grab rail when player reaches the top."
        ),
        default=TOP_EXT_STD, min=0.0, max=5.000, step=1, unit='LENGTH')
    resolution: bpy.props.IntProperty(
        name="Tube Segments",
        description=(
            "Number of sides on each tube cross-section.\n"
            "4 = square, 8 = octagon, 16+ = visually round.\n"
            "Higher values produce smoother tubes but heavier meshes."
        ),
        default=10, min=4, max=24)

    @classmethod
    def poll(cls, context):
        return _is_active_ladder(context.active_object)

    def _get_params(self):
        return dict(
            width=self.width,
            tube_diameter=self.tube_diameter,
            rung_count=self.rung_count,
            rung_spacing=self.rung_spacing,
            ground_offset=self.ground_offset,
            top_extension=self.top_extension,
            resolution=self.resolution,
        )

    # Snapshot storage for cancel restoration
    _snapshot_mesh   = None   # bmesh copy taken on invoke
    _snapshot_params = None   # param dict taken on invoke

    def _rebuild(self, context, commit=False):
        """
        Rebuild the ladder mesh from current properties.
        Dispatches to the correct builder based on dgm_ladder_type.
        commit=False  : live preview only — no expected_* or dgm_p_* written.
        commit=True   : final save — write all properties to object.
        """
        obj = context.active_object
        if obj is None or obj.type != 'MESH' or not obj.get('dgm_ladder'):
            return
        params = self._get_params()
        ladder_type = obj.get('dgm_ladder_type', 1)
        if ladder_type == 2:
            bm, rung_count, total_height = build_ladder_type2(params)
        else:
            bm, rung_count, total_height = build_ladder_type1(params)
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()
        # Always update display counters (these are cosmetic, not validated)
        obj['dgm_ladder_rungs']  = rung_count
        obj['dgm_ladder_height'] = round(total_height, 4)
        if commit:
            # Only write expected_* and dgm_p_* on confirmed OK
            obj['dgm_ladder_expected_height'] = round(total_height, 4)
            obj['dgm_ladder_expected_width']  = round(params['width'] + params['tube_diameter'], 4)
            obj['dgm_ladder_expected_depth']  = round(params['tube_diameter'], 4)
            obj['dgm_p_width']         = self.width
            obj['dgm_p_tube_diameter'] = self.tube_diameter
            obj['dgm_p_rung_count']    = self.rung_count
            obj['dgm_p_rung_spacing']  = self.rung_spacing
            obj['dgm_p_ground_offset'] = self.ground_offset
            obj['dgm_p_top_extension']  = self.top_extension
            obj['dgm_p_resolution']     = self.resolution
            obj['dgm_p_cage_depth']     = self.cage_depth
            obj['dgm_p_cage_bar_count'] = self.cage_bar_count
            obj['dgm_p_hoop_spacing']   = self.hoop_spacing
            obj['dgm_p_cage_start_z']   = self.cage_start_z
            obj['dgm_p_cage_tube_d']    = self.cage_tube_d

    def _snapshot(self, obj):
        """Take a bmesh snapshot of the current mesh and ALL properties for cancel restoration."""
        snap = bmesh.new()
        snap.from_mesh(obj.data)
        self._snapshot_mesh = snap
        self._snapshot_params = dict(
            width            = obj.get('dgm_p_width',                self.width),
            tube_diameter    = obj.get('dgm_p_tube_diameter',        self.tube_diameter),
            rung_count       = obj.get('dgm_p_rung_count',           self.rung_count),
            rung_spacing     = obj.get('dgm_p_rung_spacing',         self.rung_spacing),
            ground_offset    = obj.get('dgm_p_ground_offset',        self.ground_offset),
            top_extension    = obj.get('dgm_p_top_extension',        self.top_extension),
            resolution       = obj.get('dgm_p_resolution',           self.resolution),
            rungs            = obj.get('dgm_ladder_rungs',           self.rung_count),
            height           = obj.get('dgm_ladder_height',          0.0),
            expected_height  = obj.get('dgm_ladder_expected_height', None),
            expected_width   = obj.get('dgm_ladder_expected_width',  None),
            expected_depth   = obj.get('dgm_ladder_expected_depth',  None),
        )

    def _restore_snapshot(self, context):
        """Restore mesh and params from snapshot (used on cancel)."""
        obj = context.active_object
        if obj is None or self._snapshot_mesh is None:
            return
        self._snapshot_mesh.to_mesh(obj.data)
        obj.data.update()
        p = self._snapshot_params
        obj['dgm_p_width']         = p['width']
        obj['dgm_p_tube_diameter'] = p['tube_diameter']
        obj['dgm_p_rung_count']    = p['rung_count']
        obj['dgm_p_rung_spacing']  = p['rung_spacing']
        obj['dgm_p_ground_offset'] = p['ground_offset']
        obj['dgm_p_top_extension'] = p['top_extension']
        obj['dgm_p_resolution']    = p['resolution']
        obj['dgm_ladder_rungs']    = p['rungs']
        obj['dgm_ladder_height']   = p['height']
        # Restore expected_* so the integrity check doesn't fire after cancel
        if p['expected_height'] is not None:
            obj['dgm_ladder_expected_height'] = p['expected_height']
        if p['expected_width'] is not None:
            obj['dgm_ladder_expected_width']  = p['expected_width']
        if p['expected_depth'] is not None:
            obj['dgm_ladder_expected_depth']  = p['expected_depth']
        self._snapshot_mesh.free()
        self._snapshot_mesh   = None
        self._snapshot_params = None

    def invoke(self, context, event):
        obj = context.active_object
        # Load saved params from object
        self.width          = obj.get('dgm_p_width',         0.440)
        self.tube_diameter  = obj.get('dgm_p_tube_diameter', TUBE_DIAMETER_STD)
        self.rung_spacing   = obj.get('dgm_p_rung_spacing',  RUNG_SPACING_STD)
        self.ground_offset  = obj.get('dgm_p_ground_offset', GROUND_OFFSET_STD)
        self.top_extension  = obj.get('dgm_p_top_extension', TOP_EXT_STD)
        self.resolution     = obj.get('dgm_p_resolution',    10)
        stored_rungs = obj.get('dgm_p_rung_count', None)
        self.rung_count = stored_rungs if stored_rungs is not None                           else obj.get('dgm_ladder_rungs', 16)
        # Load cage params if editing a Type 2
        self.cage_depth      = obj.get('dgm_p_cage_depth',     0.700)
        self.cage_bar_count  = obj.get('dgm_p_cage_bar_count', 4)
        self.hoop_spacing    = obj.get('dgm_p_hoop_spacing',   0.900)
        self.cage_start_z    = obj.get('dgm_p_cage_start_z',   2.500)
        self.cage_tube_d     = obj.get('dgm_p_cage_tube_d',    0.025)
        # Take snapshot BEFORE opening dialog so cancel can restore
        self._snapshot(obj)
        # Do NOT call _rebuild here — mesh stays untouched until user edits something
        return context.window_manager.invoke_props_dialog(self, width=400)

    def cancel(self, context):
        """Called when user presses Escape or Cancel — restore original mesh."""
        self._restore_snapshot(context)

    def check(self, context):
        self._rebuild(context, commit=False)
        return True

    def draw(self, context):
        layout = self.layout
        params = self._get_params()

        obj = context.active_object
        obj_name = obj.name if obj else "?"

        box = layout.box()
        box.label(text="Editing: {}".format(obj_name), icon='MESH_CYLINDER')

        col = box.column(align=True)

        def prop_row(prop_name, std_value):
            row = col.row(align=True)
            row.prop(self, prop_name)
            row.label(text="", icon=_std_icon(getattr(self, prop_name), std_value))

        row_w = col.row(align=True)
        row_w.prop(self, 'width')
        w_icon = 'CHECKMARK' if round(self.width * 1000) in VALID_WIDTHS_MM else 'ERROR'
        row_w.label(text="", icon=w_icon)

        col.separator()
        prop_row('tube_diameter',  TUBE_DIAMETER_STD)
        col.separator()
        prop_row('rung_spacing',   RUNG_SPACING_STD)
        prop_row('ground_offset',  GROUND_OFFSET_STD)
        prop_row('top_extension',  TOP_EXT_STD)
        col.separator()
        col.prop(self, 'rung_count')

        bm_info, rung_count, total_height = build_ladder_type1(params)
        bm_info.free()
        last_rung_z = params['ground_offset'] + (rung_count - 1) * params['rung_spacing']

        info_box = layout.box()
        icol = info_box.column(align=True)
        icol.label(text="Rungs: {}".format(rung_count), icon='INFO')
        icol.label(text="Total height:  {:.3f} m".format(total_height))
        icol.label(text="Last rung at:  {:.3f} m".format(last_rung_z))
        icol.label(text="Width:  {:.0f} mm".format(params['width'] * 1000))

        # Show cage controls when editing Type 2
        obj = context.active_object
        if obj and obj.get('dgm_ladder_type') == 2:
            cage_box = layout.box()
            cage_box.label(text="Cage Settings", icon='MESH_CIRCLE')
            ccol = cage_box.column(align=True)
            ccol.prop(self, 'cage_depth')
            ccol.prop(self, 'cage_tube_d')
            ccol.separator()
            ccol.prop(self, 'hoop_spacing')
            ccol.prop(self, 'cage_bar_count')
            ccol.separator()
            ccol.prop(self, 'cage_start_z')

        q_row = layout.row(align=True)
        q_row.label(text="Tube Segments:", icon='MESH_CIRCLE')
        q_row.prop(self, 'resolution', text="")

    def execute(self, context):
        self._rebuild(context, commit=True)
        if self._snapshot_mesh:
            self._snapshot_mesh.free()
            self._snapshot_mesh   = None
            self._snapshot_params = None
        return {'FINISHED'}




# ---------------------------------------------------------------------------
#  Collision generator operator
# ---------------------------------------------------------------------------

class DGM_OT_ladder_collision(bpy.types.Operator):
    bl_idname      = "dgm.ladder_collision"
    bl_label       = "Generate Collision"
    bl_description = (
        "Generate Geometry LOD collision boxes for the selected ladder. "
        "Creates two stringer boxes (left + right rail), each 42 mm square, "
        "full ladder height, 20 kg each."
    )
    bl_options = {'REGISTER', 'UNDO'}

    mass_per_stringer: bpy.props.FloatProperty(
        name="Mass per Stringer (kg)",
        description="Collision mass of each stringer box in kg. Default: 20 kg.",
        default=20.0, min=1.0, max=500.0, step=10,
    )

    @classmethod
    def poll(cls, context):
        return _is_active_ladder(context.active_object)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Ladder Collision Settings", icon='MESH_CUBE')
        col = box.column(align=True)
        col.prop(self, 'mass_per_stringer')
        col.separator()
        col.label(text="2 components will be created:", icon='INFO')
        col.label(text="  Left stringer  —  {} kg".format(self.mass_per_stringer))
        col.label(text="  Right stringer —  {} kg".format(self.mass_per_stringer))
        col.label(text="  Total mass: {} kg".format(self.mass_per_stringer * 2))

    def execute(self, context):
        from . import geometry
        obj = context.active_object
        geo = geometry.create_ladder_collision(obj, self.mass_per_stringer)
        if geo is not None:
            self.report({'INFO'},
                "Collision created — 2 components, {} kg each".format(
                    self.mass_per_stringer))
        else:
            self.report({'WARNING'}, "No collision components created")
        return {'FINISHED'}

# ---------------------------------------------------------------------------
#  Restore operator — silently rebuilds ladder from stored params, no dialog
# ---------------------------------------------------------------------------

class DGM_OT_ladder_restore(bpy.types.Operator):
    bl_idname      = "dgm.ladder_restore"
    bl_label       = "Restore Ladder"
    bl_description = (
        "Restore ladder geometry to the correct dimensions stored in the object. "
        "Fixes any manual edits, scale changes, or Apply Scale issues."
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _is_active_ladder(context.active_object)

    def execute(self, context):
        obj = context.active_object

        # Save current transform — restore only mesh, not position/rotation
        saved_location = obj.location.copy()
        saved_rotation = obj.rotation_euler.copy()
        saved_scale    = obj.scale.copy()

        # Reset scale so mesh dimensions match the stored values exactly
        obj.scale = (1.0, 1.0, 1.0)

        # Rebuild mesh from stored params (generates local-space geometry)
        params = dict(
            width         = obj.get('dgm_p_width',         0.440),
            tube_diameter = obj.get('dgm_p_tube_diameter', TUBE_DIAMETER_STD),
            rung_count    = obj.get('dgm_p_rung_count',    16),
            rung_spacing  = obj.get('dgm_p_rung_spacing',  RUNG_SPACING_STD),
            ground_offset = obj.get('dgm_p_ground_offset', GROUND_OFFSET_STD),
            top_extension = obj.get('dgm_p_top_extension', TOP_EXT_STD),
            resolution    = obj.get('dgm_p_resolution',    10),
        )

        bm, rung_count, total_height = build_ladder_type1(params)
        bm.to_mesh(obj.data)
        bm.free()
        obj.data.update()

        # Restore position and rotation — only scale stays at 1,1,1
        obj.location      = saved_location
        obj.rotation_euler = saved_rotation

        # Refresh stored dimensions
        obj['dgm_ladder_rungs']           = rung_count
        obj['dgm_ladder_height']          = round(total_height, 4)
        obj['dgm_ladder_expected_height'] = round(total_height, 4)
        obj['dgm_ladder_expected_width']  = round(params['width'] + params['tube_diameter'], 4)
        obj['dgm_ladder_expected_depth']  = round(params['tube_diameter'], 4)

        self.report({'INFO'}, "Ladder restored to {:.3f} m".format(total_height))
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#  Panel section (called from operators.py)
# ---------------------------------------------------------------------------

def draw_ladder_generator_section(layout, context):
    obj       = context.active_object
    is_ladder = _is_active_ladder(obj)

    box = layout.box()
    box.label(text="Ladder Generator", icon='MESH_CYLINDER')

    # Add Ladder button + counter
    ladder_count = _count_scene_ladders()
    count_row = box.row(align=True)
    count_row.label(text="Ladders in scene: {}/3".format(ladder_count),
                    icon='CHECKMARK' if ladder_count < 3 else 'ERROR')

    add_row = box.row(align=True)
    add_row.enabled = ladder_count < 3
    add_row.scale_y = 1.3
    add_row.operator("dgm.ladder_type1", text="Add Ladder", icon='ADD')

    # Selected ladder info + Edit button — only when a ladder is selected
    if is_ladder:
        box.separator(factor=0.5)
        ladder_type = obj.get('dgm_ladder_type', 1)
        rungs       = obj.get('dgm_ladder_rungs', '?')
        height      = obj.get('dgm_ladder_height', '?')

        all_std = (
            round(obj.get('dgm_p_width', 0.440) * 1000) in VALID_WIDTHS_MM
            and abs(obj.get('dgm_p_tube_diameter', TUBE_DIAMETER_STD) - TUBE_DIAMETER_STD) < _TOL
            and abs(obj.get('dgm_p_rung_spacing',  RUNG_SPACING_STD)  - RUNG_SPACING_STD)  < _TOL
            and abs(obj.get('dgm_p_ground_offset', GROUND_OFFSET_STD) - GROUND_OFFSET_STD) < _TOL
            and abs(obj.get('dgm_p_top_extension', TOP_EXT_STD)       - TOP_EXT_STD)       < _TOL
        )
        status_icon = 'CHECKMARK' if all_std else 'ERROR'
        icol = box.column(align=True)
        icol.label(
            text="{}  |  {} rungs  |  {} m".format(obj.name, rungs, height),
            icon=status_icon)

        box.operator("dgm.ladder_edit", text="Edit Selected Ladder", icon='PREFERENCES')

        # Collision button — check if collision already exists for this ladder
        import json
        geo_obj = bpy.data.objects.get("Geometry")
        col_map = {}
        if geo_obj:
            try:
                col_map = json.loads(geo_obj.get('dgm_ladder_col_map', '{}'))
            except Exception:
                col_map = {}

        existing_comps = col_map.get(obj.name, [])
        # Verify the component vertex groups actually still exist
        if geo_obj and existing_comps:
            existing_comps = [c for c in existing_comps if geo_obj.vertex_groups.get(c)]

        col_row = box.row(align=True)
        if existing_comps:
            col_row.enabled = False
            col_row.operator("dgm.ladder_collision",
                text="Collision: {} ✓".format(", ".join(existing_comps)),
                icon='CHECKMARK')
        else:
            col_row.operator("dgm.ladder_collision",
                text="Generate Collision", icon='MESH_CUBE')

        # Geometry integrity check — detect scale, manual mesh edits, Apply Scale, etc.
        expected_h = obj.get('dgm_ladder_expected_height', None)
        if expected_h is not None:
            import mathutils as _mu
            world_corners = [obj.matrix_world @ _mu.Vector(c) for c in obj.bound_box]
            xs = [c.x for c in world_corners]
            ys = [c.y for c in world_corners]
            zs = [c.z for c in world_corners]
            actual_h = max(zs) - min(zs)
            actual_w = max(xs) - min(xs)
            actual_d = max(ys) - min(ys)

            expected_w = obj.get('dgm_ladder_expected_width', None)
            expected_d = obj.get('dgm_ladder_expected_depth', None)

            TOL = 0.005  # 5 mm tolerance
            height_ok = abs(actual_h - expected_h) < TOL
            width_ok  = expected_w is None or abs(actual_w - expected_w) < TOL
            depth_ok  = expected_d is None or abs(actual_d - expected_d) < TOL

            if not height_ok or not width_ok or not depth_ok:
                warn = box.box()
                warn.alert = True
                wcol = warn.column(align=True)
                wcol.label(text="Ladder geometry was modified!", icon='ERROR')
                if not height_ok:
                    wcol.label(
                        text="Height: {:.3f} m  (expected {:.3f} m)".format(
                            actual_h, expected_h),
                        icon='DOT')
                if not width_ok:
                    wcol.label(
                        text="Width:  {:.3f} m  (expected {:.3f} m)".format(
                            actual_w, expected_w),
                        icon='DOT')
                if not depth_ok:
                    wcol.label(
                        text="Depth:  {:.3f} m  (expected {:.3f} m)".format(
                            actual_d, expected_d),
                        icon='DOT')
                wcol.separator()
                wcol.label(text="Click to restore correct geometry:", icon='INFO')
                wcol.operator("dgm.ladder_restore", text="Restore Ladder", icon='FILE_REFRESH')




# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

ladder_classes = (
    DGM_OT_ladder_type1,
    DGM_OT_ladder_edit,
    DGM_OT_ladder_restore,
    DGM_OT_ladder_collision,
)


def register():
    for cls in ladder_classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(ladder_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

# ---------------------------------------------------------------------------
#  Registration
# ---------------------------------------------------------------------------

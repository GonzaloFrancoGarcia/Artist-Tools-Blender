import bpy, bmesh
from mathutils import Vector
from bmesh.types import BMVert

bl_info = {
    "name" : "Artist Tools Addon",
    "blender" : (4,4,3),
    "category" : "Object",
    "version" : (1,0,0),
    "author" : "Gonzalo Franco García",
    "description" : "Essential modeling toolkit: Mirror, Align, Pivot, Topology & Normals",
}

# ---------------- PROPIEDADES GLOBALES ----------------

# Propiedades para Mirror
PropiedadDistancia = bpy.props.FloatProperty(
    name = "Distance", 
    default = 2.0
)

# Propiedades para Topología
PropiedadNumLados = bpy.props.IntProperty(
    name = "Side Count", 
    default = 4, 
    min = 3
)

# Propiedades para Align
PropiedadAlignX = bpy.props.BoolProperty(
    name = "X", 
    default = True, 
    description = "Align on X axis"
)
PropiedadAlignY = bpy.props.BoolProperty(
    name = "Y", 
    default = True, 
    description = "Align on Y axis"
)
PropiedadAlignZ = bpy.props.BoolProperty(
    name = "Z", 
    default = True, 
    description = "Align on Z axis"
)


# ---------------- PANEL ----------------

class MiPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_mipanel"
    bl_label = "3ds Max"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Artist Tools"
    
    def draw(self, context):
        
        # --- 1. MIRROR ---
        self.layout.label(text = "Mirror:")
        col_mir = self.layout.column()
        col_mir.prop(context.scene, "distancia_mirror")
        
        row_mir = col_mir.row(align=True)
        op_x = row_mir.operator("opr.mirror_objeto", text="X")
        op_x.eje = "X"
        op_y = row_mir.operator("opr.mirror_objeto", text="Y")
        op_y.eje = "Y"
        op_z = row_mir.operator("opr.mirror_objeto", text="Z")
        op_z.eje = "Z"
        
        self.layout.separator()
        
        # --- 2. ALIGN ---
        self.layout.label(text = "Align:")
        col_align = self.layout.column()
        
        row = col_align.row(align=True)
        row.prop(context.scene, "align_x", toggle=True)
        row.prop(context.scene, "align_y", toggle=True)
        row.prop(context.scene, "align_z", toggle=True)
        
        col_align.operator("opr.alinear_objetos", 
            text="Align to Active", 
            icon="ALIGN_CENTER")

        self.layout.separator()
        
        # --- 3. PIVOT ---
        self.layout.label(text="Pivot:")
        col_pivote = self.layout.column()
        
        row_pivote = col_pivote.row(align=True)
        
        # Botones directos y sencillos
        op_geo = row_pivote.operator("opr.mover_pivote", text="To Geometry")
        op_geo.tipo = "GEOMETRY" 
        
        op_cur = row_pivote.operator("opr.mover_pivote", text="To Cursor")
        op_cur.tipo = "CURSOR"

        self.layout.separator()

        # --- 4. SELECTION ---
        self.layout.label(text="Selection:")
        col_qa = self.layout.column()
        
        row_qa = col_qa.row(align=True)
        row_qa.prop(context.scene, "num_lados_select") 
        row_qa.operator("opr.select_by_sides", 
            text="Select", 
            icon="RESTRICT_SELECT_OFF")
            
        self.layout.separator()

        # --- 5. FLIP ---
        self.layout.label(text="Normals:")
        col_normales = self.layout.column()
        
        col_normales.operator("opr.flip_normals", 
            text="Flip", 
            icon="FILE_REFRESH")


# ---------------- OPERADORES ----------------

class OperadorMirror(bpy.types.Operator):
    bl_idname = "opr.mirror_objeto"
    bl_label = "Hacer Mirror"
    bl_options = {'REGISTER', 'UNDO'}
    
    eje: bpy.props.StringProperty()

    def execute(self, context):
        if context.object.mode != 'OBJECT':
             bpy.ops.object.mode_set(mode='OBJECT')

        obj = context.active_object
        
        bpy.ops.object.duplicate_move()
        copia = context.active_object
        
        dist = context.scene.distancia_mirror
        
        if self.eje == "X":
            copia.scale[0] *= -1
            copia.location[0] += dist
        elif self.eje == "Y":
            copia.scale[1] *= -1
            copia.location[1] += dist
        elif self.eje == "Z":
            copia.scale[2] *= -1
            copia.location[2] += dist
            
        return {"FINISHED"}


class OperadorAlign(bpy.types.Operator):
    bl_idname = "opr.alinear_objetos"
    bl_label = "Alinear Objetos"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.active_object
        
        do_x = context.scene.align_x
        do_y = context.scene.align_y
        do_z = context.scene.align_z
        
        selected_objs = context.selected_objects
        for obj in selected_objs:
            if obj != target:
                if do_x: 
                    obj.location.x = target.location.x
                if do_y: 
                    obj.location.y = target.location.y
                if do_z: 
                    obj.location.z = target.location.z
        
        return {'FINISHED'}


class OperadorPivot(bpy.types.Operator):
    bl_idname = "opr.mover_pivote"
    bl_label = "Mover Pivote"
    bl_options = {'REGISTER', 'UNDO'}
    
    tipo: bpy.props.StringProperty()

    def execute(self, context):
        if context.object.mode != 'OBJECT':
             bpy.ops.object.mode_set(mode='OBJECT')
             
        if self.tipo == "GEOMETRY":
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            
        elif self.tipo == "CURSOR":
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            
        return {'FINISHED'}


class OperadorSelection(bpy.types.Operator):
    bl_idname = "opr.select_by_sides"
    bl_label = "Seleccionar por Lados"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        
        bpy.ops.object.mode_set(mode='EDIT')
            
        lados = context.scene.num_lados_select
        
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.faces.ensure_lookup_table()
        
        bpy.ops.mesh.select_all(action='DESELECT')
        
        bpy.ops.mesh.select_mode(type='FACE')
        
        for face in bm.faces:
            if len(face.verts) == lados:
                face.select = True
                
        bmesh.update_edit_mesh(me)
        return {'FINISHED'}


class OperadorFlip(bpy.types.Operator):
    bl_idname = "opr.flip_normals"
    bl_label = "Voltear Normales"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.flip_normals()
        
        return {'FINISHED'}


# ---------------- REGISTRO ----------------

CLASES = [
    MiPanel,
    OperadorMirror,
    OperadorAlign,
    OperadorPivot,
    OperadorSelection,
    OperadorFlip
]

PROPIEDADES = [
    ("distancia_mirror", PropiedadDistancia),
    ("num_lados_select", PropiedadNumLados),
    ("align_x", PropiedadAlignX),
    ("align_y", PropiedadAlignY),
    ("align_z", PropiedadAlignZ)
]

def register():
    for (nombre_prop, valor_prop) in PROPIEDADES:
        setattr(bpy.types.Scene, 
            nombre_prop, 
            valor_prop)
            
    for i in CLASES:
        bpy.utils.register_class(i)
        
def unregister():
    for (nombre_prop, valor_prop) in PROPIEDADES:
        delattr(bpy.types.Scene, 
            nombre_prop)
            
    for i in CLASES:
        bpy.utils.unregister_class(i)
        
if __name__ == "__main__":
    register()
class ADDON_OT_operator_name( bpy.types.Operator ):
    bl_idname = "object.operator_name"
    bl_label = "Operator Label"
    bl_description = "Description of the operator"
    bl_options = {'REGISTER','UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}
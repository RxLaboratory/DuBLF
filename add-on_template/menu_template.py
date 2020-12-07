class ADDON_MT_menu( bpy.types.Menu ):
    bl_label = 'Menu'
    bl_idname = 'ADDON_MT_menu'

    def draw(self, context):
        layout = self.layout
        layout.label('Menu')
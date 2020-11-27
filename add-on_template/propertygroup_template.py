class ADDON_prop_name( bpy.types.PropertyGroup ):
    """Description"""
    name: bpy.props.StringProperty(default = '')
    integer: bpy.props.IntProperty()
    items: bpy.props.CollectionProperty( type=bpy.types.StringProperty )
#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

# The Duduf Blender Framework
# Useful tools to develop scripts in Blender

import bpy # pylint: disable=import-error
import time
import re
import importlib
from . import (rigging, oca)

# ========= UTILS ======================

class DUBLF_utils():
    """Utilitaries for Duduf's tools"""
    
    toolName = "Dublf"
    
    def log( self, log = "", time_start = 0 ):
        """Logs Duik activity"""
        t = time.time() - time_start
        print( " ".join( [ self.toolName , " (%.2f s):" % t , log ] ) )
        
    def showMessageBox( self, message = "", title = "Message Box", icon = 'INFO'):
        """Displays a simple message box"""
        def draw(self, context):
            self.layout.alert = True
            self.layout.label(text = message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

# ========= STRING METHODS =============

class DUBLF_string():
    """Useful string methods"""

    @staticmethod
    def get_baseName( filename ):
        """Gets the name part of a filename without the extension"""
        fileBaseName = filename
        fileBaseNameList = filename.split('.')
        if len(fileBaseNameList) > 1:
            fileBaseName = '.'.join(fileBaseNameList[0:-1])
        return fileBaseName

# ========= File System METHODS ========

class DUBLF_fs():
    """Useful File System methods"""

    @staticmethod
    def get_fileBaseName( file ):
        """Gets the name part of a file without the extension"""
        filename = ""
        if isinstance(file, bpy.types.OperatorFileListElement):
            filename = file.name
        else:
            try:
                filename = file.stem
            except:
                pass
        return DUBLF_string.get_baseName(filename)

# ========= HANDLERS METHODS ===========

class DUBLF_handlers():
    """Methods to help creating and removing Blender handlers"""

    @staticmethod
    def append_function_unique(fn_list, fn):
        """ Appending 'fn' to 'fn_list',
            Remove any functions from with a matching name & module.
        """
        DUBLF_handlers.remove_function(fn_list, fn)
        fn_list.append(fn)

    @staticmethod
    def remove_function(fn_list, fn):
        """Removes a function from the list, if it is there"""
        fn_name = fn.__name__
        fn_module = fn.__module__
        for i in range(len(fn_list) - 1, -1, -1):
            if fn_list[i].__name__ == fn_name and fn_list[i].__module__ == fn_module:
                del fn_list[i]

    @staticmethod
    def frame_change_pre_append( fn ):
        """Appends a function to frame_change_pre handler, taking care of duplicates"""
        DUBLF_handlers.append_function_unique( bpy.app.handlers.frame_change_pre, fn )

    @staticmethod
    def frame_change_pre_remove( fn ):
        """Removes a function from frame_change_pre handler"""
        DUBLF_handlers.remove_function( bpy.app.handlers.frame_change_pre, fn )

    @staticmethod
    def frame_change_post_append( fn ):
        """Appends a function to frame_change_pre handler, taking care of duplicates"""
        DUBLF_handlers.append_function_unique( bpy.app.handlers.frame_change_post, fn )

    @staticmethod
    def frame_change_post_remove( fn ):
        """Removes a function from frame_change_pre handler"""
        DUBLF_handlers.remove_function( bpy.app.handlers.frame_change_post, fn )

    @staticmethod
    def depsgraph_update_post_append( fn ):
        """Appends a function to frame_change_pre handler, taking care of duplicates"""
        DUBLF_handlers.append_function_unique( bpy.app.handlers.depsgraph_update_post, fn )

    @staticmethod
    def depsgraph_update_post_remove( fn ):
        """Removes a function from frame_change_pre handler"""
        DUBLF_handlers.remove_function( bpy.app.handlers.depsgraph_update_post, fn )

# ========= RNA ========================

class DuBLF_rna():
    """Methods to help rna paths"""

    @staticmethod
    def get_bpy_struct( obj_id, path):
        """ Gets a bpy_struct or property from an ID and an RNA path
            Returns None in case the path is invalid
            """
        try:
            # this regexp matches with two results: first word and what's in brackets if any
            # "prop['test']" -> [("prop", "'test'")]
            # "prop" -> [("prop","")]
            # "prop[12]" -> [("prop","12")]
            matches = re.findall( r'(\w+)?(?:\[([^\]]+)\])?' , path )
            print(matches)
            for i,match in enumerate(matches) :
                attr = match[0]
                arr = match[1]
                if i == len(matches) -2:
                    if attr != '' and  arr != '':
                        obj_id = getattr(obj_id, attr)
                        return obj_id, '[' + arr + ']'
                    elif attr != '':
                        return obj_id, attr
                    else:
                        return obj_id, '[' + arr + ']'
                if attr != '':
                    obj_id = getattr(obj_id, attr)
                if arr != '':
                    obj_id = obj_id[ eval(arr) ]
            return None           
        except:
            return None

# ========= ADDONS =====================

class DuBLF_addons():
    """Methods to work with addons"""

    @staticmethod
    def is_addon_enabled( moduleName ):
        addons = bpy.context.preferences.addons
        for addon in addons:
            if addon.module == moduleName:
                return True
        return False

# ========= COLLECTIONS ================

class DuBLF_collections():
    """Collection related methods"""

    @staticmethod
    def add_collection_to_scene( scene, collectionName ):
        col = bpy.data.collections.new(collectionName)
        scene.collection.children.link(col)
        return col

    @staticmethod
    def remove_from_collection(collection, obj):
        """recursively removes an object from a collection"""
        objects = collection.objects
        if obj.name in objects:
            objects.unlink(obj)
        for col in collection.children:
            DuBLF_collections.remove_from_collection(col, obj)

    @staticmethod
    def remove_collection_from_collection(collection, col):
        """recursively removes a collection from another collection"""
        children = collection.children
        if col.name in children:
            children.unlink(col)
        for child in collection.children:
            DuBLF_collections.remove_from_collection(child, col)

    @staticmethod
    def move_to_collection( collection, obj):
        """Moves an object from the main collection to a specific one"""
        # remove from all collections
        for scene in bpy.data.scenes:
            DuBLF_collections.remove_from_collection(scene.collection, obj)
        # move to the new
        collection.objects.link(obj)

    @staticmethod
    def move_collection_to_collection( destination, collection):
        """Moves a collection to another collection"""
        # remove from all collections
        for scene in bpy.data.scenes:
            DuBLF_collections.remove_collection_from_collection(scene.collection, collection)
        # move to the new
        destination.children.link(collection)
        

# ========= MATERIALS ==================

class DuBLF_materials():
    """Material related methods"""

    @staticmethod
    def create_color_material( color, matName="Color", shading='SHADELESS' ):
        material = bpy.data.materials.new(matName)
        material.use_nodes = True
        node_tree = material.node_tree
        outputNode = DuBLF_materials.clean_node_tree(node_tree)

        material.diffuse_color = color
        material.blend_method = 'HASHED'
        material.shadow_method = 'HASHED'
        
        rgbNode = node_tree.nodes.new('ShaderNodeRGB')
        rgbNode.outputs[0].default_value = color
        alphaNode = node_tree.nodes.new('ShaderNodeValue')
        alphaNode.name = "Alpha"
        alphaNode.outputs[0].default_value = color[3]
        
        # Create Shader
        if shading == 'PRINCIPLED':
            shaderNode = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        elif shading == 'SHADELESS':
            shaderNode = DuBLF_materials.get_shadeless_node(node_tree)
        else:  # Emission Shading
            shaderNode = node_tree.nodes.new('ShaderNodeEmission')
        
        # Connect color
        node_tree.links.new(shaderNode.inputs[0], rgbNode.outputs[0])
        
        # Alpha
        if shading == 'PRINCIPLED':
            node_tree.links.new(shaderNode.inputs[18], alphaNode.outputs[0])
        else:
            bsdf_transparent = node_tree.nodes.new('ShaderNodeBsdfTransparent')

            mix_shader = node_tree.nodes.new('ShaderNodeMixShader')
            node_tree.links.new(mix_shader.inputs[0], alphaNode.outputs[0])
            node_tree.links.new(mix_shader.inputs[1], bsdf_transparent.outputs[0])
            node_tree.links.new(mix_shader.inputs[2], shaderNode.outputs[0])
            shaderNode = mix_shader
        
        # Connect to output
        node_tree.links.new(outputNode.inputs[0], shaderNode.outputs[0])
        
        # Align
        DuBLF_materials.auto_align_nodes(node_tree)
        
        return material

    @staticmethod
    def get_input_nodes(node, links):
        """Get nodes that are a inputs to the given node"""
        # Get all links going to node.
        input_links = {lnk for lnk in links if lnk.to_node == node}
        # Sort those links, get their input nodes (and avoid doubles!).
        sorted_nodes = []
        done_nodes = set()
        for socket in node.inputs:
            done_links = set()
            for link in input_links:
                nd = link.from_node
                if nd in done_nodes:
                    # Node already treated!
                    done_links.add(link)
                elif link.to_socket == socket:
                    sorted_nodes.append(nd)
                    done_links.add(link)
                    done_nodes.add(nd)
            input_links -= done_links
        return sorted_nodes

    @staticmethod
    def clean_node_tree(node_tree):
        """Clear all nodes in a shader node tree except the output.

        Returns the output node
        """
        nodes = node_tree.nodes
        for node in list(nodes):  # copy to avoid altering the loop's data source
            if not node.type == 'OUTPUT_MATERIAL':
                nodes.remove(node)

        return node_tree.nodes[0]

    @staticmethod
    def get_shadeless_node(dest_node_tree):
        """Return a "shadless" cycles/eevee node, creating a node group if nonexistent"""
        try:
            node_tree = bpy.data.node_groups['IAP_SHADELESS']

        except KeyError:
            # need to build node shadeless node group
            node_tree = bpy.data.node_groups.new('IAP_SHADELESS', 'ShaderNodeTree')
            output_node = node_tree.nodes.new('NodeGroupOutput')
            input_node = node_tree.nodes.new('NodeGroupInput')

            node_tree.outputs.new('NodeSocketShader', 'Shader')
            node_tree.inputs.new('NodeSocketColor', 'Color')

            # This could be faster as a transparent shader, but then no ambient occlusion
            diffuse_shader = node_tree.nodes.new('ShaderNodeBsdfDiffuse')
            node_tree.links.new(diffuse_shader.inputs[0], input_node.outputs[0])

            emission_shader = node_tree.nodes.new('ShaderNodeEmission')
            node_tree.links.new(emission_shader.inputs[0], input_node.outputs[0])

            light_path = node_tree.nodes.new('ShaderNodeLightPath')
            is_glossy_ray = light_path.outputs['Is Glossy Ray']
            is_shadow_ray = light_path.outputs['Is Shadow Ray']
            ray_depth = light_path.outputs['Ray Depth']
            transmission_depth = light_path.outputs['Transmission Depth']

            unrefracted_depth = node_tree.nodes.new('ShaderNodeMath')
            unrefracted_depth.operation = 'SUBTRACT'
            unrefracted_depth.label = 'Bounce Count'
            node_tree.links.new(unrefracted_depth.inputs[0], ray_depth)
            node_tree.links.new(unrefracted_depth.inputs[1], transmission_depth)

            refracted = node_tree.nodes.new('ShaderNodeMath')
            refracted.operation = 'SUBTRACT'
            refracted.label = 'Camera or Refracted'
            refracted.inputs[0].default_value = 1.0
            node_tree.links.new(refracted.inputs[1], unrefracted_depth.outputs[0])

            reflection_limit = node_tree.nodes.new('ShaderNodeMath')
            reflection_limit.operation = 'SUBTRACT'
            reflection_limit.label = 'Limit Reflections'
            reflection_limit.inputs[0].default_value = 2.0
            node_tree.links.new(reflection_limit.inputs[1], ray_depth)

            camera_reflected = node_tree.nodes.new('ShaderNodeMath')
            camera_reflected.operation = 'MULTIPLY'
            camera_reflected.label = 'Camera Ray to Glossy'
            node_tree.links.new(camera_reflected.inputs[0], reflection_limit.outputs[0])
            node_tree.links.new(camera_reflected.inputs[1], is_glossy_ray)

            shadow_or_reflect = node_tree.nodes.new('ShaderNodeMath')
            shadow_or_reflect.operation = 'MAXIMUM'
            shadow_or_reflect.label = 'Shadow or Reflection?'
            node_tree.links.new(shadow_or_reflect.inputs[0], camera_reflected.outputs[0])
            node_tree.links.new(shadow_or_reflect.inputs[1], is_shadow_ray)

            shadow_or_reflect_or_refract = node_tree.nodes.new('ShaderNodeMath')
            shadow_or_reflect_or_refract.operation = 'MAXIMUM'
            shadow_or_reflect_or_refract.label = 'Shadow, Reflect or Refract?'
            node_tree.links.new(shadow_or_reflect_or_refract.inputs[0], shadow_or_reflect.outputs[0])
            node_tree.links.new(shadow_or_reflect_or_refract.inputs[1], refracted.outputs[0])

            mix_shader = node_tree.nodes.new('ShaderNodeMixShader')
            node_tree.links.new(mix_shader.inputs[0], shadow_or_reflect_or_refract.outputs[0])
            node_tree.links.new(mix_shader.inputs[1], diffuse_shader.outputs[0])
            node_tree.links.new(mix_shader.inputs[2], emission_shader.outputs[0])

            node_tree.links.new(output_node.inputs[0], mix_shader.outputs[0])

            DuBLF_materials.auto_align_nodes(node_tree)

        group_node = dest_node_tree.nodes.new("ShaderNodeGroup")
        group_node.node_tree = node_tree

        return group_node

    @staticmethod
    def auto_align_nodes(node_tree):
        """Given a shader node tree, arrange nodes neatly relative to the output node."""
        x_gap = 200
        y_gap = 180
        nodes = node_tree.nodes
        links = node_tree.links
        output_node = None
        for node in nodes:
            if node.type == 'OUTPUT_MATERIAL' or node.type == 'GROUP_OUTPUT':
                output_node = node
                break

        else:  # Just in case there is no output
            return

        def align(to_node):
            from_nodes = DuBLF_materials.get_input_nodes(to_node, links)
            for i, node in enumerate(from_nodes):
                node.location.x = min(node.location.x, to_node.location.x - x_gap)
                node.location.y = to_node.location.y
                node.location.y -= i * y_gap
                node.location.y += (len(from_nodes) - 1) * y_gap / (len(from_nodes))
                align(node)

        align(output_node)

def register():
    importlib.reload(rigging)
    importlib.reload(oca)

    rigging.register()
    oca.register()

def unregister():
    rigging.unregister()
    oca.register()
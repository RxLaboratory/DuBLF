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

import bpy # pylint: disable=import-error
from bpy_extras.image_utils import load_image  # pylint: disable=import-error

def create_image_material( image, matName="Image", shading = 'SHADELESS'):
    
    im = load_image(image, check_existing=True, force_reload=True)
    return create_im_material(im, matName, shading)
    

def create_im_material(image, matName="Image", shading='SHADELESS'):
    material = bpy.data.materials.new(matName)
    material.use_nodes = True
    node_tree = material.node_tree
    output_node = clean_node_tree(node_tree)

    material.blend_method = 'BLEND'
    material.shadow_method = 'HASHED'

    texture_node = node_tree.nodes.new('ShaderNodeTexImage')
    texture_node.image = image
    texture_node.show_texture = True
    texture_node.extension = 'CLIP'

    # Create tree
    create_color_alpha_tree( node_tree, texture_node.outputs[0], texture_node.outputs[1], output_node.inputs[0], shading)

    return material, texture_node


def create_color_material( color, matName="Color", shading='SHADELESS' ):
    material = bpy.data.materials.new(matName)
    material.use_nodes = True
    node_tree = material.node_tree
    outputNode = clean_node_tree(node_tree)

    material.diffuse_color = color
    material.blend_method = 'BLEND'
    material.shadow_method = 'HASHED'
    
    rgbNode = node_tree.nodes.new('ShaderNodeRGB')
    rgbNode.outputs[0].default_value = color
    alphaNode = node_tree.nodes.new('ShaderNodeValue')
    alphaNode.name = "Alpha"
    alphaNode.outputs[0].default_value = color[3]
    
    # Create tree
    create_color_alpha_tree( node_tree, rgbNode.outputs[0], alphaNode.outputs[0], outputNode.inputs[0], shading)
    
    return material

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

def clean_node_tree(node_tree):
    """Clear all nodes in a shader node tree except the output.

    Returns the output node
    """
    nodes = node_tree.nodes
    for node in list(nodes):  # copy to avoid altering the loop's data source
        if not node.type == 'OUTPUT_MATERIAL':
            nodes.remove(node)

    return node_tree.nodes[0]

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

        auto_align_nodes(node_tree)

    group_node = dest_node_tree.nodes.new("ShaderNodeGroup")
    group_node.node_tree = node_tree

    return group_node

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
        from_nodes = get_input_nodes(to_node, links)
        for i, node in enumerate(from_nodes):
            node.location.x = min(node.location.x, to_node.location.x - x_gap)
            node.location.y = to_node.location.y
            node.location.y -= i * y_gap
            node.location.y += (len(from_nodes) - 1) * y_gap / (len(from_nodes))
            align(node)

    align(output_node)

def create_color_alpha_tree(node_tree,color_input, alpha_input, shader_output, shading='SHADELESS'):
    # Create Shader
    if shading == 'PRINCIPLED':
        shaderNode = node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    elif shading == 'SHADELESS':
        shaderNode = get_shadeless_node(node_tree)
    else:  # Emission Shading
        shaderNode = node_tree.nodes.new('ShaderNodeEmission')
    
    # Connect color
    node_tree.links.new(shaderNode.inputs[0], color_input)
    
    # Alpha
    alpha_node = node_tree.nodes.new('ShaderNodeMath')
    alpha_node.operation = 'MULTIPLY'
    alpha_node.inputs[1].default_value = 1
    alpha_node.label = "Opacity"
    alpha_node.name = "Opacity"
    if shading == 'PRINCIPLED':
        node_tree.links.new(alpha_node.inputs[0], alpha_input)
        node_tree.links.new(shaderNode.inputs[18], alpha_node.outputs[0])
    else:
        bsdf_transparent = node_tree.nodes.new('ShaderNodeBsdfTransparent')

        mix_shader = node_tree.nodes.new('ShaderNodeMixShader')
        node_tree.links.new(alpha_node.inputs[0], alpha_input)
        node_tree.links.new(mix_shader.inputs[0], alpha_node.outputs[0])
        node_tree.links.new(mix_shader.inputs[1], bsdf_transparent.outputs[0])
        node_tree.links.new(mix_shader.inputs[2], shaderNode.outputs[0])
        shaderNode = mix_shader
    
    # Connect to output
    node_tree.links.new(shader_output, shaderNode.outputs[0])
    
    # Align
    auto_align_nodes(node_tree)

def get_blank_image():
    try:
        im = bpy.data.images['OCA_blank']
    except KeyError:
        im = bpy.data.images.new('OCA_blank', 256, 256, alpha=True)
        im.generated_color = (0.0,0.0,0.0,0.0)
    return im

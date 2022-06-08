import numpy as np
import math
import gpu
import bgl
import bpy
from gpu_extras.batch import batch_for_shader


def get_teximage(context):
    teximage = None
    teximage = context.area.spaces.active.image

    if teximage is not None and teximage.size[1] != 0:
        return teximage
    else:
        return None


def gl_copy(image):
    if image.gl_load():
        raise Exception()

    width, height = image.size
    offscreen = gpu.types.GPUOffScreen(width, height)

    with offscreen.bind():
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)
        with gpu.matrix.push_pop():
            # reset matrices -> use normalized device coordinates [-1, 1]
            gpu.matrix.load_matrix(mu.Matrix.Identity(4))
            gpu.matrix.load_projection_matrix(mu.Matrix.Identity(4))

            shader = gpu.shader.from_builtin("2D_IMAGE")
            batch = batch_for_shader(
                shader,
                "TRI_FAN",
                {
                    "pos": ((0, 0), (width - 1, 0), (width - 1, height - 1), (0, height - 1)),
                    "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
                },
            )

            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)

            shader.bind()
            shader.uniform_int("image", 0)
            batch.draw(shader)

        buffer = bgl.Buffer(bgl.GL_BYTE, width * height * 4)
        bgl.glReadBuffer(bgl.GL_BACK)
        bgl.glReadPixels(0, 0, width, height, bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, buffer)

    offscreen.free()
    return np.array(buffer.to_list()).astype(np.float).reshape((width, height, 4)) / 255.0


def rgb2hsv(image):
    tmp = image[:, :, :3]
    r = tmp[:, :, 0]
    g = tmp[:, :, 1]
    b = tmp[:, :, 2]

    acmax = tmp.argmax(2)
    cmax = tmp.max(2)
    cmin = tmp.min(2)
    delta = cmax - cmin

    # R G B = 0 1 2
    # prevent zero division
    delta[delta == 0.0] = 1.0
    hr = np.where(acmax == 0, ((g - b) / delta) % 6.0, 0.0)
    hg = np.where(acmax == 1, (b - r) / delta + 2.0, 0.0)
    hb = np.where(acmax == 2, (r - g) / delta + 4.0, 0.0)

    H = np.where(cmax == cmin, 0.0, (hr + hg + hb) / 6.0)
    H[H < 0.0] += 1.0

    # L = (cmax + cmin) / 2.0
    # St = (cmax <= 0.0001) + (cmin >= 0.9999) + (L == 1.0) + (L == 0.0)
    # S = np.where(St, 0.0, (cmax - L) / np.minimum(L, 1.0 - L))

    L = cmax
    St = cmax <= 0.0001
    cmax[St] = 1.0
    S = np.where(St, 0.0, (cmax - cmin) / cmax)

    return [H, S, L]


def add_material(name, image):
    if len(name) > 60:
        name = name[:60]
    if name not in bpy.data.materials.keys():
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        sn = mat.node_tree.nodes.new("ShaderNodeTexImage")
        bc = mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"]
        mat.node_tree.links.new(sn.outputs["Color"], bc)
    else:
        mat = bpy.data.materials[name]

    mat.node_tree.nodes["Image Texture"].image = image
    return mat


def linear2srgb(c):
    if c < 0.0031308:
        srgb = 0.0 if c < 0.0 else c * 12.92
    else:
        srgb = 1.055 * math.pow(c, 1.0 / 2.4) - 0.055
    return max(min(srgb, 1.0), 0.0)


def linear2srgb_np(c):
    srgb = np.where(c < 0.0031308, c * 12.92, 1.055 * np.pow(c, 1.0 / 2.4) - 0.055)
    srgb[srgb > 1.0] = 1.0
    srgb[srgb < 0.0] = 0.0
    return srgb

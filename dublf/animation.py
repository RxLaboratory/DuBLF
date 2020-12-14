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

def get_curves(obj, data_path):
    """Returns all curves refering to this object and data_path"""
    curves = []
    anim_data = obj.animation_data
    if anim_data is None: return curves
    action = obj.animation_data.action
    if action is None: return curves
    fcurves = action.fcurves
    for curve in fcurves:
        if curve.data_path == data_path:
            curves.append(curve)
    return curves

def get_previous_keyframe(fcurve, frame):
    keyframes = fcurve.keyframe_points
    if len(keyframes) == 0: return None
    for keyframe in reversed(keyframes):
        f = keyframe.co[0]
        if f <= frame: return keyframe
    return None

def get_next_keyframe(fcurve, frame):
    keyframes = fcurve.keyframe_points
    if len(keyframes) == 0: return None
    for keyframe in keyframes:
        f = keyframe.co[0]
        if f >= frame: return keyframe
    return None

def is_animated(obj):
    anim_data = obj.animation_data
    if anim_data is None: return False
    if anim_data.action is None: return False
    return len(anim_data.action.fcurves) > 0

def remove_animated_index(obj, data_path, index):
    """In an animated index (like for a list), removes an index,
    and offsets all keyframes with a higher index to continue referencing the same item"""
    curves = get_curves(obj, data_path)
    for curve in curves:
        keyframes = curve.keyframe_points
        for keyframe in reversed(keyframes):
            val = keyframe.co[1]
            if val == index:
                keyframes.remove(keyframe)
            elif val > index:
                keyframe.co[1] = val - 1

def swap_animated_index(obj, data_path, indexA, indexB):
    """Swaps two indices in an animated index (like for a list)"""
    curves = get_curves(obj, data_path)
    for curve in curves:
        keyframes = curve.keyframe_points
        for keyframe in keyframes:
            if keyframe.co[1] == indexB: keyframe.co[1] = indexA
            elif keyframe.co[1] == indexA: keyframe.co[1] = indexB

def remove_all_keyframes(obj, data_path):
    """Removes all keyframes for this data path"""
    curves = get_curves(obj, data_path)
    for curve in curves:
        keyframes = curve.keyframe_points
        for keyframe in reversed(keyframes):
            keyframes.remove(keyframe)
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

def get_previous_keyframe(fcurve, frame):
    keyframes = fcurve.keyframe_points
    if len(keyframes) == 0: return None
    for keyframe in reversed(keyframes):
        f = keyframe.co[0]
        if f < frame: return keyframe
    return None

def get_next_keyframe(fcurve, frame):
    keyframes = fcurve.keyframe_points
    if len(keyframes) == 0: return None
    for keyframe in keyframes:
        f = keyframe.co[0]
        if f > frame: return keyframe
    return None

def get_keyframe_at_frame(fcurve, frame):
    keyframes = fcurve.keyframe_points
    if len(keyframes) == 0: return None
    for keyframe in keyframes:
        f = keyframe.co[0]
        if f == frame: return keyframe
        if f > frame: return None
    return None
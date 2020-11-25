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
from re import findall

def get_bpy_struct( obj_id, path):
    """ Gets a bpy_struct or property from an ID and an RNA path
        Returns None in case the path is invalid
        """
    try:
        # this regexp matches with two results: first word and what's in brackets if any
        # "prop['test']" -> [("prop", "'test'")]
        # "prop" -> [("prop","")]
        # "prop[12]" -> [("prop","12")]
        matches = findall( r'(\w+)?(?:\[([^\]]+)\])?' , path )
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

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

bl_info = {
    "name": "IAddon name",
    "category": "Import-Export",
    "blender": (2, 80, 0),
    "author": "Nicolas 'Duduf' Dufresne",
    "location": "File > Import",
    "version": (0,0,1),
    "description": "Addon description.",
    "wiki_url": "https://oca-blender-docs.rainboxlab.org/",
}

import bpy # pylint: disable=import-error
import importlib

classes = (

)

def register():

    # TODO in dev&debug only
    # importlib.reload(autorig)

    # register
    for cls in classes:
        bpy.utils.register_class(cls)

    # modules
    # dublf.register()
    
def unregister():
    # unregister
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # modules
    # dublf.unregister()

if __name__ == "__main__":
    register()
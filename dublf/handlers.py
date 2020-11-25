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

def append_function_unique(fn_list, fn):
    """ Appending 'fn' to 'fn_list',
        Remove any functions from with a matching name & module.
    """
    remove_function(fn_list, fn)
    fn_list.append(fn)

def remove_function(fn_list, fn):
    """Removes a function from the list, if it is there"""
    fn_name = fn.__name__
    fn_module = fn.__module__
    for i in range(len(fn_list) - 1, -1, -1):
        if fn_list[i].__name__ == fn_name and fn_list[i].__module__ == fn_module:
            del fn_list[i]

def frame_change_pre_append( fn ):
    """Appends a function to frame_change_pre handler, taking care of duplicates"""
    append_function_unique( bpy.app.handlers.frame_change_pre, fn )

def frame_change_pre_remove( fn ):
    """Removes a function from frame_change_pre handler"""
    remove_function( bpy.app.handlers.frame_change_pre, fn )

def frame_change_post_append( fn ):
    """Appends a function to frame_change_pre handler, taking care of duplicates"""
    append_function_unique( bpy.app.handlers.frame_change_post, fn )

def frame_change_post_remove( fn ):
    """Removes a function from frame_change_pre handler"""
    remove_function( bpy.app.handlers.frame_change_post, fn )

def depsgraph_update_post_append( fn ):
    """Appends a function to frame_change_pre handler, taking care of duplicates"""
    append_function_unique( bpy.app.handlers.depsgraph_update_post, fn )

def depsgraph_update_post_remove( fn ):
    """Removes a function from frame_change_pre handler"""
    remove_function( bpy.app.handlers.depsgraph_update_post, fn )

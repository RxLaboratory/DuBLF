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

def get_create_collection( collection_name ):
    """Gets, or creates if needed, a collection by its name.
    It is not added to the current scene."""
    
    for col in bpy.data.collections:
        if col.name == collection_name:
            # Check if it's in the scene
            
            return col
    col = bpy.data.collections.new(collection_name)
    return col

def add_collection_to_scene( scene, collectionName ):
    col = bpy.data.collections.new(collectionName)
    scene.collection.children.link(col)
    return col

def remove_from_collection(collection, obj):
    """recursively removes an object from a collection"""
    objects = collection.objects
    if obj.name in objects:
        objects.unlink(obj)
    for col in collection.children:
        remove_from_collection(col, obj)

def remove_collection_from_collection(collection, col):
    """recursively removes a collection from another collection"""
    children = collection.children
    if col.name in children:
        children.unlink(col)
    for child in collection.children:
        remove_collection_from_collection(child, col)

def move_to_collection( collection, obj):
    """Moves an object from the main collection to a specific one"""
    # remove from all collections
    for scene in bpy.data.scenes:
        remove_from_collection(scene.collection, obj)
    # move to the new
    collection.objects.link(obj)

def move_collection_to_collection( destination, collection):
    """Moves a collection to another collection"""
    # remove from all collections
    for scene in bpy.data.scenes:
        remove_collection_from_collection(scene.collection, collection)
    # move to the new
    destination.children.link(collection)

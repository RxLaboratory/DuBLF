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

from . import( # DuBLF files
    addons,
    animation,
    collections,
    context,
    fs,
    handlers,
    materials,
    ops,
    rigging,
    rna,
    shapeKeys,
    ui,
    image,
    geo
)

from . import ( # pylint: disable=import-error # DuPYF Files
    debug,
    oca,
    updater,
)

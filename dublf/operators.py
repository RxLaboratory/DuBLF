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

import webbrowser
import bpy
import sys
from time import time
import textwrap 
from .updater import checkUpdate
from .ui import showMessageBox

class OpenURL(bpy.types.Operator):
    bl_idname = "dublf.openurl"
    bl_label = ""
    
    url: bpy.props.StringProperty(
        default= ''
        )
    
    def execute(self, context):
        webbrowser.open(self.url)
        return {'FINISHED'}

class UpdateBox(bpy.types.Operator):
    bl_idname = "dublf.updatebox"
    bl_label = "Update available"
    bl_icon = "INFO"

    addonModuleName: bpy.props.StringProperty(
        default = ""
    )
 
    toolName: bpy.props.StringProperty(
        default = 'Tool',
        description = "The name of the tool",
        name = "Tool Name"
    )

    newVersion: bpy.props.StringProperty(
        default = ''
    )

    descr: bpy.props.StringProperty(
        default = '',
        name = "Description"
    )

    currentVersion: bpy.props.StringProperty(
        default = "0.0.0"
    )

    downloadURL: bpy.props.StringProperty(
        default = "http://rxlaboratory.org"
    )

    changelogURL: bpy.props.StringProperty(
        default = ""
    )

    donateURL: bpy.props.StringProperty(
        default = "http://donate.rxlab.info"
    )
 
    updateAPIURL: bpy.props.StringProperty(
        default= "https://api.rxlab.io"
    )

    preRelease: bpy.props.BoolProperty(
        default=False
    )

    discreet: bpy.props.BoolProperty(
        default=False
    )

    def execute(self, context):
        if self.addonModuleName != "":
            addon = context.preferences.addons[self.addonModuleName]
            addonPrefs = addon.preferences
            addonPrefs.last_update_check = int(time())

        return {'FINISHED'}
 
    def invoke(self, context, event):
        if self.newVersion == "":
            addonPrefs = None
            # Get update info
            if self.addonModuleName != "":
                addon = context.preferences.addons[self.addonModuleName]
                mod = sys.modules.get(addon.module)
                addonInfo = mod.bl_info
                self.toolName = addonInfo["name"]
                version = addonInfo["version"]
                self.currentVersion = str(version[0]) + "." + str(version[1]) + "." + str(version[2])
                
                if self.discreet:
                    addonPrefs = addon.preferences
                    if not addonPrefs.check_updates:
                        return {'CANCELLED'}
                    now = time()
                    last = addonPrefs.last_update_check
                    if now - last < 86400:
                        return {'CANCELLED'}

            info = checkUpdate( self.updateAPIURL, self.toolName, self.currentVersion, "blender", bpy.app.version_string, self.preRelease)
            if not info["update"]:
                if not self.discreet:
                    showMessageBox("Up-to-date!", self.toolName)
                return {'CANCELLED'}

            self.newVersion = info["version"]
            if 'donateURL' in info:
                if info['donateURL'] != "":
                    self.donateURL = info['donateURL']
            if 'changelogURL' in info:
                if info['changelogURL'] != "":
                    self.changelogURL = info['changelogURL']
            if 'downloadURL' in info:
                if info['downloadURL'] != "":
                    self.downloadURL = info['downloadURL']
            self.descr = info['description']

        return context.window_manager.invoke_props_dialog(self, width=400)
 
    def draw(self, context):
        layout = self.layout
        layout.label(text="New " + self.toolName + ", version " + self.newVersion)
        layout.separator()

        wrapper = textwrap.TextWrapper(width=70)
        lines = self.descr.split("\n")
        descrList = []
        for line in lines:
            descrList += wrapper.wrap(line)
        
        #Now in the panel:
        for text in descrList: 
            row = layout.row(align = True)
            row.alignment = 'EXPAND'
            row.label(text=text)

        layout.separator()
        layout.label(text="Current version: " + self.currentVersion)
        
        if self.downloadURL != "":
            layout.operator(OpenURL.bl_idname, text="Download", icon="URL").url = self.downloadURL
        if self.changelogURL != "":
            layout.operator(OpenURL.bl_idname, text="Changelog", icon="PRESET").url = self.changelogURL
        if self.donateURL != "":
            layout.operator(OpenURL.bl_idname, text="Donate", icon="HEART").url = self.donateURL

classes = (
    OpenURL,
    UpdateBox
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
 
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
 
if __name__ == "__main__":
    register()

    bpy.ops.dublf.updatebox('INVOKE_DEFAULT', descr = """A Nice description
    for a new tool!""", downloadURL = "http://rxlaboratory.org", changelogURL = "http://rxlaboratory.org")

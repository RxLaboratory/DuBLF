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
import platform
from time import time
import textwrap 
from .updater import checkUpdate
from .ui import showMessageBox

class DUBLF_OT_ReportIssue(bpy.types.Operator):
    bl_idname = "dublf.reportIssue"
    bl_label = "Bug Report / Feature Request"
    bl_icon = "ERROR"

    addonName = ''
    toolName = "Tool"
    toolVersion = '0.0.0'
    osName = ''
    osVersion = ''
    hostName = "Blender"
    hostVersion = ''
    reportURL = "https://rxlaboratory.org/issues"

    def execute(self, context):

        # Get tool name and version
        if self.__class__.addonName != "":
            addon = context.preferences.addons[self.__class__.addonName]
            mod = sys.modules.get(addon.module)
            addonInfo = mod.bl_info
            self.__class__.toolName = addonInfo["name"]
            version = addonInfo["version"]
            self.__class__.toolVersion = str(version[0]) + "." + str(version[1]) + "." + str(version[2])

        # Get Environment info
        self.__class__.hostVersion = bpy.app.version_string
        # Check os
        self.__class__.osName  = platform.system()
        if self.__class__.osName == "Darwin":
            self.__class__.osName = "mac"
        self.__class__.osVersion = platform.version()

        webbrowser.open( self.reportURL +
                        '?rx-tool=' + self.__class__.toolName +
                        '&rx-tool-version=' + self.__class__.toolVersion +
                        '&rx-os=' + self.__class__.osName +
                        '&rx-os-version=' + self.__class__.osVersion +
                        '&rx-host=' + self.__class__.hostName +
                        '&rx-host-version=' + self.__class__.hostVersion )

        return {'FINISHED'}

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

    openURLOp = "dublf.openurl"
    addonName = ""
    toolName = "Tool"
    newVersion = ''
    descr = "Description"
    currentVersion = "0.0.0"
    downloadURL = "http://rxlaboratory.org/"
    changelogURL = ""
    donateURL = "http://donate.rxlab.info"
    updateAPIURL = "https://api.rxlab.io"
    preRelease = False

    showDialog = True

    discreet: bpy.props.BoolProperty(
        default=False
    )

    def execute(self, context):

        if self.__class__.addonName != "":
            addon = context.preferences.addons[self.__class__.addonName]
            addonPrefs = addon.preferences
            addonPrefs.last_update_check = int(time())
            # Force save prefs
            addonPrefs.is_dirty = True
            bpy.ops.wm.save_userpref()

        return {'FINISHED'}
 
    def invoke(self, context, event):
       
        if self.__class__.newVersion == "":
            addonPrefs = None

            # Get update info
            if self.__class__.addonName != "":
                addon = context.preferences.addons[self.__class__.addonName]
                mod = sys.modules.get(addon.module)
                addonInfo = mod.bl_info
                self.__class__.toolName = addonInfo["name"]
                version = addonInfo["version"]
                self.__class__.currentVersion = str(version[0]) + "." + str(version[1]) + "." + str(version[2])

                if self.discreet:
                    addonPrefs = addon.preferences
                    if not addonPrefs.check_updates:
                        self.showDialog = False
                        return {'CANCELLED'}
                    now = time()
                    last = addonPrefs.last_update_check

                    if now - last < 86400:
                        self.showDialog = False
                        return {'CANCELLED'}
                    
                    addonPrefs.last_update_check = int(now)
                    # Force save prefs
                    addonPrefs.is_dirty = True
                    bpy.ops.wm.save_userpref()
                    self.showDialog = True

            info = checkUpdate( self.__class__.updateAPIURL, self.__class__.toolName, self.__class__.currentVersion, "blender", bpy.app.version_string, self.__class__.preRelease)
            if not info["update"]:
                if not self.discreet:
                    showMessageBox("Up-to-date!", self.__class__.toolName)
                return {'CANCELLED'}

            self.__class__.newVersion = info["version"]
            if 'donateURL' in info:
                if info['donateURL'] != "":
                    self.__class__.donateURL = info['donateURL']
            if 'changelogURL' in info:
                if info['changelogURL'] != "":
                    self.__class__.changelogURL = info['changelogURL']
            if 'downloadURL' in info:
                if info['downloadURL'] != "":
                    self.__class__.downloadURL = info['downloadURL']
            self.__class__.descr = info['description']

        if self.showDialog or not self.discreet:
            return context.window_manager.invoke_props_dialog(self, width=400)
        else:
            return {'CANCELLED'}
 
    def draw(self, context):
        layout = self.layout
        layout.label(text="New " + self.__class__.toolName + ", version " + self.__class__.newVersion)
        layout.separator()

        wrapper = textwrap.TextWrapper(width=70)
        lines = self.__class__.descr.split("\n")
        descrList = []
        for line in lines:
            descrList += wrapper.wrap(line)
        
        # Now in the panel:
        for text in descrList: 
            row = layout.row(align = True)
            row.alignment = 'EXPAND'
            row.label(text=text)

        layout.separator()
        layout.label(text="Current version: " + self.__class__.currentVersion)
        
        if self.__class__.downloadURL != "":
            layout.operator(self.__class__.openURLOp, text="Download", icon="URL").url = self.__class__.downloadURL
        if self.__class__.changelogURL != "":
            layout.operator(self.__class__.openURLOp, text="Changelog", icon="PRESET").url = self.__class__.changelogURL
        if self.__class__.donateURL != "":
            layout.operator(self.__class__.openURLOp, text="Donate", icon="HEART").url = self.__class__.donateURL

from os import path
import subprocess
import sys

import wx

import pcbnew

def check_requirements(*packages):
    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        wx.MessageDialog(None, "Error: Missing python dependencies:\n\n{}.".format('\n'.join(missing)),
                "Missing Dependencies").ShowModal()
        return False

    else:
        return True

class MeshPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = 'Mesh generator'
        self.category = 'Modify PCB'
        self.description = 'Creates security mesh traces on a PCB'
        self.icon_file_name = path.join(path.dirname(__file__), 'mesh_plugin_icon.png')
        self.show_toolbar_button = True

    def Run(self):
        if not check_requirements('pyclipper'):
            return

        from .mesh_dialog import show_dialog
        show_dialog(pcbnew.GetBoard())

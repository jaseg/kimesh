import os.path

import pcbnew

from .mesh_dialog import show_dialog

class MeshPlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = 'Mesh generator'
        self.category = 'Modify PCB'
        self.description = 'Creates security mesh traces on a PCB'
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'mesh_plugin_icon.png')
        self.show_toolbar_button = True

    def Run(self):
        import pcbnew
        show_dialog(pcbnew.GetBoard())

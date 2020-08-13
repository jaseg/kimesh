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
        if 'win' not in sys.platform:
            wx.MessageDialog(None, "Error: Missing python dependencies {}.".format(', '.join(missing)),
                    "Missing Dependencies").ShowModal()
            return False
        
        else:
            msg = 'The following python dependencies are missing:\n\n' + '\n'.join(missing) +\
                  '\n\nShould we go ahead and install these missing dependencies into the plugin directory?'
            dialog = wx.MessageDialog(None, msg, caption='Error: Missing dependencies', style=wx.YES_NO | wx.NO_DEFAULT)
            dialog.SetYesNoLabels("Install missing dependencies", "Cancel")
            if dialog.ShowModal() == wx.ID_YES:
                for dep in packages:
                    proc = subprocess.Popen(
                            "pip install --target deps {} --no-use-pep517 --only-binary :all: --platform win_amd64"\
                                    .format(dep).split(),
                            cwd=path.dirname(__file__),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
                    (stdout, stderr) = proc.communicate()
                    if proc.returncode != 0:
                        wx.MessageDialog(None, "Error installing dependencies:\n\n{}\n{}".format(stdout, stderr),
                                "Installation Error").ShowModal()
                        return False

                sys.path.append(path.abspath(path.join(path.dirname(__file__), 'deps')))

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

import wx
import mesh_plugin_dialog
import pcbnew
from collections import defaultdict
import pyclipper

# Implementing MainDialog
class MeshPluginMainDialog(mesh_plugin_dialog.MainDialog):
    def __init__(self, board):
        mesh_plugin_dialog.MainDialog.__init__(self, None)
        self.board = board

        self.m_cancelButton.Bind(wx.EVT_BUTTON, self.quit)
        self.m_removeButton.Bind(wx.EVT_BUTTON, self.tearup_mesh)
        self.m_generateButton.Bind(wx.EVT_BUTTON, self.generate_mesh)
        self.m_net_prefix.Bind(wx.EVT_TEXT, self.update_net_label)
        self.m_traceSpin.Bind(wx.EVT_SPIN_UP, lambda evt: self.spin(self.m_traceInput, 1.0))
        self.m_traceSpin.Bind(wx.EVT_SPIN_DOWN, lambda evt: self.spin(self.m_traceInput, -1.0))
        self.m_spaceSpin.Bind(wx.EVT_SPIN_UP, lambda evt: self.spin(self.m_spaceInput, 1.0))
        self.m_spaceSpin.Bind(wx.EVT_SPIN_DOWN, lambda evt: self.spin(self.m_spaceInput, -1.0))

        self.tearup_confirm_dialog = wx.MessageDialog(self, "", style=wx.YES_NO | wx.NO_DEFAULT)

        self.nets = { str(wxs) for wxs, netinfo in board.GetNetsByName().items() }
        self.update_net_label(None)

        self.SetMinSize(self.GetSize())

    def spin(self, le_input, delta):
        try:
            current = float(le_input.Value)
            current += delta
            le_input.Value = '{:.03f}'.format(current)
        except ValueError:
            pass

    def get_matching_nets(self):
        prefix = self.m_net_prefix.Value
        return { net for net in self.nets if net.startswith(prefix) }

    def tearup_mesh(self, evt):
        matching = self.get_matching_nets()

        if not str(self.m_net_prefix.Value):
            message = "You have set an empty net prefix. This will match ALL {} nets on the board. Do you really want to tear up all autorouted tracks? This cannot be undone!"

        else:
            message = "Do you really want to tear up all autorouted traces of the {} matching nets on this board? This step cannot be undone!"

        message = message.format(len(matching)) + "\n\nMatching nets:\n" + ", ".join(
                '""' if not netname else (netname[:16] + '...' if len(netname) > 16 else netname)
                for netname in (sorted(matching)[:5] + ['...'] if len(matching) > 5 else [])
        )
        self.tearup_confirm_dialog.SetMessage(message)
        self.tearup_confirm_dialog.SetYesNoLabels("Tear up {} nets".format(len(matching)), "Close")

        if self.tearup_confirm_dialog.ShowModal() == wx.ID_YES:
            for track in self.board.GetTracks():
                if not (track.GetStatus() & pcbnew.TRACK_AR):
                    continue

                if not track.GetNet().GetNetname() in matching:
                    continue

                board.Remove(track)

    def generate_mesh(self, evt):
        nets = self.get_matching_nets()

        pads = defaultdict(lambda: [])
        for module in self.board.GetModules():
            for pad in module.Pads():
                net = pad.GetNetname()
                if net in nets:
                    pads[net].append(pad)

        for net in nets:
            if net not in pads:
                return wx.MessageDialog(self, "Error: No connection pads found for net {}.".format(net)).ShowModal()
            
            if len(pads[net]) == 1:
                return wx.MessageDialog(self, "Error: Only one of two connection pads found for net {}.".format(net)).ShowModal()

            if len(pads[net]) > 2:
                return wx.MessageDialog(self, "Error: More than two connection pads found for net {}.".format(net)).ShowModal()

        eco1_id = self.board.GetLayerID('Eco1.User')
        mesh_zones = []
        for drawing in self.board.GetDrawings():
            if drawing.GetLayer() == eco1_id:
                mesh_zones.append(drawing)

        if not mesh_zones:
                return wx.MessageDialog(self, "Error: Could not find any mesh zones on the Eco1.User layer.").ShowModal()

        for zone in mesh_zones:
            anchors = []
            for module in self.board.GetModules():
                for foo in module.GraphicalItems():
                    if not isinstance(foo, pcbnew.TEXTE_MODULE):
                        continue

                    if foo.GetText() == "mesh_anchor":
                        anchors.append(module)
                        break

            if not anchors:
                return wx.MessageDialog(self, "Error: No anchor found for mesh zone centered on {:.3f}, {:.3f} mm".format(
                    zone.GetCenter().x / pcbnew.IU_PER_MM, zone.GetCenter().y / pcbnew.IU_PER_MM
                            )).ShowModal()
            if len(anchors) > 1:
                return wx.MessageDialog(self, "Error: Currently, only a single anchor is supported.").ShowModal()

            self.generate_mesh(zone, anchors)

    def generate_mesh(self, zone, anchors):
        anchor, = anchors


    def update_net_label(self, evt):
        self.m_netLabel.SetLabel('{} matching nets'.format(len(self.get_matching_nets())))

    def quit(self, evt):
        self.Destroy()

def show_dialog(board):
    dialog = MeshPluginMainDialog(board)
    dialog.ShowModal()
    return dialog

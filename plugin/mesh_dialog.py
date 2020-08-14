from collections import defaultdict
from dataclasses import dataclass

import wx

import pcbnew

import shapely
from shapely.geometry import polygon
from shapely import affinity

from . import mesh_plugin_dialog

class GeneratorError(ValueError):
    pass

class AbortError(SystemError):
    pass

@dataclass
class GeneratorSettings:
    mesh_angle:  float = 0.0   # deg
    trace_width: float = 0.127 # mm
    space_width: float = 0.127 # mm
    anchor_exit: float = 0.0   # deg
    num_traces:  int   = 2
    offset_x:    float = 0.0   # mm
    offset_y:    float = 0.0   # mm

class MeshPluginMainDialog(mesh_plugin_dialog.MainDialog):
    def __init__(self, board):
        mesh_plugin_dialog.MainDialog.__init__(self, None)
        self.board = board

        self.m_cancelButton.Bind(wx.EVT_BUTTON, self.quit)
        self.m_removeButton.Bind(wx.EVT_BUTTON, self.tearup_mesh)
        self.m_generateButton.Bind(wx.EVT_BUTTON, self.generate_mesh)
        self.m_net_prefix.Bind(wx.EVT_TEXT, self.update_net_label)

        self.tearup_confirm_dialog = wx.MessageDialog(self, "", style=wx.YES_NO | wx.NO_DEFAULT)

        self.nets = { str(wxs) for wxs, netinfo in board.GetNetsByName().items() }
        self.update_net_label(None)

        self.SetMinSize(self.GetSize())

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
            self.tearup_mesh()

    def tearup_mesh(self):
        for track in self.board.GetTracks():
            if not (track.GetStatus() & pcbnew.TRACK_AR):
                continue

            if not track.GetNet().GetNetname() in matching:
                continue

            board.Remove(track)

    def generate_mesh(self, evt):
        try:
            settings = GeneratorSettings(
                mesh_angle  = float(self.m_angleSpin.Value),
                trace_width = float(self.m_traceSpin.Value),
                space_width = float(self.m_spaceSpin.Value),
                anchor_exit = float(self.m_exitSpin.Value),
                num_traces  = int(self.m_traceCountSpin.Value),
                offset_x    = float(self.m_offsetXSpin.Value),
                offset_y    = float(self.m_offsetYSpin.Value))
        except ValueError as e:
            return wx.MessageDialog(self, "Invalid input value: {}.".format(e), "Invalid input").ShowModal()

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

            try:
                def warn(msg):
                    dialog = wx.MessageDialog(self, msg + '\n\nDo you want to abort mesh generation?',
                            "Mesh Generation Warning").ShowModal()
                    dialog = wx.MessageDialog(self, "", style=wx.YES_NO | wx.NO_DEFAULT)
                    dialog.SetYesNoLabels("Abort", "Ignore and continue")

                    if self.tearup_confirm_dialog.ShowModal() == wx.ID_YES:
                        raise AbortError()

                self.generate_mesh_backend(zone, anchors, warn=warn)

            except GeneratorError as e:
                return wx.MessageDialog(self, str(e), "Mesh Generation Error").ShowModal()
            except AbortError:
                pass

    def poly_set_to_shapely(self, poly_set):
        for i in range(poly_set.OutlineCount()):
            outline = poly_set.Outline(i)

            outline_points = []
            for j in range(outline.PointCount()):
                point = outline.CPoint(j)
                outline_points.append((pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)))
            yield polygon.LinearRing(outline_points)

    def generate_mesh_backend(self, zone, anchors, warn=lambda s: None, settings=GeneratorSettings()):
        anchor, = anchors

        anchor_outlines = list(self.poly_set_to_shapely(anchor.GetBoundingPoly()))
        if len(anchor_outlines) == 0:
            raise GeneratorError('Could not find any outlines for anchor {}'.format(anchor.GetReference()))
        if len(anchor_outlines) > 1:
            warn('Anchor {} has multiple outlines. Using first outline for trace start.')

        zone_outlines = list(self.poly_set_to_shapely(zone.GetPolyShape()))
        if len(zone_outlines) == 0:
            raise GeneratorError('Could not find any outlines for mesh zone.')
        if len(zone_outlines) > 1:
            raise GeneratorError('Mesh zone has too many outlines (has {}, should have one).'.format(len(zone_outlines)))
        zone_outline, *_rest = zone_outlines
        
        mesh_origin = zone_outline.centroid
        width_per_trace = settings.trace_width + settings.space_width
        grid_cell_width = width_per_trace * settings.num_traces

        zone_outline_rotated = affinity.rotate(zone_outline, -settings.mesh_angle, origin=mesh_origin)
        bbox = zone_outline_rotated.bounds

        grid_origin = (bbox[0] + settings.offset_x - grid_cell_width, bbox[1] + settings.offset_y - grid_cell_width)
        grid_rows = int((bbox[3] - grid_origin[1]) / grid_cell_width + 2)
        grid_cols = int((bbox[2] - grid_origin[0]) / grid_cell_width + 2)
        print(f'generating grid of size {grid_rows} * {grid_cols}')

        grid = []
        for y in range(grid_rows):
            row = []
            for x in range(grid_cols):
                cell = polygon.LinearRing([(0, 0), (0, 1), (1, 1), (1, 0)])
                cell = affinity.scale(cell, grid_cell_width, grid_cell_width, origin=(0, 0))
                cell = affinity.translate(cell, mesh_origin.x + x*grid_cell_width, mesh_origin.y + y*grid_cell_width)
                cell = affinity.rotate(cell, settings.mesh_angle, origin=mesh_origin)
                row.append(cell)
            grid.append(row)
            break

        for row in grid:
            for cell in row:
                poly = pcbnew.DRAWSEGMENT()
                poly.SetLayer(self.board.GetLayerID('Eco2.User'))
                poly.SetShape(pcbnew.S_POLYGON)
                poly.SetWidth(0)
                self.board.Add(poly)
                s = poly.GetPolyShape()
                s.NewOutline()
                for x, y in zip(*cell.xy):
                    s.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
                    print('OUTLINE POINT', x, y)
            break

        pcbnew.Refresh()
        #self.tearup_mesh()
        # TODO generate

    def update_net_label(self, evt):
        self.m_netLabel.SetLabel('{} matching nets'.format(len(self.get_matching_nets())))

    def quit(self, evt):
        self.Destroy()

def show_dialog(board):
    dialog = MeshPluginMainDialog(board)
    dialog.ShowModal()
    return dialog

from collections import defaultdict
from dataclasses import dataclass
from contextlib import contextmanager
import textwrap
import random

import wx

import pcbnew

import matplotlib.cm
import shapely
from shapely import geometry
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

                self.generate_mesh_backend(zone, anchors, warn=warn, settings=settings)

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
            yield polygon.Polygon(outline_points)

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
        
        width_per_trace = settings.trace_width + settings.space_width
        grid_cell_width = width_per_trace * settings.num_traces

        zone_outline_rotated = affinity.rotate(zone_outline, -settings.mesh_angle, origin=zone_outline.centroid)
        bbox = zone_outline_rotated.bounds

        grid_origin = (bbox[0] + settings.offset_x - grid_cell_width, bbox[1] + settings.offset_y - grid_cell_width)
        grid_rows = int((bbox[3] - grid_origin[1]) / grid_cell_width + 2)
        grid_cols = int((bbox[2] - grid_origin[0]) / grid_cell_width + 2)
        print(f'generating grid of size {grid_rows} * {grid_cols}')

        grid = []
        for y in range(grid_rows):
            row = []
            for x in range(grid_cols):
                cell = polygon.Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
                cell = affinity.scale(cell, grid_cell_width, grid_cell_width, origin=(0, 0))
                cell = affinity.translate(cell, grid_origin[0] + x*grid_cell_width, grid_origin[1] + y*grid_cell_width)
                cell = affinity.rotate(cell, settings.mesh_angle, origin=zone_outline.centroid)
                row.append(cell)
            grid.append(row)

        exit_line = affinity.rotate(geometry.LineString([(0,0), (0,-100000)]), settings.anchor_exit, origin=(0, 0))
        exit_line = affinity.translate(exit_line, anchor_outlines[0].centroid.x, anchor_outlines[0].centroid.y)
        possible_exits = []
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if any(ol.overlaps(cell) for ol in anchor_outlines): # cell lies on outline
                    if exit_line.crosses(cell): # cell lies on exit line
                        possible_exits.append((cell, (x, y)))
        if len(possible_exits) == 0:
            raise GeneratorError('Cannot find an exit. This is a bug, please report.')
        exit_cell = possible_exits[0] # might overlap multiple if not orthogonal

        num_valid = 0
        with DebugOutput('/mnt/c/Users/jaseg/shared/test.svg') as dbg:
            dbg.add(zone_outline, color='#00000020')

            for y, row in enumerate(grid):
                for x, cell in enumerate(row):
                    if zone_outline.contains(cell):
                        if cell == exit_cell[0]:
                            color = '#ff00ff80'
                        elif any(ol.overlaps(cell) for ol in anchor_outlines):
                            color = '#ffff0080'
                        elif any(ol.contains(cell) for ol in anchor_outlines):
                            color = '#ff000080'
                        else:
                            num_valid += 1
                            color = '#00ff0080'
                    elif zone_outline.overlaps(cell):
                        color = '#ffff0080'
                    else:
                        color = '#ff000080'
                    dbg.add(cell, color=color)

            for foo in anchor_outlines:
                dbg.add(foo, color='#0000ff00', stroke_width=0.05, stroke_color='#000000ff')

        def is_valid(cell):
            if not zone_outline.contains(cell):
                return False
            if any(ol.overlaps(cell) for ol in anchor_outlines):
                return False
            if any(ol.contains(cell) for ol in anchor_outlines):
                return False
            return True

        def iter_neighbors(x, y):
            if x > 0:
                yield x-1, y
            if x < grid_cols:
                yield x+1, y
            if y > 0:
                yield x, y-1
            if y < grid_rows:
                yield x, y+1

        def random_iter(it):
            l = list(it)
            random.shuffle(l)
            yield from l

        not_visited = { (x, y) for x in range(grid_cols) for y in range(grid_rows) if is_valid(grid[y][x]) }
        num_to_visit = len(not_visited)
        with DebugOutput('/mnt/c/Users/jaseg/shared/test2.svg') as dbg:
            dbg.add(zone_outline, color='#00000020')
            
            x, y = exit_cell[1]
            visited = 0
            stack = []
            while not_visited:
                for n_x, n_y in random_iter(iter_neighbors(x, y)):
                    if (n_x, n_y) in not_visited:
                        dbg.add(grid[n_y][n_x], color=virihex(visited, max=num_to_visit))
                        stack.append((x, y))
                        not_visited.remove((n_x, n_y))
                        visited += 1
                        x, y = n_x, n_y
                        break
                else:
                    *stack, (x, y) = stack

            for foo in anchor_outlines:
                dbg.add(foo, color='#0000ff00', stroke_width=0.05, stroke_color='#000000ff')



        #pcbnew.Refresh()
        #self.tearup_mesh()
        # TODO generate

    def update_net_label(self, evt):
        self.m_netLabel.SetLabel('{} matching nets'.format(len(self.get_matching_nets())))

    def quit(self, evt):
        self.Destroy()

def virihex(val, max=1.0, alpha=1.0):
    r, g, b, _a = matplotlib.cm.viridis(val/max)
    r, g, b, a = [ int(round(0xff*c)) for c in [r, g, b, alpha] ]
    return f'#{r:02x}{g:02x}{b:02x}{a:02x}'

@contextmanager
def DebugOutput(filename):
    with open(filename, 'w') as f:
        wrapper = DebugOutputWrapper(f)
        yield wrapper
        wrapper.save()

class DebugOutputWrapper:
    def __init__(self, f):
        self.f = f
        self.objs = []

    def add(self, obj, color=None, stroke_width=0, stroke_color=None):
        self.objs.append((obj, (color, stroke_color, stroke_width)))

    def gen_svg(self, obj, fill_color=None, stroke_color=None, stroke_width=None):
        fill_color = fill_color or '#ff0000aa'
        stroke_color = stroke_color or '#000000ff'
        stroke_width = 0 if stroke_width is None else stroke_width

        exterior_coords = [ ["{},{}".format(*c) for c in obj.exterior.coords] ]
        interior_coords = [ ["{},{}".format(*c) for c in interior.coords] for interior in obj.interiors ]
        path = " ".join([
            "M {0} L {1} z".format(coords[0], " L ".join(coords[1:]))
            for coords in exterior_coords + interior_coords])
        return (f'<path fill-rule="evenodd" fill="{fill_color}" stroke="{stroke_color}" '
                f'stroke-width="{stroke_width}" opacity="0.6" d="{path}" />')
    
    def save(self, margin:'unit'=5, scale:'px/unit'=10):
        #specify margin in coordinate units
        margin = 5

        bboxes = [ list(obj.bounds) for obj, _style in self.objs ]
        min_x = min( bbox[0] for bbox in bboxes ) - margin
        min_y = min( bbox[1] for bbox in bboxes ) - margin
        max_x = max( bbox[2] for bbox in bboxes ) + margin
        max_y = max( bbox[3] for bbox in bboxes ) + margin

        width = max_x - min_x
        height = max_y - min_y

        props = {
            'version': '1.1',
            'baseProfile': 'full',
            'width': '{width:.0f}px'.format(width = width*scale),
            'height': '{height:.0f}px'.format(height = height*scale),
            'viewBox': '%.1f,%.1f,%.1f,%.1f' % (min_x, min_y, width, height),
            'xmlns': 'http://www.w3.org/2000/svg',
            'xmlns:ev': 'http://www.w3.org/2001/xml-events',
            'xmlns:xlink': 'http://www.w3.org/1999/xlink'
        }

        self.f.write(textwrap.dedent(r'''
            <?xml version="1.0" encoding="utf-8" ?>
            <svg {attrs:s}>
            {data}
            </svg>
        ''').format(
            attrs = ' '.join(['{key:s}="{val:s}"'.format(key = key, val = props[key]) for key in props]),
            data = '\n'.join(self.gen_svg(obj, *style) for obj, style in self.objs)
        ).strip())

def show_dialog(board):
    dialog = MeshPluginMainDialog(board)
    dialog.ShowModal()
    return dialog

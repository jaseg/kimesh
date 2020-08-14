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
        grid_cell_width = width_per_trace * settings.num_traces * 2

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
                yield x-1, y, 0b0100
            if x < grid_cols:
                yield x+1, y, 0b0001
            if y > 0:
                yield x, y-1, 0b1000
            if y < grid_rows:
                yield x, y+1, 0b0010

        def reciprocal(mask):
            return {
                    0b0001: 0b0100,
                    0b0010: 0b1000,
                    0b0100: 0b0001,
                    0b1000: 0b0010
                    }[mask]

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
            key = 0
            stack = []
            while not_visited or stack:
                for n_x, n_y, mask in random_iter(iter_neighbors(x, y)):
                    if (n_x, n_y) in not_visited:
                        dbg.add(grid[n_y][n_x], color=virihex(visited, max=num_to_visit), opacity=0.2)
                        key |= mask
                        stack.append((x, y, key))
                        not_visited.remove((n_x, n_y))
                        visited += 1
                        x, y, key = n_x, n_y, reciprocal(mask)
                        break
                else:
                    for segment in Pattern.render(key, settings.num_traces):
                        segment = affinity.scale(segment, grid_cell_width, grid_cell_width, origin=(0, 0))
                        segment = affinity.translate(segment, grid_origin[0] + x*grid_cell_width, grid_origin[1] + y*grid_cell_width)
                        dbg.add(segment, stroke_width=settings.trace_width, color='#ff000000', stroke_color='#ff000080')
                    *stack, (x, y, key) = stack

            for foo in anchor_outlines:
                dbg.add(foo, color='#0000ff00', stroke_width=0.05, stroke_color='#000000ff')



        #pcbnew.Refresh()
        #self.tearup_mesh()
        # TODO generate

    def update_net_label(self, evt):
        self.m_netLabel.SetLabel('{} matching nets'.format(len(self.get_matching_nets())))

    def quit(self, evt):
        self.Destroy()


class Pattern:
    @staticmethod
    def render(key, n):
        yield from Pattern.LUT[key](n)
    
    def draw_I(n):
        for i in range(2*n):
            sp = (i+0.5) * (1/(2*n))
            yield geometry.LineString([(sp, 0), (sp, 1)])

    def draw_U(n):
        for i in range(n):
            sp = (i+0.5) * (1/(2*n))
            yield geometry.LineString([(sp, 0), (sp, 1-sp), (1-sp, 1-sp), (1-sp, 0)])

    def draw_L(n):
        for i in range(2*n):
            sp = (i+0.5) * (1/(2*n))
            yield geometry.LineString([(sp, 0), (sp, 1-sp), (1, 1-sp)])
    
    def draw_T(n):
        for i in range(n):
            sp = (i+0.5) * (1/(2*n))
            yield geometry.LineString([(0, sp), (1, sp)])
            yield geometry.LineString([(0, 1-sp), (sp, 1-sp), (sp, 1)])
            yield geometry.LineString([(1-sp, 1), (1-sp, 1-sp), (1, 1-sp)])

    def draw_X(n):
        for i in range(n):
            sp = (i+0.5) * (1/(2*n))
            yield geometry.LineString([(0, sp), (sp, sp), (sp, 0)])
            yield geometry.LineString([(1-sp, 0), (1-sp, sp), (1, sp)])
            yield geometry.LineString([(0, 1-sp), (sp, 1-sp), (sp, 1)])
            yield geometry.LineString([(1-sp, 1), (1-sp, 1-sp), (1, 1-sp)])

    def rotate(pattern, deg):
        def wrapper(n):
            for segment in pattern(n):
                yield affinity.rotate(segment, deg, origin=(0.5, 0.5))
        return wrapper

    def raise_error(n):
        return []
        raise ValueError('Tried to render invalid cell. This is a bug.')

    LUT = {
            0b0000: raise_error,
            0b0001: rotate(draw_U, 90),
            0b0010: rotate(draw_U, 180),
            0b0011: rotate(draw_L, 90),
            0b0100: rotate(draw_U, -90),
            0b0101: rotate(draw_I, -90),
            0b0110: rotate(draw_L, 180),
            0b0111: draw_T,
            0b1000: draw_U,
            0b1001: draw_L,
            0b1010: draw_I,
            0b1011: rotate(draw_T, -90),
            0b1100: rotate(draw_L, -90),
            0b1101: rotate(draw_T, 180),
            0b1110: rotate(draw_T, 90),
            0b1111: draw_X
    }


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

    def add(self, obj, color=None, stroke_width=0, stroke_color=None, opacity=1.0):
        self.objs.append((obj, (color, stroke_color, stroke_width, opacity)))

    def gen_svg(self, obj, fill_color=None, stroke_color=None, stroke_width=None, opacity=1.0):
        fill_color = fill_color or '#ff0000aa'
        stroke_color = stroke_color or '#000000ff'
        stroke_width = 0 if stroke_width is None else stroke_width

        if isinstance(obj, polygon.Polygon):
            exterior_coords = [ ["{},{}".format(*c) for c in obj.exterior.coords] ]
            interior_coords = [ ["{},{}".format(*c) for c in interior.coords] for interior in obj.interiors ]
            all_coords = exterior_coords + interior_coords
            path = " ".join([
                "M {0} L {1} z".format(coords[0], " L ".join(coords[1:]))
                for coords in all_coords])
        elif isinstance(obj, geometry.LineString):
            all_coords = [ ["{},{}".format(*c) for c in obj.coords] ]
            path = " ".join([
                "M {0} L {1}".format(coords[0], " L ".join(coords[1:]))
                for coords in all_coords])
        else:
            raise ValueError(f'Unhandled shapely object type {type(obj)}')
        return (f'<path fill-rule="evenodd" fill="{fill_color}" opacity="{opacity}" stroke="{stroke_color}" '
                f'stroke-width="{stroke_width}" d="{path}" />')
    
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

from collections import defaultdict
from dataclasses import dataclass
from contextlib import contextmanager
import textwrap
import random
import math
from itertools import count, islice

import wx

import pcbnew

import matplotlib.cm
import shapely
from shapely import geometry
from shapely.geometry import polygon
from shapely import affinity
import shapely.ops

from . import mesh_plugin_dialog

class GeneratorError(ValueError):
    pass

class AbortError(SystemError):
    pass

@dataclass
class GeneratorSettings:
    mesh_angle:     float = 0.0   # deg
    trace_width:    float = 0.127 # mm
    space_width:    float = 0.127 # mm
    anchor_exit:    float = 0.0   # deg
    num_traces:     int   = 2
    offset_x:       float = 0.0   # mm
    offset_y:       float = 0.0   # mm
    chamfer:        float = 0.0   # unit fraction
    target_layer_id:int   = 0     # kicad layer id, populated later
    mask_layer_id:  int   = 0     # kicad layer id, populated later
    random_seed:    str   = None
    randomness:     float = 1.0

class MeshPluginMainDialog(mesh_plugin_dialog.MainDialog):
    def __init__(self, board):
        mesh_plugin_dialog.MainDialog.__init__(self, None)
        self.board = board

        self.m_cancelButton.Bind(wx.EVT_BUTTON, self.quit)
        self.m_removeButton.Bind(wx.EVT_BUTTON, self.confirm_tearup_mesh)
        self.m_removeAllButton.Bind(wx.EVT_BUTTON, self.confirm_tearup_mesh_all)
        self.m_generateButton.Bind(wx.EVT_BUTTON, self.generate_mesh)
        self.m_net_prefix.Bind(wx.EVT_TEXT, self.update_net_label)
        # currently, BOARD.Remove() is b0rked and kicad crashes. Disable function for now.
        self.m_removeButton.Disable()
        self.m_removeAllButton.Disable()

        self.tearup_confirm_dialog = wx.MessageDialog(self, "", style=wx.YES_NO | wx.NO_DEFAULT)

        self.nets = { str(wxs) for wxs, netinfo in board.GetNetsByName().items() }
        self.update_net_label(None)

        self.Fit()

        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            name = board.GetLayerName(i)
            self.m_layerChoice.Append(name)
            self.m_maskLayerChoice.Append(name)
            if name == 'User.Eco1':
                self.m_maskLayerChoice.SetSelection(i)
            elif name == 'F.Cu':
                self.m_layerChoice.SetSelection(i)

        self.SetMinSize(self.GetSize())

    def get_matching_nets(self):
        prefix = self.m_net_prefix.Value
        return { net for net in self.nets if net.startswith(prefix) }

    def net_names(self):
        prefix = self.m_net_prefix.Value
        for i in count():
            yield f'{prefix}{i}'

    def confirm_tearup_mesh_all(self, evt):
        self.tearup_confirm_dialog.SetMessage('Do you really want to tear up all autorouted traces on this board? This stap cannot be undone!')
        self.tearup_confirm_dialog.SetYesNoLabels("Tear up all autorouted traces", "Close")

        if self.tearup_confirm_dialog.ShowModal() == wx.ID_YES:
            self.tearup_mesh()

    def confirm_tearup_mesh(self, evt):
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
        self.tearup_confirm_dialog.SetYesNoLabels("Tear up {} traces".format(len(matching)), "Close")

        if self.tearup_confirm_dialog.ShowModal() == wx.ID_YES:
            self.tearup_mesh(matching)

    def tearup_mesh(self, matching=None):
        count = 0
        for track in self.board.GetTracks():
            if not (track.GetStatus() & pcbnew.TRACK_AR):
                continue

            if matching is not None and track.GetNet().GetNetname() not in matching:
                continue

            count += 1
            self.board.Remove(track)
        print(f'Tore up {count} trace segments.')

    def generate_mesh(self, evt):
        try:
            settings = GeneratorSettings(
                mesh_angle  = float(self.m_angleSpin.Value),
                trace_width = float(self.m_traceSpin.Value),
                space_width = float(self.m_spaceSpin.Value),
                anchor_exit = float(self.m_exitSpin.Value),
                num_traces  = int(self.m_traceCountSpin.Value),
                offset_x    = float(self.m_offsetXSpin.Value),
                offset_y    = float(self.m_offsetYSpin.Value),
                chamfer     = float(self.m_chamferSpin.Value)/100.0,
                target_layer_id = self.m_layerChoice.GetSelection(),
                mask_layer_id   = self.m_maskLayerChoice.GetSelection(),
                random_seed = str(self.m_seedInput.Value) or None,
                randomness  = float(self.m_randomnessSpin.Value)/100.0)
        except ValueError as e:
            return wx.MessageDialog(self, "Invalid input value: {}.".format(e), "Invalid input").ShowModal()

        mesh_zones = []
        for drawing in self.board.GetDrawings():
            if drawing.GetLayer() == settings.mask_layer_id:
                mesh_zones.append(drawing)

        if not mesh_zones:
                return wx.MessageDialog(self, "Error: Could not find any mesh zones on the outline pattern layer.").ShowModal()


        outlines = pcbnew.SHAPE_POLY_SET()
        self.board.GetBoardPolygonOutlines(outlines, "")
        board_outlines = list(self.poly_set_to_shapely(outlines))
        board_mask = shapely.ops.unary_union(board_outlines)

        zone_outlines = [ outline for zone in mesh_zones for outline in self.poly_set_to_shapely(zone.GetPolyShape()) ]
        zone_mask = shapely.ops.unary_union(zone_outlines)

        mask = zone_mask.intersection(board_mask)

        anchor = [ mod for mod in self.board.GetModules() if mod.GetReference() == self.m_anchorInput.Value ]
        if len(anchor) == 0:
            return wx.MessageDialog(self, f'Error: Could not find anchor footprint "{self.m_anchorInput.Value}".').ShowModal()
        if len(anchor) > 1:
            return wx.MessageDialog(self, f'Error: Multiple footprints with anchor footprint reference "{self.m_anchorInput.Value}".').ShowModal()
        anchor, = anchor

        try:
            def warn(msg):
                dialog = wx.MessageDialog(self, msg + '\n\nDo you want to abort mesh generation?',
                        "Mesh Generation Warning").ShowModal()
                dialog = wx.MessageDialog(self, "", style=wx.YES_NO | wx.NO_DEFAULT)
                dialog.SetYesNoLabels("Abort", "Ignore and continue")

                if self.tearup_confirm_dialog.ShowModal() == wx.ID_YES:
                    raise AbortError()

            nets = list(islice(self.net_names(), settings.num_traces))
            self.generate_mesh_backend(mask, anchor, nets=nets, warn=warn, settings=settings)

        except GeneratorError as e:
            return wx.MessageDialog(self, str(e), "Mesh Generation Error").ShowModal()
        except AbortError:
            pass

    def poly_set_to_shapely(self, poly_set):
        for i in range(poly_set.OutlineCount()):
            outline = poly_set.Outline(i)

            def shape_line_chain_to_coords(line_chain):
                points = []
                for j in range(line_chain.PointCount()):
                    point = line_chain.CPoint(j)
                    points.append((pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)))
                return points

            exterior = shape_line_chain_to_coords(outline)
            interiors = [ shape_line_chain_to_coords(poly_set.Hole(i, j)) for j in range(poly_set.HoleCount(i)) ]
            yield polygon.Polygon(exterior, interiors)

    def generate_mesh_backend(self, mask, anchor, nets, warn=lambda s: None, settings=GeneratorSettings()):
        anchor_outlines = list(self.poly_set_to_shapely(anchor.GetBoundingPoly()))
        if len(anchor_outlines) == 0:
            raise GeneratorError('Could not find any outlines for anchor {}'.format(anchor.GetReference()))
        if len(anchor_outlines) > 1:
            warn('Anchor {} has multiple outlines. Using first outline for trace start.')

        width_per_trace = settings.trace_width + settings.space_width
        grid_cell_width = width_per_trace * settings.num_traces * 2

        mask_rotated = affinity.rotate(mask, -settings.mesh_angle, origin=mask.centroid)
        bbox = mask_rotated.bounds

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
                cell = affinity.rotate(cell, settings.mesh_angle, origin=mask.centroid)
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
        with DebugOutput('/mnt/c/Users/jaseg/shared/dbg_grid.svg') as dbg:
            dbg.add(mask, color='#00000020')

            for y, row in enumerate(grid):
                for x, cell in enumerate(row):
                    if mask.contains(cell):
                        if cell == exit_cell[0]:
                            color = '#ff00ff80'
                        elif any(ol.overlaps(cell) for ol in anchor_outlines):
                            color = '#ffff0080'
                        elif any(ol.contains(cell) for ol in anchor_outlines):
                            color = '#ff000080'
                        else:
                            num_valid += 1
                            color = '#00ff0080'
                    elif mask.overlaps(cell):
                        color = '#ffff0080'
                    else:
                        color = '#ff000080'
                    dbg.add(cell, color=color)

            for foo in anchor_outlines:
                dbg.add(foo, color='#0000ff00', stroke_width=0.05, stroke_color='#000000ff')

        def is_valid(cell):
            if not mask.contains(cell):
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
                    0b1000: 0b0010,
                    0b0000: 0b0000
                    }[mask]

        rnd_state = random.Random(settings.random_seed)
        def skewed_random_iter(it, mask, randomness):
            l = list(it)
            if rnd_state.random() < 1.0 - randomness:
                for x, y, m in l:
                    if m == mask:
                        yield x, y, m
                        break
                l.remove((x, y, m))
            rnd_state.shuffle(l)
            yield from l

        target_layer_id = self.board.GetLayerID('F.Cu') # FIXME make configurable
        def add_track(segment:geometry.LineString, net=None):
            coords = list(segment.coords)
            for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
                if (x1, y1) == (x2, y2): # zero-length track due to zero chamfer
                    continue
                track = pcbnew.TRACK(self.board)
                track.SetStatus(track.GetStatus() | pcbnew.TRACK_AR)
                track.SetStart(pcbnew.wxPoint(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
                track.SetEnd(pcbnew.wxPoint(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
                track.SetWidth(pcbnew.FromMM(settings.trace_width))
                track.SetLayer(target_layer_id)
                if net is not None:
                    track.SetNet(net)
                self.board.Add(track)

        netinfos = []
        for name in nets:
            ni = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(ni)
            netinfos.append(ni)

        not_visited = { (x, y) for x in range(grid_cols) for y in range(grid_rows) if is_valid(grid[y][x]) }
        num_to_visit = len(not_visited)
        track_count = 0
        with DebugOutput('/mnt/c/Users/jaseg/shared/dbg_cells.svg') as dbg_cells,\
             DebugOutput('/mnt/c/Users/jaseg/shared/dbg_composite.svg') as dbg_composite,\
             DebugOutput('/mnt/c/Users/jaseg/shared/dbg_tiles.svg') as dbg_tiles,\
             DebugOutput('/mnt/c/Users/jaseg/shared/dbg_traces.svg') as dbg_traces:
            dbg_cells.add(mask, color='#00000020')
            dbg_composite.add(mask, color='#00000020')
            dbg_traces.add(mask, color='#00000020')
            dbg_tiles.add(mask, color='#00000020')
            
            TILE_COLORS = {
                0b0000: '#ffcc00ff',
                0b0001: '#d40000ff',
                0b0010: '#d40000ff',
                0b0011: '#ff6600ff',
                0b0100: '#d40000ff',
                0b0101: '#00d400ff',
                0b0110: '#ff6600ff',
                0b0111: '#00ccffff',
                0b1000: '#d40000ff',
                0b1001: '#ff6600ff',
                0b1010: '#00d400ff',
                0b1011: '#00ccffff',
                0b1100: '#ff6600ff',
                0b1101: '#00ccffff',
                0b1110: '#00ccffff',
                0b1111: '#ffcc00ff'}
            x, y = exit_cell[1]
            visited = 0
            key = 0
            entry_dir = 0
            stack = []
            depth = 0
            max_depth = 0
            i = 0
            past_tiles = {}
            def dump_output(i):
                with DebugOutput(f'/mnt/c/Users/jaseg/Pictures/kicad-mesh/per-tile/step{i}.svg') as dbg_per_tile:
                    dbg_per_tile.add(mask, color='#00000020')
                    for foo in anchor_outlines:
                        dbg_per_tile.add(foo, color='#00000080', stroke_width=0.05, stroke_color='#00000000')
                        
                    for le_y, row in enumerate(grid):
                        for le_x, cell in enumerate(row):
                            if mask.contains(cell):
                                if cell == exit_cell[0]:
                                    color = '#ff00ff80'
                                elif any(ol.overlaps(cell) for ol in anchor_outlines):
                                    color = '#ffff0080'
                                elif any(ol.contains(cell) for ol in anchor_outlines):
                                    color = '#ff000080'
                                else:
                                    color = '#00ff0080'
                            elif mask.overlaps(cell):
                                color = '#ffff0080'
                            else:
                                color = '#ff000080'
                            dbg_per_tile.add(cell, color=color)

                    for (le_x, le_y), (stroke_color, segments) in past_tiles.items():
                        for segment in segments:
                            segment = affinity.scale(segment, grid_cell_width, grid_cell_width, origin=(0, 0))
                            segment = affinity.translate(segment, grid_origin[0] + le_x*grid_cell_width, grid_origin[1] + le_y*grid_cell_width)
                            segment = affinity.rotate(segment, settings.mesh_angle, origin=mask.centroid)
                            dbg_per_tile.add(segment, stroke_width=settings.trace_width, color='#ff000000', stroke_color=stroke_color)

            armed = False
            while not_visited or stack:
                print(f'iteration {i}: {len(not_visited)}, {len(stack)}')
                for n_x, n_y, bmask in skewed_random_iter(iter_neighbors(x, y), entry_dir, settings.randomness):
                    if (n_x, n_y) in not_visited:
                        dbg_composite.add(grid[n_y][n_x], color=('visit_depth', depth), opacity=1.0)
                        dbg_cells.add(grid[n_y][n_x], color=('visit_depth', depth), opacity=1.0)
                        key |= bmask
                        stack.append((x, y, key, bmask, depth))
                        not_visited.remove((n_x, n_y))
                        visited += 1
                        depth += 1
                        i += 1
                        armed = True
                        max_depth = max(depth, max_depth)

                        past_tiles[x, y] = (TILE_COLORS[key],
                                [segment
                                    for segment, _net in Pattern.render(key, settings.num_traces, settings.chamfer) ])

                        x, y, key, entry_dir = n_x, n_y, reciprocal(bmask), bmask
                        dump_output(i)
                        break
                else:
                    stroke_color = TILE_COLORS[key]
                    past_tiles[x, y] = (stroke_color,
                            [segment
                                for segment, _net in Pattern.render(key, settings.num_traces, settings.chamfer) ])
                    for segment, net in Pattern.render(key, settings.num_traces, settings.chamfer):
                        segment = affinity.scale(segment, grid_cell_width, grid_cell_width, origin=(0, 0))
                        segment = affinity.translate(segment, grid_origin[0] + x*grid_cell_width, grid_origin[1] + y*grid_cell_width)
                        segment = affinity.rotate(segment, settings.mesh_angle, origin=mask.centroid)
                        dbg_composite.add(segment, stroke_width=settings.trace_width, color='#ff000000', stroke_color='#ffffff60')
                        dbg_traces.add(segment, stroke_width=settings.trace_width, color='#ff000000', stroke_color='#000000ff')
                        dbg_tiles.add(segment, stroke_width=settings.trace_width, color='#ff000000', stroke_color=stroke_color)
                        #add_track(segment, netinfos[net]) # FIXME (works, disabled for debug)
                        track_count += 1
                    if not stack:
                        break
                    if armed:
                        i += 1
                        dump_output(i)
                        armed = False
                    *stack, (x, y, key, entry_dir, depth) = stack

            dbg_cells.scale_colors('visit_depth', max_depth)
            dbg_composite.scale_colors('visit_depth', max_depth)

            for foo in anchor_outlines:
                dbg_cells.add(foo, color='#00000080', stroke_width=0.05, stroke_color='#00000000')
                dbg_traces.add(foo, color='#00000080', stroke_width=0.05, stroke_color='#00000000')
                dbg_composite.add(foo, color='#00000080', stroke_width=0.05, stroke_color='#00000000')
                dbg_tiles.add(foo, color='#00000080', stroke_width=0.05, stroke_color='#00000000')


        print(f'Added {track_count} trace segments.')

        #pcbnew.Refresh()
        #self.tearup_mesh()
        # TODO generate

    def update_net_label(self, evt):
        self.m_netLabel.SetLabel('Like: ' + ', '.join(islice(self.net_names(), 3)) + ', ...')

    def quit(self, evt):
        self.Destroy()


class Pattern:
    @staticmethod
    def render(key, n, cd=0):
        yield from Pattern.LUT[key](n, cd=math.tan(math.pi/8) * cd)
    
    def draw_I(n, cd):
        for i in range(n):
            sp = (i+0.5) * (1/(2*n))
            yield geometry.LineString([(sp, 0), (sp, 1)]), i
            sp = (2*n-1-i+0.5) * (1/(2*n))
            yield geometry.LineString([(sp, 0), (sp, 1)]), i

    def draw_U(n, cd):
        pitch = (1/(2*n))
        cd *= pitch # chamfer depth
        for i in range(n):
            sp = (i+0.5) * pitch
            yield geometry.LineString([(sp, 0), (sp, 1-sp-cd), (sp+cd, 1-sp), (1-sp-cd, 1-sp), (1-sp, 1-sp-cd), (1-sp, 0)]), i

    def draw_L(n, cd):
        pitch = (1/(2*n))
        cd *= pitch # chamfer depth
        for i in range(n):
            sp = (i+0.5) * pitch
            yield geometry.LineString([(sp, 0), (sp, 1-sp-cd), (sp+cd, 1-sp), (1, 1-sp)]), i
            sp = (2*n-1-i+0.5) * pitch
            yield geometry.LineString([(sp, 0), (sp, 1-sp-cd), (sp+cd, 1-sp), (1, 1-sp)]), i
    
    def draw_T(n, cd):
        pitch = (1/(2*n))
        cd *= pitch # chamfer depth
        for i in range(n):
            sp = (i+0.5) * pitch
            # through line
            yield geometry.LineString([(0, sp), (1, sp)]), i
            # two corners on the opposite side
            yield geometry.LineString([(0, 1-sp), (sp-cd, 1-sp), (sp, 1-sp+cd), (sp, 1)]), i
            yield geometry.LineString([(1-sp, 1), (1-sp, 1-sp+cd), (1-sp+cd, 1-sp), (1, 1-sp)]), i

    def draw_X(n, cd):
        pitch = (1/(2*n))
        cd *= pitch # chamfer depth
        for i in range(n):
            sp = (i+0.5) * pitch
            yield geometry.LineString([(0, sp), (sp-cd, sp), (sp, sp-cd), (sp, 0)]), i
            yield geometry.LineString([(1-sp, 0), (1-sp, sp-cd), (1-sp+cd, sp), (1, sp)]), i
            yield geometry.LineString([(0, 1-sp), (sp-cd, 1-sp), (sp, 1-sp+cd), (sp, 1)]), i
            yield geometry.LineString([(1-sp, 1), (1-sp, 1-sp+cd), (1-sp+cd, 1-sp), (1, 1-sp)]), i

    def rotate(pattern, deg):
        def wrapper(n, *args, **kwargs):
            for segment, net in pattern(n, *args, **kwargs):
                yield affinity.rotate(segment, deg, origin=(0.5, 0.5)), net
        return wrapper

    def raise_error(n, *args, **kwargs):
        #raise ValueError('Tried to render invalid cell. This is a bug.')
        return []

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

    def scale_colors(self, group, max_value):
        self.objs = [
                (obj,
                    (virihex(color[1], max=max_value) if isinstance(color, tuple) and color[0] == group else color,
                        *rest))
            for obj, (color, *rest) in self.objs ]

    def add(self, obj, color=None, stroke_width=0, stroke_color=None, opacity=1.0):
        self.objs.append((obj, (color, stroke_color, stroke_width, opacity)))

    def gen_svg(self, obj, fill_color=None, stroke_color=None, stroke_width=None, opacity=1.0):
        fill_color = fill_color or '#ff0000aa'
        stroke_color = stroke_color or '#000000ff'
        stroke_width = 0 if stroke_width is None else stroke_width

        if isinstance(obj, geometry.MultiPolygon):
            out = ''
            for geom in obj.geoms:
                out += gen_svg(geom, fill_color, stroke_color, stroke_width, opacity)
            return out

        elif isinstance(obj, polygon.Polygon):
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

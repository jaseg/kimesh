from collections import defaultdict
import dataclasses
from contextlib import contextmanager
import textwrap
import random
import math
from itertools import count, islice
import json
from os import path

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

@dataclasses.dataclass
class GeneratorSettings:
    edge_clearance: float = 1.5   # mm
    anchor:         str   = None  # Footprint designator
    chamfer:        float = 0.0   # unit fraction
    mask_layer_id:  int   = 0     # kicad layer id, populated later
    random_seed:    str   = None
    randomness:     float = 1.0

    def serialize(self):
        d = dataclasses.asdict(self)
        d['kimesh_settings_version'] = '1.0.0'
        return json.dumps(d).encode()

    @classmethod
    def deserialize(cls, data):
        d = json.loads(data.decode())
        version = d.pop('kimesh_settings_version')
        vtup = tuple(map(int, version.split('.')))
        if vtup > (2, 0, 0):
            raise cls.VersionError("Project kimesh settings file is too new for this plugin's version.")
        return cls(**d)

    class VersionError(ValueError):
        pass


class MeshPluginMainDialog(mesh_plugin_dialog.MainDialog):
    def __init__(self, board):
        mesh_plugin_dialog.MainDialog.__init__(self, None)
        self.board = board

        self.m_cancelButton.Bind(wx.EVT_BUTTON, self.quit)
        self.m_removeButton.Bind(wx.EVT_BUTTON, self.confirm_tearup_mesh)
        self.m_generateButton.Bind(wx.EVT_BUTTON, self.generate_mesh)
        self.m_net_prefix.Bind(wx.EVT_TEXT, self.update_net_label)

        self.tearup_confirm_dialog = wx.MessageDialog(self, "", style=wx.YES_NO | wx.NO_DEFAULT)

        self.nets = { str(wxs) for wxs, netinfo in board.GetNetsByName().items() }
        self.update_net_label(None)

        self.Fit()

        settings = None
        if path.isfile(self.settings_fn()):
            with open(self.settings_fn(), 'rb') as f:
                try:
                    settings = GeneratorSettings.deserialize(f.read())
                except GeneratorSettings.VersionError as e:
                    wx.MessageDialog(self, "Cannot load settings: {}.".format(e), "File I/O error").ShowModal()

        for i in range(pcbnew.PCB_LAYER_ID_COUNT):
            name = board.GetLayerName(i)
            self.m_maskLayerChoice.Append(name)
            if name == 'User.Eco1':
                self.m_maskLayerChoice.SetSelection(i)

        for i, fp in enumerate(self.board.Footprints()):
            ref = fp.GetReference()
            self.m_anchorChoice.Append(ref)
            if settings and ref == settings.anchor:
                self.m_anchorChoice.SetSelection(i)

        if settings:
            self.m_chamferSpin.Value = settings.chamfer*100.0
            self.m_maskLayerChoice.SetSelection(settings.mask_layer_id)
            self.m_seedInput.Value = settings.random_seed or ''
            self.m_randomnessSpin.Value = settings.randomness*100.0
            self.m_edgeClearanceSpin.Value = settings.edge_clearance

        self.SetMinSize(self.GetSize())

    def get_matching_nets(self):
        prefix = self.m_net_prefix.Value
        return { net for net in self.nets if net.startswith(prefix) }

    def confirm_tearup_mesh(self, evt):
        matching = self.get_matching_nets()

        if not str(self.m_net_prefix.Value):
            message = "You have set an empty net prefix. This will match ALL {} nets on the board. Do you really want to tear up all tracks? This cannot be undone!"

        else:
            message = "Do you really want to tear up all traces of the {} matching nets on this board? This step cannot be undone!"

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
            if matching is not None and track.GetNet().GetNetname() not in matching:
                continue

            count += 1
            self.board.Remove(track)
        print(f'Tore up {count} trace segments.')

    def settings_fn(self):
        return path.join(path.dirname(self.board.GetFileName()), 'last_kimesh_settings.json')

    def generate_mesh(self, evt):
        try:
            settings = GeneratorSettings(
                edge_clearance = float(self.m_edgeClearanceSpin.Value),
                anchor      = str(list(self.board.Footprints())[self.m_anchorChoice.GetSelection()].GetReference()),
                chamfer     = float(self.m_chamferSpin.Value)/100.0,
                mask_layer_id   = self.m_maskLayerChoice.GetSelection(),
                random_seed = str(self.m_seedInput.Value) or None,
                randomness  = float(self.m_randomnessSpin.Value)/100.0)
        except ValueError as e:
            return wx.MessageDialog(self, "Invalid input value: {}.".format(e), "Invalid input").ShowModal()

        try:
            with open(self.settings_fn(), 'wb') as f:
                f.write(settings.serialize())
                print('Saved settings to', f.name)
        except:
            wx.MessageDialog(self, "Cannot save settings: {}.".format(e), "File I/O error").ShowModal()

        anchor = [ fp for fp in self.board.Footprints() if fp.GetReference() == settings.anchor ]
        if len(anchor) == 0:
            return wx.MessageDialog(self, f'Error: Could not find anchor footprint "{self.m_anchorInput.Value}".').ShowModal()
        if len(anchor) > 1:
            return wx.MessageDialog(self, f'Error: Multiple footprints with anchor footprint reference "{self.m_anchorInput.Value}".').ShowModal()
        anchor, = anchor

        pad0, *_ = anchor.Pads()
        lset = pad0.GetLayerSet()
        target_layer_id, *_ = [l for l in lset.CuStack() if lset.Contains(l)]

        mesh_zones = []
        for drawing in self.board.GetDrawings():
            if drawing.GetLayer() == settings.mask_layer_id:
                mesh_zones.append(drawing.GetPolyShape())

        if not mesh_zones:
                return wx.MessageDialog(self, "Error: Could not find any mesh zones on the outline pattern layer.").ShowModal()

        keepouts = []
        for zone in self.board.Zones():
            if zone.GetDoNotAllowCopperPour() and zone.GetLayerSet().Contains(target_layer_id):
                keepouts.append(zone.Outline())
        print(f'Found {len(keepouts)} keepout areas.')

        outlines = pcbnew.SHAPE_POLY_SET()
        self.board.GetBoardPolygonOutlines(outlines)
        board_outlines = list(self.poly_set_to_shapely(outlines))
        board_mask = shapely.ops.unary_union(board_outlines)
        board_mask = board_mask.buffer(-settings.edge_clearance)

        zone_outlines = [ outline for zone in mesh_zones for outline in self.poly_set_to_shapely(zone) ]
        zone_mask = shapely.ops.unary_union(zone_outlines)
        mask = zone_mask.intersection(board_mask)

        keepout_outlines = [ outline for zone in keepouts for outline in self.poly_set_to_shapely(zone) ]
        keepout_mask = shapely.ops.unary_union(keepout_outlines)
        mask = shapely.difference(mask, keepout_mask)

        try:
            def warn(msg):
                dialog = wx.MessageDialog(self, msg + '\n\nDo you want to abort mesh generation?',
                        "Mesh Generation Warning").ShowModal()
                dialog = wx.MessageDialog(self, "", style=wx.YES_NO | wx.NO_DEFAULT)
                dialog.SetYesNoLabels("Abort", "Ignore and continue")

                if self.tearup_confirm_dialog.ShowModal() == wx.ID_YES:
                    raise AbortError()

            self.generate_mesh_backend(mask, anchor, net_prefix=str(self.m_net_prefix.Value), target_layer_id=target_layer_id, warn=warn, settings=settings)

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

    def generate_mesh_backend(self, mask, anchor, net_prefix, target_layer_id, warn=lambda s: None, settings=GeneratorSettings()):
        anchor_outlines = list(self.poly_set_to_shapely(anchor.GetBoundingHull()))
        if len(anchor_outlines) == 0:
            raise GeneratorError('Could not find any outlines for anchor {}'.format(anchor.GetReference()))
        if len(anchor_outlines) > 1:
            warn('Anchor {} has multiple outlines. Using first outline for trace start.')
        anchor_pads = list(sorted(anchor.Pads(), key=lambda pad: int(pad.GetNumber())))

        mesh_angle = anchor.GetOrientationDegrees()
        trace_width = pcbnew.ToMM(anchor_pads[0].GetSize()[0])
        space_width = pcbnew.ToMM(math.dist(anchor_pads[0].GetPosition(), anchor_pads[1].GetPosition())) - trace_width
        num_traces = len(anchor_pads)
        assert num_traces%2 == 0
        num_traces //= 2
        nets = [f'{net_prefix}{i}' for i in range(num_traces)]

        width_per_trace = trace_width + space_width
        grid_cell_width = width_per_trace * num_traces * 2

        x0, y0 = anchor_pads[0].GetPosition()
        x0, y0 = pcbnew.ToMM(x0), pcbnew.ToMM(y0)
        xl, yl = anchor_pads[-1].GetPosition()
        xl, yl = pcbnew.ToMM(xl), pcbnew.ToMM(yl)

        mesh_angle = math.atan2(xl-x0, yl-y0)
        print('mesh angle is', math.degrees(mesh_angle))
        len_along = - width_per_trace/2
        x0 += -trace_width/2 * math.cos(mesh_angle) + len_along * math.sin(mesh_angle)
        y0 += -trace_width/2 * math.sin(mesh_angle) + len_along * math.cos(mesh_angle)

        mask_xformed = affinity.translate(mask, -x0, -y0)
        mask_xformed = affinity.rotate(mask_xformed, -mesh_angle, origin=(0, 0), use_radians=True)
        bbox = mask_xformed.bounds

        grid_x0, grid_y0 = math.floor(bbox[0]/grid_cell_width), math.floor(bbox[1]/grid_cell_width)
        grid_origin = grid_x0*grid_cell_width, grid_y0*grid_cell_width
        grid_rows = int(math.ceil((bbox[3] - grid_origin[1]) / grid_cell_width))
        grid_cols = int(math.ceil((bbox[2] - grid_origin[0]) / grid_cell_width))
        print(f'generating grid of size {grid_rows} * {grid_cols} with origin {grid_x0}, {grid_y0}')

        grid = []
        for y in range(grid_y0, grid_y0+grid_rows):
            row = []
            for x in range(grid_x0, grid_x0+grid_cols):
                cell = polygon.Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
                cell = affinity.scale(cell, grid_cell_width, grid_cell_width, origin=(0, 0))
                cell = affinity.translate(cell, x*grid_cell_width, y*grid_cell_width)
                cell = affinity.rotate(cell, mesh_angle, origin=(0, 0), use_radians=True)
                cell = affinity.translate(cell, x0, y0)
                row.append(cell)
            grid.append(row)

        num_valid = 0
        with DebugOutput('dbg_grid.svg') as dbg:
            dbg.add(mask, color='#00000020')

            for y, row in enumerate(grid, start=grid_y0):
                for x, cell in enumerate(row, start=grid_x0):
                    if mask.contains(cell):
                        if x == 0 and y == 0: # exit cell
                            color = '#ff00ff80'
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

            dbg.add([[(x0-2, y0), (x0+2, y0)], [(x0, y0-2), (x0, y0+2)]], color='none', stroke_width=0.05, stroke_color='#ff0000ff')

        def is_valid(cell):
            if not mask.contains(cell):
                return False
            return True

        def iter_neighbors(x, y):
            if x > grid_x0:
                yield x-1, y, 0b0100
            if x - grid_x0 < grid_cols:
                yield x+1, y, 0b0001
            if y > grid_y0:
                yield x, y-1, 0b1000
            if y - grid_y0 < grid_rows:
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

        def add_track(segment:geometry.LineString, net=None):
            coords = list(segment.coords)
            for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
                if (x1, y1) == (x2, y2): # zero-length track due to zero chamfer
                    continue
                track = pcbnew.PCB_TRACK(self.board)
                #track.SetStatus(track.GetStatus() | pcbnew.TRACK_AR)
                track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
                track.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
                track.SetWidth(pcbnew.FromMM(trace_width))
                track.SetLayer(target_layer_id)
                if net is not None:
                    track.SetNet(net)
                self.board.Add(track)

        netinfos = []
        for name in nets:
            ni = pcbnew.NETINFO_ITEM(self.board, name)
            self.board.Add(ni)
            netinfos.append(ni)

        not_visited = { (x, y) for x in range(grid_x0, grid_x0+grid_cols) for y in range(grid_y0, grid_y0+grid_rows) if is_valid(grid[y-grid_y0][x-grid_x0]) }
        num_to_visit = len(not_visited)
        track_count = 0
        with DebugOutput('dbg_cells.svg') as dbg_cells,\
             DebugOutput('dbg_composite.svg') as dbg_composite,\
             DebugOutput('dbg_tiles.svg') as dbg_tiles,\
             DebugOutput('dbg_traces.svg') as dbg_traces:
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
            x, y = -1, 0
            visited = 0
            key = 0
            entry_dir = 0b0001
            stack = []
            depth = 0
            max_depth = 0
            i = 0
            past_tiles = {}
            def dump_output(i):
                with DebugOutput(f'per-tile/step{i}.svg') as dbg_per_tile:
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
                            segment = affinity.translate(segment, le_x*grid_cell_width, le_y*grid_cell_width)
                            segment = affinity.rotate(segment, mesh_angle, origin=(0, 0), use_radians=True)
                            segment = affinity.translate(segment, x0, y0)
                            dbg_per_tile.add(segment, stroke_width=trace_width, color='#ff000000', stroke_color=stroke_color)

            armed = False
            while not_visited or stack:
                for n_x, n_y, bmask in skewed_random_iter(iter_neighbors(x, y), entry_dir, settings.randomness):
                    if (n_x, n_y) in not_visited:
                        dbg_composite.add(grid[n_y-grid_y0][n_x-grid_x0], color=('visit_depth', depth), opacity=1.0)
                        dbg_cells.add(grid[n_y-grid_y0][n_x-grid_x0], color=('visit_depth', depth), opacity=1.0)
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
                                    for segment, _net in Pattern.render(key, num_traces, settings.chamfer) ])

                        x, y, key, entry_dir = n_x, n_y, reciprocal(bmask), bmask
                        #dump_output(i)
                        break
                else:
                    stroke_color = TILE_COLORS[key]
                    past_tiles[x, y] = (stroke_color,
                            [segment for segment, _net in Pattern.render(key, num_traces, settings.chamfer) ])
                    for segment, net in Pattern.render(key, num_traces, settings.chamfer):
                        if is_valid(grid[y-grid_y0][x-grid_x0]):
                            segment = affinity.scale(segment, grid_cell_width, grid_cell_width, origin=(0, 0))
                            segment = affinity.translate(segment, x*grid_cell_width, y*grid_cell_width)
                            segment = affinity.rotate(segment, mesh_angle, origin=(0, 0), use_radians=True)
                            segment = affinity.translate(segment, x0, y0)
                            dbg_composite.add(segment, stroke_width=trace_width, color='#ff000000', stroke_color='#ffffff60')
                            dbg_traces.add(segment, stroke_width=trace_width, color='#ff000000', stroke_color='#000000ff')
                            dbg_tiles.add(segment, stroke_width=trace_width, color='#ff000000', stroke_color=stroke_color)
                            add_track(segment, netinfos[net]) # FIXME (works, disabled for debug)
                            track_count += 1
                    if not stack:
                        break
                    if armed:
                        i += 1
                        #dump_output(i)
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
        self.m_netLabel.SetLabel('Like: ' + ', '.join(f'{self.m_net_prefix.Value}{i}' for i in range(3)) + ', ...')

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
    filename = path.join('/tmp', filename)
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
                out += self.gen_svg(geom, fill_color, stroke_color, stroke_width, opacity)
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

        elif isinstance(obj, list):
            all_coords = [ [f'{x},{y}' for x, y in seg] for seg in obj ]
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

        bboxes = [ list(obj.bounds) for obj, _style in self.objs if not isinstance(obj, list) ]
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

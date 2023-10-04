#!/usr/bin/env python3

from pathlib import Path
import itertools

import gerbonara.cad.kicad as kc
from gerbonara.cad.kicad import footprints
import gerbonara as gn
from gerbonara.utils import MM

import click

@click.command()
@click.option('-w', '--trace-width', default='0.15', help='Comma-separated list of trace widths [mm]')
@click.option('-c', '--clearance', default='0.15', help='Comma-separated list of clearances to step through [mm]')
@click.option('-n', '--conductors', default='2', help='Comma-separated list of numbers of conductors')
@click.argument('output_dir', type=click.Path(dir_okay=True, file_okay=False, path_type=Path))
def generate_footprints(output_dir, trace_width, clearance, conductors):
    trace_widths = [float(x.strip()) for x in trace_width.split(',')]
    clearances = [float(x.strip()) for x in clearance.split(',')]
    conductors = [int(x.strip()) for x in conductors.split(',')]

    if output_dir.suffix != '.pretty':
        output_dir = output_dir.with_name(output_dir.name + '.pretty')

    for trace, space, conductors in itertools.product(trace_widths, clearances, conductors):
        pitch = trace + space

        fp = footprints.Footprint(
                name=f'MeshAnchor_{conductors}W_T{trace:.3f}mm_S{space:.3f}mm',
                _version=20230620,
                generator = footprints.Atom('kimesh_footprint_generator'),
                descr=f'KiMesh mesh anchor footprint, {conductors} wires, {trace:.3f} mm trace width, {space:.3f} mm clearance',
                tags='net tie',
                attributes=footprints.Attribute(footprints.Atom.smd),
                net_tie_pad_groups=[f'{i+1},{2*conductors-i},{2*conductors+1+i},{4*conductors-i}' for i in range(conductors)],
                polygons=[footprints.Polygon(
                    pts=footprints.PointList(xy=[
                        footprints.XYCoord(-pitch/2, pitch * (conductors - i - 0.5) + trace/2),
                        footprints.XYCoord(pitch/2, pitch * (conductors - i - 0.5) + trace/2),
                        footprints.XYCoord(pitch/2, pitch * (conductors - i - 0.5) - trace/2),
                        footprints.XYCoord(-pitch/2, pitch * (conductors - i - 0.5) - trace/2),
                        ]),
                    layer='F.Cu',
                    fill=footprints.Atom.solid)
                          for i in range(2*conductors)],
                pads=[
                    footprints.Pad(
                        number=f'{i+1}',
                        type=footprints.Atom.smd,
                        shape=footprints.Atom.circle,
                        at=footprints.AtPos(pitch * (i//(2*conductors) - 0.5), -pitch * (conductors - i%(2*conductors) - 0.5)),
                        size=footprints.XYCoord(trace, trace),
                        layers=['F.Cu'])
                    for i in range(4*conductors)])
        output_dir.mkdir(exist_ok=True)
        fp.make_standard_properties()
        fp.write(output_dir / f'{fp.name}.kicad_mod')

if __name__ == '__main__':
    generate_footprints()

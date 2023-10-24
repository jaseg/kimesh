#!/usr/bin/env python3
import re
import hashlib
import shutil
import subprocess
import json
from pathlib import Path

import click

def tree_size(path):
    return sum(entry.stat().st_size for entry in path.glob('**/*') if entry.is_file())

@click.command()
@click.option('--major', 'increment', flag_value='major')
@click.option('--minor', 'increment', flag_value='minor', default=True)
@click.option('--patch', 'increment', flag_value='patch', default=True)
@click.argument('version', required=False)
def do_release(version, increment):
    if not version:
        tag = subprocess.run('git describe --tags --abbrev=0 --match v*'.split(),
                             check=True, capture_output=True, text=True)
        major, minor, patch = map(int, re.fullmatch(r'v([0-9]+)\.([0-9]+)\.([0-9]+)', tag.stdout.strip()).groups())
        match increment:
            case 'major':
                major, minor, patch = (major+1, 0, 0)
            case 'minor':
                major, minor, patch = (major, minor+1, 0)
            case 'patch':
                major, minor, patch = (major, minor, patch+1)
        version = f'{major}.{minor}.{patch}'
    
    res = subprocess.run('git status --porcelain --untracked-files=no'.split(),
                   check=True, capture_output=True, text=True)
    if res.stdout.strip():
        raise click.ClickException('There are uncommitted changes in this repository.')

    print('Cleaning old footprints')
    footprint_dir = Path('de.jaseg.kimesh.footprints') / 'footprints'
    shutil.rmtree(footprint_dir, ignore_errors=True)
    footprint_dir.mkdir()

    print('Re-generating footprints')
    for n in range(2, 9):
        subprocess.run(['python', '-m', 'footprint_generator',
                        '-w', '0.100,0.120,0.150,0.200,0.250,0.300,0.350,0.400,0.500,0.600,0.700,0.800,1.000,1.200,1.500,1.800',
                        '-c', '0.100,0.120,0.150,0.200,0.300,0.400,0.500',
                        '-n', str(n),
                        str(footprint_dir / f'kimesh_anchors_{n}wire.pretty')
                        ], check=True)

    res = subprocess.run('git ls-files'.split(), check=True, capture_output=True, text=True)
    for path in res.stdout.splitlines():
        if re.fullmatch(r'de\.jaseg\.kimesh\.[^/]*-v[.0-9]*\.zip', path.strip()):
            print(f'Removing old release zip {path} from git index.')
            subprocess.run(['git', 'rm', path], check=True, capture_output=True)

    for pkg_dir in Path('de.jaseg.kimesh.plugin'), Path('de.jaseg.kimesh.footprints'):
        # NOTE: metadata.json appears twice. In what I believe is a sub-optimal design choice, the variant in the
        # archive is only allowed to contain the current version in its version list without its zip file metadata,
        # while the variant in the repository index is supposed to contain all past versions including their zip file
        # metadata. AFAICT they are the same otherwise.
        meta_path = Path(f'{pkg_dir}-repo-metadata.json')

        print(f'Updating metadata file {meta_path}')
        ver_dict = {
            'version': version,
            'status': 'stable',
            'kicad_version': '7.99',
        }

        # Include just the version metadata in the metadata for the archive
        meta_file = json.loads(meta_path.read_text())
        meta_file['versions'] = [ver_dict]
        (pkg_dir / 'metadata.json').write_text(json.dumps(meta_file, indent=4))

        zip_fn = Path(shutil.make_archive(f'{pkg_dir.name}-v{version}', 'zip', pkg_dir, '.'))
        print(f'Adding new release zip {zip_fn} to git index.')
        subprocess.run(['git', 'add', str(zip_fn)], check=True, capture_output=True)

        # Add the zip's metadata to the metadata for the repository
        ver_dict['download_sha256'] = hashlib.sha256(zip_fn.read_bytes()).hexdigest()
        ver_dict['download_size'] = zip_fn.stat().st_size
        ver_dict['download_url'] = f'https://git.jaseg.de/kimesh.git/plain/{zip_fn.name}?h=v{version}'
        ver_dict['install_size'] = tree_size(pkg_dir)

        meta_file = json.loads(meta_path.read_text())
        meta_file['versions'].append(ver_dict)
        meta_path.write_text(json.dumps(meta_file, indent=4))

        print(f'Adding updated metadata file {meta_path} to git index')
        subprocess.run(['git', 'add', str(meta_path)], check=True, capture_output=True)

    print('Create git commit')
    subprocess.run(['git', 'commit', '-m', f'Version {version}', '--no-edit'], check=True, capture_output=True)
    res = subprocess.run('git rev-parse --short HEAD'.split(), check=True, capture_output=True, text=True)
    print(f'Created commit {res.stdout.strip()}')
    print(f'Creating and signing version tag v{version}')
    subprocess.run(['git',
                    '-c', 'user.signingkey=E36F75307F0A0EC2D145FF5CED7A208EEEC76F2D',
                    '-c', 'user.email=python-mpv@jaseg.de',
                    'tag', '-s', f'v{version}', '-m', f'Version v{version}'],
                   check=True)

if __name__ == '__main__':
    do_release()

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from time import sleep

import requests
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)

progress = Progress(
    TextColumn('{task.description}', markup=False),
    BarColumn(bar_width=None),
    MofNCompleteColumn(),
    TimeElapsedColumn(),
)

ns = {'wcs': 'http://www.opengis.net/wcs/2.0', 'ows': 'http://www.opengis.net/ows/2.0'}


def main():
    parser = argparse.ArgumentParser(description='Download all files from a WCS service')
    parser.add_argument('url', help='URL of the WCS service')
    parser.add_argument(
        '-o',
        '--output-path',
        dest='output_path',
        default='images',
        help='The path to store the downloaded files',
    )
    parser.add_argument(
        '-s',
        '--substitute',
        dest='substitute',
        default=[],
        nargs='+',
        help='Rename the files according using re.sub, the arguments are separated by /.',
    )
    args = parser.parse_args()

    output_path = Path(args.output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    contents = parse_capabilities(args.url)
    with progress:
        task = progress.add_task(f'Downloading to {output_path}', total=len(contents))
        for content in contents:
            file_name = substitute_file_name('{}.tif'.format(content['id']), args.substitute)
            file_path = output_path / file_name
            download_content(args.url, content, file_path)
            progress.advance(task)


def parse_capabilities(service_url):
    capabilities_url = service_url + '?service=WCS&acceptversions=2.0.1&request=GetCapabilities'
    response = requests.get(capabilities_url)
    root = ET.fromstring(response.content)

    contents = []
    for node in root.findall('./wcs:Contents/wcs:CoverageSummary', namespaces=ns):
        coverage_id = node.find('./wcs:CoverageId', namespaces=ns)
        lower_corner = [
            float(item) for item in node.find('./ows:WGS84BoundingBox/ows:LowerCorner', namespaces=ns).text.split()
        ]
        upper_corner = [
            float(item) for item in node.find('./ows:WGS84BoundingBox/ows:UpperCorner', namespaces=ns).text.split()
        ]

        content = {'id': coverage_id.text, 'lower_corner': lower_corner, 'upper_corner': upper_corner}

        contents.append(content)

    return contents


def download_content(service_url, content, file_path):
    if not file_path.exists():
        download_url = f'{service_url}?VERSION=2.0.1&SERVICE=WCS&REQUEST=GetCoverage&COVERAGEID={content["id"]}'
        response = requests.get(download_url)
        file_path.write_bytes(response.content)
        sleep(1)


def substitute_file_name(file_name, substitute):
    for pattern, repl in [string.split('/') for string in substitute]:
        file_name = re.sub(pattern, repl, file_name)
    return file_name

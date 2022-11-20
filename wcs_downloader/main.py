import argparse
import json
from pathlib import Path
import re
from time import sleep
import xml.etree.ElementTree as ET

import requests
from tqdm import tqdm

ns = {
    'wcs': 'http://www.opengis.net/wcs/2.0',
    'ows': 'http://www.opengis.net/ows/2.0'
}


def download():
    parser = argparse.ArgumentParser(description='Download all files from a WCS service')
    parser.add_argument('url', help='URL of the WCS service')
    parser.add_argument('-o|--output-path', dest='output_path', default='images',
                        help='The path to store the downloaded files')
    parser.add_argument('-s|--substitute', dest='substitute', default=[], nargs='+',
                        help='Rename the files according using re.sub, the arguments are seperated by /.')
    args = parser.parse_args()

    output_path = Path(args.output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    contents = parse_capabilities(args.url)

    for content in tqdm(contents):
        file_name = substitute_file_name('{}.tif'.format(content['id']), args.substitute)
        file_path = output_path / file_name

        if not file_path.exists():
            download_url = args.url + '?VERSION=2.0.1&SERVICE=WCS&REQUEST=GetCoverage&COVERAGEID={}'.format(content['id'])
            response = requests.get(download_url)
            open(file_path, 'wb').write(response.content)
            sleep(1)


def tilestache():
    parser = argparse.ArgumentParser(description='Create a TileStacge config for all files from a WCS service')
    parser.add_argument('url', help='URL of the WCS service')
    parser.add_argument('-c|--config-path', dest='config_path', default='config.json',
                        help='The path to the config file to create')
    parser.add_argument('-o|--output-path', dest='output_path', default='images',
                        help='The path to the downloaded files')
    parser.add_argument('-s|--substitute', dest='substitute', default=[], nargs='+',
                        help='Rename the files according using re.sub, the arguments are seperated by /.')
    parser.add_argument('--maskband', default=None,
                        help='Add maskband argument to \'provider\' config.')
    args = parser.parse_args()

    output_path = Path(args.output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    contents = parse_capabilities(args.url)

    config = {
      'cache': {
        'name': 'Test'
      },
      'layers': {}
    }

    for content in contents:
        file_name = substitute_file_name('{}.tif'.format(content['id']), args.substitute)
        file_path = output_path / file_name

        config['layers'][file_path.stem] = {
            'provider': {
                'class': 'TileStache.Goodies.Providers.GDAL:Provider',
                'kwargs': {
                    'filename': str(file_path)
                }
            },
            'bounds': {
                'low': 10,
                'high': 20
            }
        }

        if args.maskband:
            config['layers'][file_path.stem]['provider']['kwargs']['maskband'] = int(args.maskband)

        if content.get('upper_corner') and content.get('lower_corner'):
            config['layers'][file_path.stem]['preview'] = {
                'lat': (content['upper_corner'][1] + content['lower_corner'][1]) * .5,
                'lon': (content['upper_corner'][0] + content['lower_corner'][0]) * .5,
                'zoom': 15
            }

    with open(args.config_path, 'w') as fp:
        json.dump(config, fp, indent=2)


def parse_capabilities(service_url):
    capabilities_url = service_url + '?REQUEST=GetCapabilities'
    response = requests.get(capabilities_url)
    root = ET.fromstring(response.content)

    contents = []
    for node in root.findall('./wcs:Contents/wcs:CoverageSummary', namespaces=ns):
        coverage_id = node.find('./wcs:CoverageId', namespaces=ns)
        lower_corner = [float(item) for item in node.find('./ows:WGS84BoundingBox/ows:LowerCorner', namespaces=ns).text.split()]
        upper_corner = [float(item) for item in node.find('./ows:WGS84BoundingBox/ows:UpperCorner', namespaces=ns).text.split()]

        content = {
            'id': coverage_id.text,
            'lower_corner': lower_corner,
            'upper_corner': upper_corner
        }

        contents.append(content)

    return contents


def substitute_file_name(file_name, substitute):
    for pattern, repl in [string.split('/') for string in substitute]:
        file_name = re.sub(pattern, repl, file_name)
    return file_name

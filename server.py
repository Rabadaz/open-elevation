import configparser
import json
import os
import platform

from bottle import route, run, request, response, hook
from gdal_interfaces import GDALTileInterface
from LocationRequest import LocationRequest


class InternalException(ValueError):
    """
    Utility exception class to handle errors internally and return error codes to the client
    """
    pass


class ServerConfig:
    def __init__(self, config_parser):
        if 'server' not in config_parser.sections():
            raise InternalException("Config file incomplete")

        self.HOST = config_parser.get('server', 'host')
        self.PORT = config_parser.getint('server', 'port')
        self.NUM_WORKERS = config_parser.getint('server', 'workers')
        self.URL_ENDPOINT = config_parser.get('server', 'endpoint')
        self.ALWAYS_REBUILD_SUMMARY = config_parser.getboolean('server', 'always-rebuild-summary')
        self.DEFAULT_DATASET = config_parser.get('server', 'default-dataset')
        self.CERTS_FOLDER = config_parser.get('server', 'certs-folder')
        self.CERT_FILE = '%s/cert.crt' % self.CERTS_FOLDER
        self.KEY_FILE = '%s/cert.key' % self.CERTS_FOLDER


print('Reading config file ...')
parser = configparser.ConfigParser()
parser.read('config.ini')

CONFIGURATION = ServerConfig(parser)

"""
Initialize a global interfaces. This can grow quite large, because it has a cache.
"""
interfaces = {}
for ds in parser.sections():
    if ds == "server":
        continue

    data_folder = parser.get(ds, "data-folder")
    interfaces[ds] = GDALTileInterface(data_folder, '%s/summary.json' % data_folder,
                                       parser.getint(ds, "open-interfaces-size"))

    if interfaces[ds].has_summary_json() and not CONFIGURATION.ALWAYS_REBUILD_SUMMARY:
        print('Re-using existing summary JSON')
        interfaces[ds].read_summary_json()
    else:
        print('Creating summary JSON ...')
        interfaces[ds].create_summary_json()


def get_elevation(location_request):
    """
    Get the elevation at point (lat,lng) using the currently opened interface
    :param location_request:
    :return:
    """

    def generateError(error):
        return {
            'latitude': location_request.lat,
            'longitude': location_request.lng,
            'error': error
        }

    try:
        elevation_results = {}
        for data_set in location_request.data_sets:
            if data_set not in interfaces:
                return generateError('No such dataset loaded (%s)' % data_set)
            elevation_results[data_set] = interfaces[data_set].lookup(location_request.lat, location_request.lng)
    except:
        return generateError('No such coordinate (%s, %s)' % (location_request.lat, location_request.lng))
    return {
        'latitude': location_request.lat,
        'longitude': location_request.lng,
        'elevation_results': elevation_results
    }


@hook('after_request')
def enable_cors():
    """
    Enable CORS support.
    :return:
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'


def lat_lng_from_location(location_with_comma):
    """
    Parse the latitude and longitude of a location in the format "xx.xxx,yy.yyy" (which we accept as a query string)
    :param location_with_comma:
    :return:
    """
    try:
        lat, lng = [float(i) for i in location_with_comma.split(',')]
        return LocationRequest(lat, lng)
    except:
        raise InternalException(json.dumps({'error': 'Bad parameter format "%s".' % location_with_comma}))


def query_to_locations():
    """
    Grab a list of locations from the query and turn them into [(lat,lng),(lat,lng),...]
    :return:
    """
    locations = request.query.locations
    if not locations:
        raise InternalException(json.dumps({'error': '"Locations" is required.'}))

    return [lat_lng_from_location(l) for l in locations.split('|')]


def parse_body():
    """
    Grab a list of locations from the body and turn them into LocationRequest objects
    :return:
    """
    try:
        locations = request.json.get('locations', None)
    except Exception:
        raise InternalException(json.dumps({'error': 'Invalid JSON.'}))

    if not locations:
        raise InternalException(json.dumps({'error': '"Locations" is required in the body.'}))

    ret = []
    for body_location in locations:
        try:
            data_sets = [CONFIGURATION.DEFAULT_DATASET]
            if 'datasets' in body_location:
                if hasattr(body_location['datasets'], "__len__"):
                    data_sets = body_location['datasets']
            ret.append(LocationRequest(body_location['latitude'], body_location['longitude'], data_sets=data_sets))
        except KeyError:
            raise InternalException(json.dumps({'error': '"%s" is not in a valid format.' % body_location}))
    return ret


def do_lookup(get_locations_func):
    """
    Generic method which gets the locations  by calling get_locations_func
    and returns an answer ready to go to the client.
    :return:
    """
    try:
        locations = get_locations_func()
        return {'results': [get_elevation(location_request) for location_request in locations]}
    except InternalException as e:
        response.status = 400
        response.content_type = 'application/json'
        return e.args[0]


# For CORS
@route(CONFIGURATION.URL_ENDPOINT, method=['OPTIONS'])
def cors_handler():
    return {}


@route(CONFIGURATION.URL_ENDPOINT, method=['GET'])
def get_lookup():
    """
    GET method. Uses query_to_locations.
    :return:
    """
    return do_lookup(query_to_locations)


@route(CONFIGURATION.URL_ENDPOINT, method=['POST'])
def post_lookup():
    """
    GET method. Uses body_to_locations.
    :return:
    """
    return do_lookup(parse_body)


server = 'gunicorn' if platform.system() != "Windows" else 'wsgiref'

if os.path.isfile(CONFIGURATION.CERT_FILE) and os.path.isfile(CONFIGURATION.KEY_FILE):
    print('Using HTTPS')
    run(host=CONFIGURATION.HOST, port=CONFIGURATION.PORT, server=server, workers=CONFIGURATION.NUM_WORKERS,
        certfile=CONFIGURATION.CERT_FILE, keyfile=CONFIGURATION.KEY_FILE)
else:
    print('Using HTTP')
    run(host=CONFIGURATION.HOST, port=CONFIGURATION.PORT, server=server, workers=CONFIGURATION.NUM_WORKERS)

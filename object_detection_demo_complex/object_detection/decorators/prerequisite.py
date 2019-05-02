from functools import wraps
from utils.api_response import ApiResponse
from bottle import request
from utils.config import config

RESPONSE = {
    'user_id': {
        'message': 'Missing user id',
        'offset': 2
    },
    'app_name': {
        'message': 'Missing application name',
        'offset': 3
    },
    'image': {
        'message': 'Image not found',
        'offset': 4
    }
}


def prerequisite(key):
    if key not in request.params:
        ApiResponse.set_msg(RESPONSE[key]['offset'], RESPONSE[key]['message'])
    else:
        ApiResponse.set_msg(0, 'Success')
    return ApiResponse.get(config["api"]["base_code_decorators"])

def user_id_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = prerequisite('user_id')
        if response['header']['code'] > 0:
            return response
        return f(*args, **kwargs)
    return decorated_function


def app_name_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = prerequisite('app_name')
        if response['header']['code'] > 0:
            return response
        return f(*args, **kwargs)
    return decorated_function


def image_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'image_file' not in request.files:
            ApiResponse.set_msg(RESPONSE['image']['offset'], RESPONSE['image']['message'])
            return ApiResponse.get(config["api"]["base_code_object_detection"])
        return f(*args, **kwargs)
    return decorated_function
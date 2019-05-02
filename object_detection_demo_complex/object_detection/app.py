#!/usr/bin/env python

from bottle import route, run, request, static_file

from decorators.prerequisite import user_id_required, app_name_required, image_required
from services.object_detection_service import ObjectDetectionService
from utils.api_response import ApiResponse
from utils.config import config

import requests, os

#app = Flask(__name__, static_url_path="/" + config["img_dir"], static_folder="storage")
oda = ObjectDetectionService()

@route('/api/image/upload', method='POST')
@user_id_required
@app_name_required
@image_required
def upload_image():
    oda.set_prerequisites(get_query_params())
    file = request.files['image_file']
    return oda.save_image(file)

@route('/api/image/detect_object/<image_name>')
@user_id_required
@app_name_required
def detect_object(image_name):
    oda.set_prerequisites(get_query_params())
    return oda.save_object_detected_image(image_name)

@route('/' + config['img_dir'] + '/<filepath:path>')
def images_static (filepath):
    return static_file(filepath, root='storage')

def get_query_params():
    return {
        "user_id": request.params.get('user_id'),
        "url_root": request.urlparts[0] + '://' + request.urlparts[1] + '/',
        "app_name": request.params.get('app_name')
    }

payload = {'name':os.environ['name']}
agent_url = 'http://agent:5001/api/microservices'
r = requests.put(url=agent_url,data=payload)

run(host='0.0.0.0', port=5000, debug=False)

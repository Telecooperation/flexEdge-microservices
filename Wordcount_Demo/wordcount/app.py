#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask
from flask_restful import Api, Resource, reqparse

import werkzeug
import requests
import os

app = Flask(__name__)
api = Api(app)

class Wordcount(Resource):
    
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
    
    def post(self):
        data = self.parser.parse_args()
        
        if data == "":
            return {
                    'data':'',
                    'message':'No file found',
                    'status':'error'
                    }
            
        text = data['file'].read()
        
        #send alive msg to agent
        payload = {'name':os.environ['name']}
        agent_url = 'http://agent:5001/api/microservices'
        r = requests.put(url=agent_url,data=payload)
        
        return len(text.split())
        
        
        

api.add_resource(Wordcount, '/wordcount')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4001)
import os
import json

CWD_PATH = os.getcwd()
PATH_TO_CONFIG = os.path.join(CWD_PATH, 'config.json')
with open(PATH_TO_CONFIG , 'r') as f:
    config = json.load(f)
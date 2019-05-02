# Object-Detector-App

A real-time object recognition application using [Google's TensorFlow Object Detection API](https://github.com/tensorflow/models/tree/master/object_detection) and [OpenCV](http://opencv.org/).

## Getting Started
1. `conda env create -f environment.yml`
2. `python object_detection_app.py` 
    Optional arguments (default value):
    * Device index of the camera `--source=0`
    * Width of the frames in the video stream `--width=480`
    * Height of the frames in the video stream `--height=360`
    * Number of workers `--num-workers=2`
    * Size of the queue `--queue-size=5`

## Tests
```
pytest -vs utils/
```

## Requirements
- [Anaconda / Python 3.5](https://www.continuum.io/downloads)
- [TensorFlow 1.2](https://www.tensorflow.org/)
- [OpenCV 3.0](http://opencv.org/)

## Notes
- OpenCV 3.1 might crash on OSX after a while, so that's why I had to switch to version 3.0. See open issue and solution [here](https://github.com/opencv/opencv/issues/5874).
- Moving the `.read()` part of the video stream in a multiple child processes did not work. However, it was possible to move it to a separate thread.

## Copyright

See [LICENSE](LICENSE) for details.
Copyright (c) 2017 [Dat Tran](http://www.dat-tran.com/).

## Services

- base_url: http://IP-ADDRESS-OF-YOUR-MACHINE:5000/
- USER_ID: mobile user id 
- APP_NAME: objectdetection

### Detect Object

    curl --request GET \
      --url 'http://{{base_url}}/api/image/detect_object/[IMAGE_NAME]?user_id=[USER_ID]&app_name=[APP_NAME]'
  
### Upload image  

    curl --request POST \
      --url 'http://{{base_url}}/api/image/upload?user_id=[USER_ID]&app_name=[APP_NAME]' \
      --header 'content-type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW' \
      --form image_file=[IMAGE_FILE]

### Get latest images

    curl --request GET \
      --url 'http://{{base_url}}/api/image?user_id=[USER_ID]&app_name=[APP_NAME]'
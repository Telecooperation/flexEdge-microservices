import cv2
from flask import Flask, request, send_from_directory, send_file
import time

app = Flask(__name__)

def convertToRGB(img): 
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

def shrink_img(img):
    height, width = img.shape[:2]
    max_height = 600
    max_width = 800
    if max_height < height or max_width < width:
        scaling_factor = max_height / float(height)
        if max_width/float(width) < scaling_factor:
            scaling_factor = max_width / float(width)
        img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
    return img

@app.route('/detect_face', methods=['POST'])
def detect_face():
    file = request.files['file']
    file.save('input.jpg')
    test1 = shrink_img(cv2.imread('input.jpg'))
    gray_img = cv2.cvtColor(test1, cv2.COLOR_BGR2GRAY)
    haar_face_cascade = cv2.CascadeClassifier('lbpcascade_frontalface.xml')
    faces = haar_face_cascade.detectMultiScale(gray_img, scaleFactor=1.2, minNeighbors=5);
    t1_start = time.time()
    for (x, y, w, h) in faces:
        cv2.rectangle(test1, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.imwrite('output.jpg', test1)
    return send_file('output.jpg', mimetype='image/jpeg')
app.run(host="0.0.0.0", port=5000)
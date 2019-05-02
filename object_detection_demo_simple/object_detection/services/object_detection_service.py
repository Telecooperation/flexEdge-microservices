import glob
import os
import uuid
from multiprocessing import Queue, Pool

import numpy as np
import scipy.misc

# https://github.com/tensorflow/tensorflow/issues/7778#issuecomment-281678077
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
import tensorflow as tf
from skimage.io import imread

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
from utils.api_response import ApiResponse
from utils.config import config
from werkzeug.utils import secure_filename
from utils.logger import Logger
from utils.mkdir_p import mkdir_p
from PIL import Image


class ObjectDetectionService:
    CWD_PATH = os.getcwd()

    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    MODEL_NAME = 'ssd_mobilenet_v1_coco'
    PATH_TO_CKPT = os.path.join(CWD_PATH, 'object_detection', MODEL_NAME, 'frozen_inference_graph.pb')

    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = os.path.join(CWD_PATH, 'object_detection', 'data', 'mscoco_label_map.pbtxt')

    NUM_CLASSES = 90

    # Loading label map
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                                use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    LOG_TAG = 'ObjectDetectionService'

    ALLOWED_EXTENSIONS = set(config["storage"]["allowed_extensions"])
    SIZE = 1024, 768

    def __init__(self):
        self.input_q = Queue(maxsize=5)
        self.output_q = Queue(maxsize=5)
        self.pool = Pool(2, self.worker, (self.input_q, self.output_q))

    def set_prerequisites(self, params):
        try:
            Logger.info(ObjectDetectionService.LOG_TAG, params)
            self.url_root = params.get("url_root")
            self.user_id = params.get("user_id")
            self.app_name = params.get("app_name")
            self.path_to_image = os.path.join(ObjectDetectionService.CWD_PATH, 'storage', self.user_id,
                                              self.app_name)
            self.path_to_upload_original = os.path.join(self.path_to_image, config["storage"]["upload_dir"],
                                                        config["storage"]["original_dir"])
            self.path_to_upload_thumbnail = os.path.join(self.path_to_image, config["storage"]["upload_dir"],
                                                         config["storage"]["thumbnail_dir"])
            self.path_to_output = os.path.join(self.path_to_image, config["storage"]["output_dir"])

            if not os.path.isdir(self.path_to_image):
                mkdir_p(self.path_to_image)

            if not os.path.isdir(self.path_to_upload_original):
                mkdir_p(self.path_to_upload_original)

            if not os.path.isdir(self.path_to_upload_thumbnail):
                mkdir_p(self.path_to_upload_thumbnail)

            if not os.path.isdir(self.path_to_output):
                mkdir_p(self.path_to_output)
        except Exception as e:
            ApiResponse.set_msg(1, "Internal server error")
            Logger.error(ObjectDetectionService.LOG_TAG, "Exception: {error}".format(error=str(e)))
            return ApiResponse.get(config["api"]["base_code_object_detection"])

    def detect_objects(self, image_np, sess, detection_graph):
        # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image_np, axis=0)
        image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

        # Each box represents a part of the image where a particular object was detected.
        boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

        # Each score represent how level of confidence for each of the objects.
        # Score is shown on the result image, together with the class label.
        scores = detection_graph.get_tensor_by_name('detection_scores:0')
        classes = detection_graph.get_tensor_by_name('detection_classes:0')
        num_detections = detection_graph.get_tensor_by_name('num_detections:0')

        # Actual detection.
        (boxes, scores, classes, num_detections) = sess.run(
            [boxes, scores, classes, num_detections],
            feed_dict={image_tensor: image_np_expanded})

        # Visualization of the results of a detection.
        vis_util.visualize_boxes_and_labels_on_image_array(
            image_np,
            np.squeeze(boxes),
            np.squeeze(classes).astype(np.int32),
            np.squeeze(scores),
            ObjectDetectionService.category_index,
            use_normalized_coordinates=True,
            line_thickness=8)
        return image_np

    def worker(self, input_q, output_q):
        # Load a (frozen) Tensorflow model into memory.
        detection_graph = tf.Graph()
        with detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(ObjectDetectionService.PATH_TO_CKPT, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

            sess = tf.Session(graph=detection_graph)

        while True:
            frame = input_q.get()
            output_q.put(self.detect_objects(frame, sess, detection_graph))

        sess.close()

    # Error code: 2 to 15
    def save_object_detected_image(self, image_name):
        try:
            Logger.info(ObjectDetectionService.LOG_TAG, "Image name received: {image_name}".format(image_name=image_name))

            if(image_name):
                image_path = os.path.join(self.path_to_upload_original, image_name)
                image_file = imread(image_path)
                self.input_q.put(image_file)

                scipy.misc.imsave(os.path.join(self.path_to_output, image_name), self.output_q.get())

                ApiResponse.set_body(0, "Success", { "image_url": ObjectDetectionService.get_image_url(
                    image_name,
                    self.user_id,
                    self.app_name,
                    config["storage"]["output_dir"],
                    self.url_root
                )})
            else:
                ApiResponse.set_msg(2,"Image name is required")
        except FileNotFoundError as e:
            ApiResponse.set_msg(3, "Image not found. Please try it after uploading the image.")
            Logger.error(ObjectDetectionService.LOG_TAG, "Exception: {error}".format(error=str(e)))
        except Exception as e:
            ApiResponse.set_msg(4, "Internal server error")
            Logger.error(ObjectDetectionService.LOG_TAG, "Exception: {error}".format(error=str(e)))
        return ApiResponse.get(config["api"]["base_code_object_detection"])

    # Error code: 16 to 30
    def save_image(self, image_file):
        try:
            # submit a empty part without filename
            if image_file.filename == '':
                ApiResponse.set_msg(16, "Image file is required")
            elif image_file and ObjectDetectionService.allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                unique_filename = ObjectDetectionService.get_unique_filename(filename)
                image_file.save(os.path.join(self.path_to_upload_original, unique_filename))
                response = self.resize_image(unique_filename)
                if(response['header']['code'] == 0):
                    ApiResponse.set_body(0, "Image uploaded successfully", {
                        "image_name": response['body']['image_name']
                    })
                else:
                    return response
            else:
                ApiResponse.set_msg(17, "Allowed extensions are: " + ObjectDetectionService.ALLOWED_EXTENSIONS)

        except Exception as e:
            ApiResponse.set_msg(18, "Internal server error")
            Logger.error(ObjectDetectionService.LOG_TAG, "Exception: {error}".format(error=str(e)))
        return ApiResponse.get(config["api"]["base_code_object_detection"])

    # Get the latest image for a given user (at max retrieval_limit)
    # @link https://stackoverflow.com/a/39327156
    # Error code: 31 to 45
    def get_lastest_images(self):
        try:
            list_of_files = glob.iglob(self.path_to_upload_thumbnail + '/*')  # * means all if need specific format then *.csv
            files = sorted(list_of_files, key=os.path.getctime, reverse=True)
            if len(files):
                latest_images = []
                for file in files:
                    image_name = os.path.basename(file)
                    latest_images.append(ObjectDetectionService.get_image_url(
                        image_name,
                        self.user_id,
                        self.app_name,
                        os.path.join(config["storage"]["upload_dir"], config["storage"]["thumbnail_dir"]),
                        self.url_root
                    ))
                    if len(latest_images) == config["storage"]["retrieval_limit"]:
                        break
                ApiResponse.set_body(0, "Records found", {"latest_images": latest_images})
            else:
                ApiResponse.set_msg(32, "Record not found")

        except Exception as e:
            ApiResponse.set_msg(33, "Internal server error")
            Logger.error(ObjectDetectionService.LOG_TAG, "Exception: {error}".format(error=str(e)))
        return ApiResponse.get(config["api"]["base_code_object_detection"])

    # Resize image
    # https://stackoverflow.com/a/273962
    # Error code: 46 to 60
    def resize_image(self, image_name):
        try:
            im = Image.open(os.path.join(self.path_to_upload_original, image_name))
            im.thumbnail(ObjectDetectionService.SIZE, Image.ANTIALIAS)
            im.save(os.path.join(self.path_to_upload_thumbnail , image_name) , "JPEG")
            ApiResponse.set_body(0, "Image resized successfully", {
                "image_name": image_name
            })
        except IOError:
            ApiResponse.set_msg(46, "Cannot create thumbnail for '%s'" % image_name)

        return ApiResponse.get(config["api"]["base_code_object_detection"])

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ObjectDetectionService.ALLOWED_EXTENSIONS

    @staticmethod
    def get_unique_filename(file):
        file_extension = os.path.splitext(file)[1]
        return str(uuid.uuid4()) + file_extension

    @staticmethod
    def get_image_url(image_name, user_id, app_name, directory, url_root):
        image_url = config["storage"]["image_url"].format(
            url_root=url_root,
            img_dir=config["img_dir"],
            user_id=user_id,
            app_name=app_name,
            directory=directory,
            image_name=image_name
        )
        return image_url

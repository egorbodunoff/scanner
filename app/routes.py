from flask import current_app as app, render_template, jsonify, request, Response
from app.api.qr_api import read_from_port
from app.api.camera_api import *
from app.api.video_camera_api import *
from app.image_processing.image_sharpness import calculate_sharpness
from app.detection.inference_yolo5_examples import predict_my_version
from app.detection.generate_json_with_filenames_examples import generate_json
from app.detection.insert_result_into_empty_examples import insert_result
from app.detection.filter_json_by_area_examples import filter_json
from logger_config import logger
from datetime import datetime
import threading
import cv2
import json
import os



camera = CameraAPI()
video_camera = VideoCamera(camera)
folder_name = None
image_name = None
port = '/dev/ttyACM0'
lock = threading.Lock()


def qr_reader():
    global folder_name
    while True:
        try:
            qr_data = read_from_port(port)
            if qr_data != folder_name:
                logger.info(f'qr data receive - {qr_data}')

                folder_name = qr_data.strip()
                folder_path = os.path.join('app/static/', folder_name)

                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    logger.info(f'folder {folder_path} created')


        except Exception as e:
            logger.error(f'read qr error {str(e)}')
    

def register_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/activate_port', methods=['POST'])
    def activate_port():
        global folder_name

        try:
            qr_data = read_from_port(port)
            if qr_data:
                folder_name = qr_data.strip()
                folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)

                return jsonify({
                    'QR Code': qr_data
                })
            else:
                return jsonify({'error': 'No data read from port'}), 500
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @app.route('/capture_image', methods=['POST'])
    def capture_image():
        global image_name, folder_name

        if not folder_name:
            logger.warning('/capture_image - No qr data')
            return jsonify({'error': 'No qr data'}), 500
        
        image_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        try:
            with camera:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], folder_name, f'{ image_name}.bmp')
                file = os.path.join('static', folder_name, f'{image_name}.bmp')

                camera.capture_frame(filepath)
                logger.info(f'/capture_image - image is saved to the path {filepath}')

                return jsonify({
                    'message': 'Image captured successfully.',
                    'file_path': file
                    }), 200
            
        except Exception as e:
            logger.error(f'/capture_image - capture image error {str(e)}')
            return jsonify({'error': str(e)}), 500
        



    @app.route('/parameters', methods=['GET'])
    def get_parameters():
        try:
            with camera:
                exposure_time = camera.ExposureTime
                gamma = camera.Gamma
                width = camera.Width
                height = camera.Height
                offset_x = camera.OffsetX
                offset_y = camera.OffsetY

                parameters = {
                    'ExposureTime': exposure_time,
                    'Gamma': gamma,
                    'Width': width,
                    'Height': height,
                    'OffsetX': offset_x,
                    'OffsetY': offset_y
                }
                logger.info('/parameters - parameters have been received')

                return jsonify(parameters), 200

        except Exception as e:
            logger.error(f'/parameters - error {str(e)}')
            return jsonify({'error': str(e)}), 500
        

    @app.route('/parameter/<param>', methods=['POST'])
    def handle_parameter(param):
        try:
            with camera:
                new_value = int(request.json)

                if new_value is not None:
                    setattr(camera, param, new_value)
                    logger.info('/parameter/<param> - parameters are set')

                    return jsonify({'message': f'{param} updated successfully'}), 200
                else:
                    logger.warning('/parameter/<param> - parameters are not set')
                    return jsonify({'error': f'Invalid value provided for {param}'}), 400
                
        except Exception as e:
            logger.error(f'/parameter/<param> - error {str(e)}')
            return jsonify({'error': str(e)}), 500
        

    @app.route('/calculate_sharpness', methods=['POST'])
    def calculate_sharpness_route():
        global folder_name, image_name

        if not folder_name or not image_name:
            logger.warning('/calculate_sharpness - No image')
            return jsonify({'error': 'No image'}), 500

        try:
            image = cv2.imread(f'app/static/{folder_name}/{image_name}.bmp')
            sharpness = calculate_sharpness(image)
            logger.info(f'/calculate_sharpness - sharpness is {sharpness}')

            return jsonify({"sharpness": sharpness}), 200
        
        except Exception as e:
            logger.error(f'/calculate_sharpness error - {str(e)}')
            return jsonify({"error": str(e)}), 500
        

    @app.route('/rundetection', methods=['POST'])
    def run_detection():
        global image_name, folder_name

        if not folder_name or not image_name:
            logger.warning('/rundetection - No image')
            return jsonify({'error': 'No image'}), 500

        try:    
            filepath = f'app/static/{folder_name}/{image_name}.bmp'
            print(filepath)
            generate_json(filepath)

            predict_my_version(
                model_type='yolov5',
                model_path='app/detection/results_1_28_02_23_medium_1200_without_slice/kaggle/working/yolov5/runs/train/results_1/weights/best.pt',
                source=filepath,
                model_device='cuda',
                model_confidence_threshold=0.0,
                slice_height=2000,
                slice_width=1800,
                overlap_height_ratio=0.03,
                overlap_width_ratio=0.03,
                novisual=False,
                postprocess_type='NMS',
                postprocess_match_metric='IOS',
                dataset_json_path='empty_only_filenames.json',
                verbose=1
            )
            insert_result()
            filter_json()
            score = []
    
            with open('full_result.json') as f:
                data = json.load(f)
                logger.info('/rundetection - full_result.json is read')

                for im in data['annotations']:
                    score.append(im['score'])
                logger.info(f'/rundetection - score received {max(score)}')

            
            logger.info(f'/rundetection - score {max(score)}, for image static/exp/visuals/{image_name}.png')
            return jsonify({
                "score": str(max(score)),
                'file_path': f'static/exp/visuals/{image_name}.png'
                }), 200
        
        except Exception as e:
            logger.error(f'/rundetection error - {str(e)}')
            return jsonify({"error": str(e)}), 500
        

    @app.route('/qr_data', methods=['GET'])
    def get_qr_data():
       try:
           logger.info(f'/qr_data folder name is {folder_name}')
           if folder_name is not None:
               logger.info(f'/qr_data - update form for folder name')
               return jsonify({"QR Code": folder_name}), 200
           
           else:
               return jsonify({"error": "No QR data available"}), 404
           
       except Exception as e:
           logger.error(f'/qr_data - {str(e)}')
           return jsonify({"error": str(e)}), 500
        

    @app.route('/video_feed')
    def video_feed():
        def gen_frame(camera):
            while True:
                frame = camera.get_frame_bytes()
                if frame:
                    yield (b'--frame\r\n'
                        b'Content-Type: image/bmp\r\n\r\n' + frame + b'\r\n\r\n')
                else:
                    break
        return Response(gen_frame(video_camera), mimetype='multipart/x-mixed-replace; boundary=frame')


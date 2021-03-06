from app.api import bp
# from app.api.keras_open_nsfw import predict
import os
from flask import request
import time
from app.main.utils import make_response, is_base64
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO
import base64
from tensorflow.keras.models import load_model
import numpy as np
from skimage import transform
# import keras.backend.tensorflow_backend as tb
# tb._SYMBOLIC_SCOPE.value = True


CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
# MODEL_PATH = os.path.join(CURRENT_PATH, 'keras_open_nsfw/nsfw_mobilenet2.h5')
IMAGE_UPLOAD_FOLDER = os.path.join(CURRENT_PATH, '../../logs/image_upload')
IMAGE_PATH = os.path.join(CURRENT_PATH, 'image.jpg')
IMAGE_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
FILENAME = ''
NEW_MODEL_PATH = os.path.join(CURRENT_PATH, 'keras_open_nsfw/lakshaychhabra_weights.h5')

if not os.path.exists(IMAGE_UPLOAD_FOLDER):
    os.mkdir(IMAGE_UPLOAD_FOLDER)

# model = predict.load_model(MODEL_PATH)
# predict.classify(model, IMAGE_PATH)
new_model = load_model(NEW_MODEL_PATH)


@bp.route('/nsfw/check', methods=['GET', 'POST'])
def classify_photo_nsfw():
    if request.method == 'GET':
        return make_response(False, description='The get method is not available')

    if request.content_type.startswith('multipart/form-data'):
        # check if the post request has the file part
        if 'file' not in request.files:
            return make_response(False, description='File not found!')
        image_file = request.files['file']
        image_file.stream.seek(0)
        image_file.save(IMAGE_PATH)
        FILENAME = secure_filename(image_file.filename)

    elif request.content_type.startswith('application/json'):
        data = request.json
        if 'base64_image' not in data:
            return make_response(False, description='Base64 image not found!')
        if 'filename' not in data:
            return make_response(False, description='Filename not found!')
        base64_image = data['base64_image'].replace('data:image/jpeg;base64,', '')
        if not isinstance(base64_image, str):
            return make_response(False, description='Base64 string format is incorrect')

        try:
            imgdata = base64.b64decode(base64_image)
            with open(IMAGE_PATH, 'wb') as f:
                f.write(imgdata)
            FILENAME = data['filename']
        except:
            return make_response(False, description='Decode image is failed')
    else:
        return make_response(False, description='Content type is not avaliable')

    # check filename
    # if user does not select file, browser also
    # submit an empty part without filename
    if FILENAME == '' or not allowed_file(FILENAME):
        return make_response(False, description='Invalid file format!')

    # test image
    try:
        Image.open(IMAGE_PATH)
    except:
        return make_response(False, description='Invalid image data!')

    # Prediction image
    start = time.time()
    # old model
    # dict_result = predict.classify(model, IMAGE_PATH)
    # softmax = dict_result[IMAGE_PATH]
    # label = max(softmax, key=softmax.get)
    # result = {'NSFW': 0}
    # if label == 'porn' or label == 'hentai':
    #     result['NSFW'] = 1
    # result['Score'] = softmax

    # new model
    image = load(IMAGE_PATH)
    dict_result = new_model.predict(image)
    softmax = dict_result[0]
    result = {'NSFW': 0}
    if len(softmax) == 3:
        neural_score = round(float(softmax[0]), 3)
        porn_score = round(float(softmax[1]), 3)
        sexy_score = 1 - neural_score - porn_score
        if porn_score > neural_score and porn_score > sexy_score:
            result['NSFW'] = 1
        result['Score'] = {'Neural': neural_score, 'Porn': porn_score, 'Sexy': sexy_score}
    else:
        return make_response(False, description='Model cannot prediction image')

    basename, ext = os.path.splitext(FILENAME)
    basename += time.strftime("_%Y%m%d_%H%M%S")
    basename += "_SFW" if result['NSFW'] == 0 else '_NSFW'
    FILENAME = basename + ext

    im = Image.open(IMAGE_PATH)
    im_resize = im.resize((224, int(im.height * 224 / im.width)))
    im_resize.save(os.path.join(IMAGE_UPLOAD_FOLDER, FILENAME))
    print(f'Model classify in {time.time() - start} seconds. Result: {result}. File: {FILENAME}')

    return make_response(True, result, '')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in IMAGE_ALLOWED_EXTENSIONS


def load(filename):
    np_image = Image.open(filename)
    np_image = np.array(np_image).astype('float32') / 255
    np_image = transform.resize(np_image, (224, 224, 3))
    np_image = np.expand_dims(np_image, axis=0)
    # img=mpimg.imread(filename)
    return np_image

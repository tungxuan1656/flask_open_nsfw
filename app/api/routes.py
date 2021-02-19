from app.api import bp
from app.api.keras_open_nsfw import predict
import os
from flask import request
import time
from app.main.utils import make_response
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO


CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_PATH, 'keras_open_nsfw/nsfw_mobilenet2.h5')
IMAGE_UPLOAD_FOLDER = os.path.join(CURRENT_PATH, '../../logs/image_upload')
IMAGE_PATH = os.path.join(CURRENT_PATH, 'image.jpg')
IMAGE_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

if not os.path.exists(IMAGE_UPLOAD_FOLDER):
    os.mkdir(IMAGE_UPLOAD_FOLDER)

model = predict.load_model(MODEL_PATH)
predict.classify(model, IMAGE_PATH)


@bp.route('/nsfw/check', methods=['GET', 'POST'])
def classify_photo_nsfw():
    if request.method == 'GET':
        return make_response(False, description='The get method is not available')

    # check if the post request has the file part
    if 'file' not in request.files:
        return make_response(False, description='File not found!')
    image_file = request.files['file']

    # if user does not select file, browser also
    # submit an empty part without filename
    if image_file.filename == '':
        return make_response(False, description='File not found!')

    if image_file and allowed_file(image_file.filename):
        pass
    else:
        return make_response(False, description='Invalid file format!')

    image_file.stream.seek(0)
    image_file.save(IMAGE_PATH)

    start = time.time()
    dict_result = predict.classify(model, IMAGE_PATH)

    softmax = dict_result[IMAGE_PATH]
    label = max(softmax, key=softmax.get)
    result = {'NSFW': 0}
    if label == 'porn' or label == 'hentai':
        result['NSFW'] = 1

    filename = secure_filename(image_file.filename)
    basename, ext = os.path.splitext(filename)
    basename += time.strftime("_%Y%m%d_%H%M%S")
    basename += "_SFW" if result['NSFW'] == 0 else '_NSFW'
    filename = basename + ext
    image_file.stream.seek(0)
    # image_file.save(os.path.join(IMAGE_UPLOAD_FOLDER, filename))
    image_bytes = BytesIO(image_file.stream.read())
    im = Image.open(image_bytes)
    im_resize = im.resize((224, int(im.height * 224 / im.width)))
    im_resize.save(os.path.join(IMAGE_UPLOAD_FOLDER, filename))
    print(f'Model classify in {time.time() - start} seconds. Result: {result}. File: {filename}')

    return make_response(True, result, '')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in IMAGE_ALLOWED_EXTENSIONS

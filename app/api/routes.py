from app.api import bp
from app.api.keras_open_nsfw import predict
import os
from flask import request, jsonify
import time
from app.main.utils import make_response, is_base64
import base64


cwd = os.getcwd()
model = predict.load_model(f'{cwd}/app/api/keras_open_nsfw/nsfw_mobilenet2.h5')
predict.classify(model, f'{cwd}/app/api/image.jpg')


@bp.route('/classify_nsfw', methods=['GET', 'POST'])
def classify_photo_nsfw():
    if request.method == 'GET':
        return make_response(False, description='The get method is not available')

    data = request.json
    if 'base64_image' not in data:
        return make_response(False, description='Image is empty!')

    base64_image = data['base64_image'].replace('data:image/jpeg;base64,', '')
    if not isinstance(base64_image, str) or not is_base64(base64_image):
        return make_response(False, description='Base64 string format is incorrect')

    imgdata = base64.b64decode(base64_image)
    image_path = './app/api/image.jpg'
    with open(image_path, 'wb') as f:
        f.write(imgdata)

    # start = time.time()
    dict_result = predict.classify(model, image_path)
    # print(f'Model classify in {time.time() - start} seconds')
    softmax = dict_result[image_path]
    label = max(softmax, key=softmax.get)
    result = {'NSFW': 0}
    if label == 'porn' or label == 'hentai':
        result['NSFW'] = 1
    # result['Classify'] = {'Label': label, 'Detail': softmax}
    return make_response(True, result, '')

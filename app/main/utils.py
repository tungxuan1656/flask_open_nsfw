from typing import Dict
from flask import json, jsonify
import base64


def make_response(is_success=True, params=None, description=''):
    if is_success:
        response = dict()
        response['Result'] = 'Success'
        response['Description'] = description
        if params is not None and isinstance(params, dict):
            response.update(params)

        return jsonify(response)
    else:
        r = jsonify({'Result': 'Failed', 'Description': description})
        print(r)
        return r


def is_base64(sb):
    try:
        if isinstance(sb, str):
            # If there's any unicode here, an exception will be thrown and the function will return false
            sb_bytes = bytes(sb, 'ascii')
        elif isinstance(sb, bytes):
            sb_bytes = sb
        else:
            raise ValueError("Argument must be string or bytes")
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False

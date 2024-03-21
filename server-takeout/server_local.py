import re

from flask import Flask, request, make_response
from datetime import datetime
import os

app = Flask(__name__)
IMG_PATH = "C:/useful_frame/"


@app.route('/')
def local_data():
    List = []
    datanames = os.listdir(IMG_PATH)
    for i in datanames:
        List.append(re.split(r'[---]', os.path.splitext(i)[0]))
    numbers_new = []
    for i in List:
        numbers = list(map(int, i))
        numbers_new.append(numbers)
    result = str(numbers_new)
    return result


def local():
    app.run()


@app.route('/<string:filename>', methods=['GET'])
def display_img(filename):
    request_begin_time = datetime.today()
    print("request_begin_time", request_begin_time)
    if request.method == 'GET':
        if filename is None:
            pass
        else:
            image_data = open(IMG_PATH + filename, "rb").read()
            response = make_response(image_data)
            response.headers['Content-Type'] = 'image/jpg'
            return response
    else:
        pass

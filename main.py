from flask import Flask, render_template, request, make_response
from flask_restful import Api
import argparse
import logging
import json
from controller import Controller
from persistent_storage import PersistentStorage
import time
import random


app = Flask(__name__,
            static_folder="./html/static",
            template_folder="./html")
api = Api(app)

@app.route('/')
def index():
    storage = PersistentStorage()
    data = storage.get_all_data()
    return render_template('index.html', data=data)


@app.route('/create', methods=['POST'])
def add_relmon():
    relmon = json.loads(request.data.decode('utf-8'))
    relmon['status'] = 'new'
    relmon['id'] = int(time.time())
    relmon['secret_hash'] = '%032x' % (random.getrandbits(128))
    for category in relmon['categories']:
            category['lists']['reference'] = [{'name': x, 'file_name': '-', 'file_status': 'initial', 'file_size': 0} for x in category['lists']['reference']]
            category['lists']['target'] = [{'name': x, 'file_name': '-', 'file_status': 'initial', 'file_size': 0} for x in category['lists']['target']]

    storage = PersistentStorage()
    storage.create_relmon(relmon)
    return output_text({'message': 'OK'})


def output_text(data, code=200, headers=None):
    """
    Makes a Flask response with a plain text encoded body
    """
    resp = make_response(json.dumps(data, indent=2, sort_keys=True), code)
    resp.headers.extend(headers or {})
    resp.headers['Content-Type'] = 'application/json'
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/update_file', methods=['POST'])
def update_file():
    data = json.loads(request.data.decode('utf-8'))
    storage = PersistentStorage()
    relmon = storage.get_relmon_by_id(data['relmon_id'])
    for category in relmon['categories']:
        if category['name'] == data['category']:
            for relval in category['lists'][data['list_type']]:
                if relval['name'] == data['relval_name']:
                    relval['file_name'] = data['file_name']
                    relval['file_status'] = data['file_status']
                    relval['file_size'] = data['file_size']
                    storage.update_relmon(relmon)
                    break

            break
    return output_text({'message': 'OK'})


@app.route('/update_status', methods=['POST'])
def update_status():
    data = json.loads(request.data.decode('utf-8'))
    storage = PersistentStorage()
    relmon = storage.get_relmon_by_id(data['relmon_id'])
    relmon['status'] = data['relmon_status']
    storage.update_relmon(relmon)
    return output_text({'message': 'OK'})


def run_flask():

    parser = argparse.ArgumentParser(description='Stats2')
    parser.add_argument('--port',
                        help='Port, default is 8001')
    parser.add_argument('--host',
                        help='Host IP, default is 127.0.0.1')
    parser.add_argument('--debug',
                        help='Debug mode',
                        action='store_true')
    args = vars(parser.parse_args())
    port = args.get('port', None)
    host = args.get('host', None)
    debug = args.get('debug', False)
    if not port:
        port = 8001

    if not host:
        host = '127.0.0.1'

    app.run(host=host,
            port=int(port),
            debug=debug,
            threaded=True)


if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)
    controller = Controller()
    run_flask()
    controller.stop()
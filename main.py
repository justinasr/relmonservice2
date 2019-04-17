from flask import Flask, render_template, request, make_response
from flask_restful import Api
import argparse
import logging
import json
from controller import Controller
from persistent_storage import PersistentStorage
import time
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from logging import handlers


app = Flask(__name__,
            static_folder="./html/static",
            template_folder="./html")
api = Api(app)
scheduler = BackgroundScheduler()
controller = Controller()


@app.route('/')
def index():
    storage = PersistentStorage()
    data = storage.get_all_data()
    for relmon in data:
        relmon['last_update'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(relmon.get('last_update', 0)))
        for category in relmon.get('categories'):
            category['reference'] = [{'name': (x.get('name', '')),
                                      'file_name': x.get('file_name', ''),
                                      'file_url': x.get('file_url', ''),
                                      'file_size': x.get('file_size', 0),
                                      'status': x.get('status', '')} for x in category['reference']]

            category['reference_status'] = {}
            category['reference_total_size'] = 0
            for relmon in category['reference']:
                category['reference_total_size'] += relmon.get('file_size', 0)
                relmon_status = relmon.get('status', '<unknown>')
                if relmon_status not in category['reference_status']:
                    category['reference_status'][relmon_status] = 0

                category['reference_status'][relmon_status] = category['reference_status'][relmon_status] + 1

            category['target'] = [{'name': (x.get('name', '')),
                                   'file_name': x.get('file_name', ''),
                                   'file_url': x.get('file_url', ''),
                                   'file_size': x.get('file_size', 0),
                                   'status': x.get('status', '')} for x in category['target']]

            category['target_status'] = {}
            category['target_total_size'] = 0
            for relmon in category['target']:
                category['target_total_size'] += relmon.get('file_size', 0)
                relmon_status = relmon.get('status', '<unknown>')
                if relmon_status not in category['target_status']:
                    category['target_status'][relmon_status] = 0

                category['target_status'][relmon_status] = category['target_status'][relmon_status] + 1

    data.sort(key=lambda x: x.get('id', -1))
    return render_template('index.html', data=data)


@app.route('/create', methods=['POST'])
def add_relmon():
    relmon = json.loads(request.data.decode('utf-8'))
    if 'id' not in relmon:
        relmon['id'] = int(time.time())

    controller.reset_relmon(relmon)
    storage = PersistentStorage()
    storage.create_relmon(relmon)
    return output_text({'message': 'OK'})


@app.route('/reset', methods=['POST'])
def reset_relmon():
    data = json.loads(request.data.decode('utf-8'))
    if 'id' in data:
        storage = PersistentStorage()
        relmon = storage.get_relmon_by_id(data['id'])
        controller.reset_relmon(relmon)
        storage.update_relmon(relmon)
        return output_text({'message': 'OK'})

    return output_text({'message': 'No ID'})


@app.route('/delete', methods=['DELETE'])
def delete_relmon():
    relmon = json.loads(request.data.decode('utf-8'))
    storage = PersistentStorage()
    storage.delete_relmon(relmon['id'])
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


@app.route('/update', methods=['POST'])
def update_info():
    data = json.loads(request.data.decode('utf-8'))
    storage = PersistentStorage()
    relmon = storage.get_relmon_by_id(data['id'])
    if relmon.get('secret_hash', 'NO_HASH1') != data.get('secret_hash', 'NO_HASH2'):
        return output_text({'message': 'Wrong secret hash'})

    old_status = relmon.get('status')
    relmon['categories'] = data['categories']
    relmon['status'] = data['status']
    if relmon['status'] == 'running' and relmon['status'] != old_status:
        tick()

    logger = logging.getLogger('logger')
    logger.info('Update for %s (%s). Status is %s' % (relmon['name'],
                                                      relmon['id'],
                                                      relmon['status']))
    storage.update_relmon(relmon)
    return output_text({'message': 'OK'})


@app.route('/tick')
def controller_tick():
    for job in scheduler.get_jobs():
        job.modify(next_run_time=datetime.now())

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


def tick():
    controller.tick()


def setup_logging():
    # Max log file size - 5Mb
    max_log_file_size = 1024 * 1024 * 5
    max_log_file_count = 10
    log_file_name = 'logs/log.log'
    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)
    handler = handlers.RotatingFileHandler(log_file_name,
                                           'a',
                                           max_log_file_size,
                                           max_log_file_count)
    formatter = logging.Formatter(fmt='[%(asctime)s][%(levelname)s] %(message)s',
                                  datefmt='%d/%b/%Y:%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == '__main__':
    setup_logging()
    scheduler.add_executor('processpool')
    scheduler.add_job(tick, 'interval', seconds=600)
    scheduler.start()
    run_flask()
    scheduler.shutdown()

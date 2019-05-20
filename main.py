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
    data = None
    while not data:
        try:
            data = storage.get_all_data()
        except:
            time.sleep(1)

    for relmon in data:
        relmon['last_update'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(relmon.get('last_update', 0)))
        relmon['done_size'] = 0
        relmon['total_size'] = 0
        relmon['downloaded_relvals'] = 0
        relmon['total_relvals'] = 0
        for category in relmon.get('categories'):
            category['reference'] = [{'name': (x.get('name', '')),
                                      'file_name': x.get('file_name', ''),
                                      'file_url': x.get('file_url', ''),
                                      'file_size': x.get('file_size', 0),
                                      'status': x.get('status', '')} for x in category['reference']]

            category['reference_status'] = {}
            category['reference_total_size'] = 0
            relmon['total_relvals'] = relmon['total_relvals'] + len(category['reference']) + len(category['target'])
            for relval in category['reference']:
                category['reference_total_size'] += relval.get('file_size', 0)
                relmon_status = relval['status']
                if relmon_status not in category['reference_status']:
                    category['reference_status'][relmon_status] = 0

                if relmon_status == 'downloaded':
                    relmon['downloaded_relvals'] = relmon['downloaded_relvals'] + 1

                if category['status'] == 'done':
                    relmon['done_size'] += relval.get('file_size', 0)

                category['reference_status'][relmon_status] = category['reference_status'][relmon_status] + 1

            category['target'] = [{'name': (x.get('name', '')),
                                   'file_name': x.get('file_name', ''),
                                   'file_url': x.get('file_url', ''),
                                   'file_size': x.get('file_size', 0),
                                   'status': x.get('status', '')} for x in category['target']]

            category['target_status'] = {}
            category['target_total_size'] = 0
            for relval in category['target']:
                category['target_total_size'] += relval.get('file_size', 0)
                relmon_status = relval['status']
                if relmon_status not in category['target_status']:
                    category['target_status'][relmon_status] = 0

                if relmon_status == 'downloaded':
                    relmon['downloaded_relvals'] = relmon['downloaded_relvals'] + 1

                if category['status'] == 'done':
                    relmon['done_size'] += relval.get('file_size', 0)

                category['target_status'][relmon_status] = category['target_status'][relmon_status] + 1

            relmon['total_size'] += category['reference_total_size'] + category['target_total_size']

        relmon['total_size'] = max(relmon['total_size'], 0.001)
        if 'secret_hash' in relmon:
            del relmon['secret_hash']

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
        if relmon['status'] not in ['terminated']:
            return output_text({'message': 'Cannot reset relmon in status %s' % (relmon['status'])})

        relmon['status'] = 'new'
        storage.update_relmon(relmon)
        tick()
        return output_text({'message': 'OK'})

    return output_text({'message': 'No ID'})


@app.route('/terminate', methods=['POST'])
def terminate_relmon():
    data = json.loads(request.data.decode('utf-8'))
    if 'id' in data:
        storage = PersistentStorage()
        relmon = storage.get_relmon_by_id(data['id'])
        if relmon['status'] not in ['submitted', 'running', 'moving']:
            return output_text({'message': 'Cannot terminate relmon in status %s' % (relmon['status'])})

        relmon['status'] = 'terminating'
        storage.update_relmon(relmon)
        tick()
        return output_text({'message': 'OK'})

    return output_text({'message': 'No ID'})


@app.route('/delete', methods=['DELETE'])
def delete_relmon():
    data = json.loads(request.data.decode('utf-8'))
    if 'id' in data:
        storage = PersistentStorage()
        relmon = storage.get_relmon_by_id(data['id'])
        if relmon['status'] not in ['terminated', 'done']:
            return output_text({'message': 'Cannot delete relmon in status %s' % (relmon['status'])})

        relmon['status'] = 'deleting'
        storage.update_relmon(relmon)
        tick()
        return output_text({'message': 'OK'})

    return output_text({'message': 'No ID'})


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
    logger = logging.getLogger('logger')
    if relmon.get('secret_hash', 'NO_HASH1') != data.get('secret_hash', 'NO_HASH2'):
        logger.error('Wrong secret hash')
        return output_text({'message': 'Wrong secret hash'})

    old_status = relmon.get('status')
    if old_status != 'submitted' and old_status != 'running':
        logger.error('Bad status %s' % (old_status))
        return output_text({'message': 'Bad status %s' % (old_status)})

    relmon['categories'] = data['categories']
    relmon['status'] = data['status']
    if relmon['status'] != old_status:
        tick()

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


def setup_console_logging():
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)

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
    setup_console_logging()
    scheduler.add_executor('processpool')
    scheduler.add_job(tick, 'interval', seconds=600, max_instances=1)
    scheduler.start()
    run_flask()
    scheduler.shutdown()

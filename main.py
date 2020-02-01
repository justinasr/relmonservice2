from flask import Flask, render_template, request, make_response
from flask_restful import Api
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from logging import handlers
import argparse
import logging
import json
import time
import configparser
import os
from local.controller import Controller
from mongodb_database import Database
from local.relmon import RelMon


app = Flask(__name__,
            static_folder="./frontend/dist/static",
            template_folder="./frontend/dist")
api = Api(app)
scheduler = BackgroundScheduler()
controller = None


@app.route('/')
def index_page():
    return render_template('index.html')


@app.route('/api/create', methods=['POST'])
def add_relmon():
    relmon = json.loads(request.data.decode('utf-8'))
    controller.create_relmon(relmon, Database())
    controller_tick()
    return output_text({'message': 'OK'})


@app.route('/api/reset', methods=['POST'])
def reset_relmon():
    data = json.loads(request.data.decode('utf-8'))
    if 'id' in data:
        controller.add_to_reset_list(str(int(data['id'])))
        controller_tick()
        return output_text({'message': 'OK'})

    return output_text({'message': 'No ID'})


@app.route('/api/delete', methods=['DELETE'])
def delete_relmon():
    data = json.loads(request.data.decode('utf-8'))
    if 'id' in data:
        controller.add_to_delete_list(str(int(data['id'])))
        controller_tick()
        return output_text({'message': 'OK'})

    return output_text({'message': 'No ID'})


@app.route('/api/get_relmons')
def get_relmons():
    db = Database()
    data = db.get_relmons(include_docs=True)
    for relmon in data:
        relmon['last_update'] = time.strftime('%Y-%m-%d %H:%M', time.localtime(relmon.get('last_update', 0)))
        relmon['done_size'] = 0
        relmon['total_size'] = 0
        relmon['downloaded_relvals'] = 0
        relmon['total_relvals'] = 0
        for category in relmon.get('categories'):
            category['reference'] = [{'name': (x.get('name', '')),
                                      'file_name': x.get('file_name', ''),
                                      'file_url': x.get('file_url', ''),
                                      'file_size': x.get('file_size', 0),
                                      'status': x.get('status', ''),
                                      'versioned': x.get('versioned', False)} for x in category['reference']]

            category['reference_status'] = {}
            category['reference_total_size'] = 0
            relmon['total_relvals'] = relmon['total_relvals'] + len(category['reference']) + len(category['target'])
            for relval in category['reference']:
                category['reference_total_size'] += relval.get('file_size', 0)
                relmon_status = relval['status']
                if relmon_status not in category['reference_status']:
                    category['reference_status'][relmon_status] = 0

                if relmon_status != 'initial':
                    relmon['downloaded_relvals'] = relmon['downloaded_relvals'] + 1

                if category['status'] == 'done':
                    relmon['done_size'] += relval.get('file_size', 0)

                category['reference_status'][relmon_status] = category['reference_status'][relmon_status] + 1

            category['target'] = [{'name': (x.get('name', '')),
                                   'file_name': x.get('file_name', ''),
                                   'file_url': x.get('file_url', ''),
                                   'file_size': x.get('file_size', 0),
                                   'status': x.get('status', ''),
                                   'versioned': x.get('versioned', False)} for x in category['target']]

            category['target_status'] = {}
            category['target_total_size'] = 0
            for relval in category['target']:
                category['target_total_size'] += relval.get('file_size', 0)
                relmon_status = relval['status']
                if relmon_status not in category['target_status']:
                    category['target_status'][relmon_status] = 0

                if relmon_status != 'initial':
                    relmon['downloaded_relvals'] = relmon['downloaded_relvals'] + 1

                if category['status'] == 'done':
                    relmon['done_size'] += relval.get('file_size', 0)

                category['target_status'][relmon_status] = category['target_status'][relmon_status] + 1

            relmon['total_size'] += category['reference_total_size'] + category['target_total_size']

        relmon['total_size'] = max(relmon['total_size'], 0.001)

    data.sort(key=lambda x: x.get('id', -1), reverse=True)
    return output_text({'data': data})


def output_text(data, code=200, headers=None):
    """
    Makes a Flask response with a plain text encoded body
    """
    resp = make_response(json.dumps(data, indent=1, sort_keys=True), code)
    resp.headers.extend(headers or {})
    resp.headers['Content-Type'] = 'application/json'
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/api/edit', methods=['POST'])
def edit_relmon():
    relmon = json.loads(request.data.decode('utf-8'))
    controller.edit_relmon(relmon, Database())
    controller_tick()
    return output_text({'message': 'OK'})


@app.route('/api/update', methods=['POST'])
def update_info():
    data = json.loads(request.data.decode('utf-8'))
    db = Database()
    relmon = db.get_relmon(data['id'])
    if not relmon:
        return output_text({'message', 'Could not find'})

    logger = logging.getLogger('logger')
    old_status = relmon.get('status')
    relmon['categories'] = data['categories']
    relmon['status'] = data['status']
    logger.info('Update for %s (%s). Status is %s' % (relmon['name'],
                                                      relmon['id'],
                                                      relmon['status']))
    db.update_relmon(RelMon(relmon))
    if relmon['status'] != old_status:
        controller_tick()

    return output_text({'message': 'OK'})


@app.route('/api/tick')
def controller_tick():
    for job in scheduler.get_jobs():
        job.modify(next_run_time=datetime.now())

    return output_text({'message': 'OK'})


def tick():
    controller.tick()


def setup_console_logging():
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)


def get_config(mode):
    if mode == 'env':
        keys = ['callback_url',
                'cookie_url',
                'grid_certificate',
                'grid_key',
                'host',
                'port',
                'submission_host',
                'remote_directory',
                'ssh_credentials',
                'web_location']
        config = {}
        for key in keys:
            config[key] = os.environ.get(key.upper())

    else:
        config = configparser.ConfigParser()
        config.read('config.cfg')
        config = dict(config.items(mode))

    logging.info('Config values:')
    for key, value in config.items():
        logging.info('%s %s', key, value)

    return config


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RelMon Service')
    parser.add_argument('--mode',
                        choices=['prod', 'dev', 'env'],
                        required=True,
                        help='Production (prod) or development (dev) mode from config file or environment variables (env) mode')
    parser.add_argument('--debug',
                        help='Debug mode',
                        action='store_true')
    args = vars(parser.parse_args())
    debug = args.get('debug', False)
    setup_console_logging()
    logger = logging.getLogger('logger')
    mode = args.get('mode', 'dev').lower()
    logger.info('Mode is "%s"', mode)
    config = get_config(mode)
    controller = Controller(config)
    scheduler.add_executor('processpool')
    scheduler.add_job(tick, 'interval', seconds=600, max_instances=1)
    scheduler.start()
    port = int(config.get('port', 8001))
    host = config.get('host', '127.0.0.1')
    logger.info('Will run on %s:%s', host, port)
    app.run(host=host,
            port=port,
            debug=debug,
            threaded=True)
    scheduler.shutdown()

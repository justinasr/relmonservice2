from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import logging
import time
import os


class Database:
    PAGE_SIZE = 25

    def __init__(self):
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', 27017)
        self.logger = logging.getLogger('logger')
        self.client = MongoClient(db_host, db_port)
        self.relmons_db = self.client['relmons']
        self.relmons = self.relmons_db['relmons']

    def create_relmon(self, relmon):
        relmon_json = relmon.get_json()
        relmon_json['last_update'] = int(time.time())
        relmon_json['_id'] = relmon_json['id']
        try:
            return self.relmons.insert_one(relmon_json)
        except DuplicateKeyError:
            return None

    def update_relmon(self, relmon):
        relmon_json = relmon.get_json()
        relmon_json['last_update'] = int(time.time())
        if '_id' not in relmon_json:
            self.logger.error('No _id in document')
            return False

        try:
            self.relmons.replace_one({'_id': relmon_json['_id']}, relmon_json)
        except DuplicateKeyError:
            return None

    def delete_relmon(self, relmon):
        self.relmons.delete_one({'_id': relmon.get_id()})

    def get_relmon_count(self):
        return self.relmons.count_documents({})

    def get_relmon(self, relmon_id):
        return self.relmons.find_one({'_id': relmon_id})

    def get_relmons(self, page=0, page_size=PAGE_SIZE, include_docs=False):
        relmons = self.relmons.find().sort('_id', -1)
        total_rows = relmons.count()
        relmons = relmons.skip(page * page_size).limit(page_size)
        return list(relmons), total_rows

    def get_relmons_with_status(self, status, page=0, page_size=PAGE_SIZE, include_docs=False):
        relmons = self.relmons.find({'status': status})
        relmons = relmons.skip(page * page_size).limit(page_size)
        return list(relmons)

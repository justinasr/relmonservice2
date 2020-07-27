"""
Module that contains Database class
"""
import logging
import time
import json
import os
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


class Database:
    """
    Database class represents MongoDB database
    It encapsulates underlying connection and exposes some convenience methods
    """
    PAGE_SIZE = 10

    def __init__(self):
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', 27017)
        self.logger = logging.getLogger('logger')
        db_auth = os.environ.get('DB_AUTH', None)
        username = None
        password = None
        if db_auth:
            with open(db_auth) as json_file:
                credentials = json.load(json_file)

            username = credentials['username']
            password = credentials['password']

        if username and password:
            self.logger.debug('Using DB with username and password')
            self.client = MongoClient(db_host,
                                      db_port,
                                      username=username,
                                      password=password,
                                      authSource='admin',
                                      authMechanism='SCRAM-SHA-256')
        else:
            self.logger.debug('Using DB without username and password')
            self.client = MongoClient(db_host, db_port)

        self.relmons_db = self.client['relmons']
        self.relmons = self.relmons_db['relmons']

    def create_relmon(self, relmon):
        """
        Add given RelMon to the database
        """
        relmon_json = relmon.get_json()
        relmon_json['last_update'] = int(time.time())
        relmon_json['_id'] = relmon_json['id']
        try:
            return self.relmons.insert_one(relmon_json)
        except DuplicateKeyError:
            return None

    def update_relmon(self, relmon):
        """
        Update given RelMon in the database based on ID
        """
        relmon_json = relmon.get_json()
        relmon_json['last_update'] = int(time.time())
        if '_id' not in relmon_json:
            self.logger.error('No _id in document')
            return

        try:
            self.relmons.replace_one({'_id': relmon_json['_id']}, relmon_json)
        except DuplicateKeyError:
            return

    def delete_relmon(self, relmon):
        """
        Delete given RelMon from the database based on it's ID
        """
        self.relmons.delete_one({'_id': relmon.get_id()})

    def get_relmon_count(self):
        """
        Return total number of RelMons in the database
        """
        return self.relmons.count_documents({})

    def get_relmon(self, relmon_id):
        """
        Fetch a RelMon with given ID from the database
        """
        return self.relmons.find_one({'_id': relmon_id})

    def get_relmons(self, query_dict=None, page=0, page_size=PAGE_SIZE):
        """
        Search for relmons in the database
        Return list of paginated RelMons and total number of search results
        """
        if query_dict is None:
            query_dict = {}

        relmons = self.relmons.find(query_dict).sort('_id', -1)
        total_rows = relmons.count()
        relmons = relmons.skip(page * page_size).limit(page_size)
        return list(relmons), total_rows

    def get_relmons_with_status(self, status):
        """
        Get list of RelMons with given status
        """
        relmons = self.relmons.find({'status': status})
        return list(relmons)

    def get_relmons_with_condor_status(self, status):
        """
        Get list of RelMons with given HTCondor status
        """
        relmons = self.relmons.find({'condor_status': status})
        return list(relmons)

    def get_relmons_with_name(self, relmon_name):
        """
        Get list of (should be one) RelMons with given name
        """
        relmons = self.relmons.find({'name': relmon_name})
        return list(relmons)

from threading import Lock
import json
import time
import logging


class PersistentStorage:

    __locks = {}

    def __init__(self, file_name='data.json'):
        self.file_name = file_name
        if file_name not in self.__locks:
            self.__locks[file_name] = Lock()

        self.lock = self.__locks[file_name]
        self.logger = logging.getLogger('logger')

    def get_all_data(self):
        for i in range(3):
            try:
                with open(self.file_name) as json_file:
                    data = json.load(json_file)

                if data is not None:
                    return data
            except:
                self.logger.info('Could not read %s. Retrying again %s.' % (self.file_name, i + 1))
                time.sleep(0.5)

        return None

    def get_relmon_by_name(self, name):
        data = self.get_all_data()
        for relmon in data:
            if relmon['name'] == name:
                return relmon

        return None

    def get_relmon_by_id(self, relmon_id):
        data = self.get_all_data()
        for relmon in data:
            if relmon['id'] == relmon_id:
                return relmon

        return None

    def create_relmon(self, relmon):
        if self.get_relmon_by_id(relmon['id']) is not None:
            raise Exception('Duplicate')

        if self.get_relmon_by_name(relmon['name']) is not None:
            raise Exception('Duplicate')

        self.logger.info('Will acquire lock for %s (%s). Method create_relmon' % (relmon['name'], relmon['id']))
        self.lock.acquire()
        self.logger.info('Did acquire lock for %s (%s). Method create_relmon' % (relmon['name'], relmon['id']))
        data = self.get_all_data()
        relmon['last_update'] = int(time.time())
        data.append(relmon)
        with open('data.json', 'w') as json_file:
            json.dump(data, json_file, indent=2, sort_keys=True)

        self.logger.info('Will release lock for %s (%s). Method create_relmon' % (relmon['name'], relmon['id']))
        self.lock.release()
        self.logger.info('Did release lock for %s (%s). Method create_relmon' % (relmon['name'], relmon['id']))

    def update_relmon(self, relmon):
        self.delete_relmon(relmon['id'])
        self.create_relmon(relmon)

    def delete_relmon(self, relmon_id):
        self.logger.info('Will acquire lock for (%s). Method delete_relmon' % (relmon_id))
        self.lock.acquire()
        self.logger.info('Did acquire lock for (%s). Method delete_relmon' % (relmon_id))
        data = self.get_all_data()
        data = [x for x in data if x['id'] != relmon_id]
        with open('data.json', 'w') as json_file:
            json.dump(data, json_file, indent=2, sort_keys=True)

        self.logger.info('Will release lock for (%s). Method delete_relmon' % (relmon_id))
        self.lock.release()
        self.logger.info('Did release lock for (%s). Method delete_relmon' % (relmon_id))

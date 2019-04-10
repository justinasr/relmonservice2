from threading import Lock
import json
import time


class PersistentStorage:

    __locks = {}

    def __init__(self, file_name='data.json'):
        self.file_name = file_name
        if file_name not in self.__locks:
            self.__locks[file_name] = Lock()

        self.lock = self.__locks[file_name]

    def get_all_data(self):
        with open(self.file_name) as json_file:
            data = json.load(json_file)

        return data

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

        self.lock.acquire()
        data = self.get_all_data()
        relmon['last_update'] = int(time.time())
        data.append(relmon)
        with open('data.json', 'w') as json_file:
            json.dump(data, json_file, indent=2, sort_keys=True)

        self.lock.release()

    def update_relmon(self, relmon):
        self.delete_relmon(relmon['id'])
        self.create_relmon(relmon)

    def delete_relmon(self, relmon_id):
        self.lock.acquire()
        data = self.get_all_data()
        data = [x for x in data if x['id'] != relmon_id]
        with open('data.json', 'w') as json_file:
            json.dump(data, json_file, indent=2, sort_keys=True)

        self.lock.release()

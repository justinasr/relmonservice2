import logging
import shutil
import random


class RelMon():

    def __init__(self, data):
        self.data = data
        self.data['categories'].sort(key=lambda x: x.get('name'))
        self.logger = logging.getLogger('logger')
        self.logger.info('Resources for %s are CPU:%s, memory: %s memory, disk: %s' % (self,
                                                                                       self.get_cpu(),
                                                                                       self.get_memory(),
                                                                                       self.get_disk()))

    def reset(self):
        # Delete local logs
        shutil.rmtree('logs/%s' % (self.get_id()), ignore_errors=True)
        self.set_status('new')
        self.set_condor_status('<unknown>')
        self.set_condor_id(0)
        self.data['secret_hash'] = '%032x' % (random.getrandbits(128))
        for category in self.data['categories']:
            category['status'] = 'initial'
            category['reference'] = [{'name': x['name'].strip(),
                                      'file_name': '',
                                      'file_url': '',
                                      'file_size': 0,
                                      'status': 'initial'} for x in category['reference']]
            category['target'] = [{'name': (x['name'].strip()),
                                   'file_name': '',
                                   'file_url': '',
                                   'file_size': 0,
                                   'status': 'initial'} for x in category['target']]

        return self.data

    def get_id(self):
        return self.data['id']

    def get_name(self):
        return self.data['name']

    def get_cpu(self):
        number_of_relvals = 0
        for category in self.data['categories']:
            number_of_relvals += len(category['reference'])
            number_of_relvals += len(category['target'])

        cpus = 1
        if number_of_relvals <= 10:
            # Max 5 vs 5
            cpus = 1
        elif number_of_relvals <= 30:
            # Max 15 vs 15
            cpus = 2
        elif number_of_relvals <= 50:
            # Max 25 vs 25
            cpus = 4
        elif number_of_relvals <= 150:
            # Max 75 vs 75
            cpus = 8
        else:
            # > 75 vs 75
            cpus = 16

        return cpus

    def get_memory(self):
        memory = str(self.get_cpu() * 2) + 'G'
        return memory

    def get_disk(self):
        number_of_relvals = 0
        for category in self.data['categories']:
            number_of_relvals += len(category['reference'])
            number_of_relvals += len(category['target'])

        disk = '%sM' % (number_of_relvals * 300)
        return disk

    def get_json(self):
        return self.data

    def get_status(self):
        return self.data['status']

    def get_condor_status(self):
        if 'condor_status' in self.data:
            return self.data['condor_status']
        else:
            return ''

    def get_condor_id(self):
        return self.data['condor_id']

    def set_status(self, status):
        self.data['status'] = status

    def set_condor_status(self, condor_status):
        self.data['condor_status'] = condor_status

    def set_condor_id(self, condor_id):
        self.data['condor_id'] = condor_id

    def __str__(self):
        return '%s (%s)' % (self.get_name(), self.get_id())

    def __repr__(self):
        return '%s (%s)' % (self.get_name(), self.get_id())
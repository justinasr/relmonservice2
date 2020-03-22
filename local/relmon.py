"""
Module for RelMon class
"""
import os
import re
from copy import deepcopy


class RelMon():
    """
    This class represents a single RelMon object and has some convenience methods
    such as required resources and reset
    """

    def __init__(self, data):
        data = deepcopy(data)
        data['name'] = self.sanitize_name(data['name'])
        self.data = data
        relmon_path = 'relmons/%s/' % (self.get_id())
        if not os.path.isdir(relmon_path):
            os.mkdir(relmon_path)

        for category in self.data.get('categories', []):
            category['status'] = category.get('status', 'initial')
            new_references = []
            for old_reference in category['reference']:
                if isinstance(old_reference, str):
                    new_references.append({'name': self.sanitize_relval(old_reference),
                                           'file_name': '',
                                           'file_url': '',
                                           'file_size': 0,
                                           'status': 'initial'})
                else:
                    new_references.append({'name': self.sanitize_relval(old_reference['name']),
                                           'file_name': old_reference.get('file_name', ''),
                                           'file_url': old_reference.get('file_url', ''),
                                           'file_size': old_reference.get('file_size', 0),
                                           'status': old_reference.get('status', 'initial')})

            new_targets = []
            for old_target in category['target']:
                if isinstance(old_target, str):
                    new_targets.append({'name': self.sanitize_relval(old_target),
                                        'file_name': '',
                                        'file_url': '',
                                        'file_size': 0,
                                        'status': 'initial'})
                else:
                    new_targets.append({'name': self.sanitize_relval(old_target['name']),
                                        'file_name': old_target.get('file_name', ''),
                                        'file_url': old_target.get('file_url', ''),
                                        'file_size': old_target.get('file_size', 0),
                                        'status': old_target.get('status', 'initial')})

            category['reference'] = new_references
            category['target'] = new_targets

    def sanitize_relval(self, s):
        """
        Replace all non letters, digits, hyphens and underscores with underscore
        """
        return re.sub(r'[^A-Za-z0-9\-_]', '_', s.strip())

    def sanitize_name(self, s):
        """
        Replace all non letters, digits, hyphens and underscores with underscore
        """
        return re.sub(r'[^A-Za-z0-9\-_]', '_', s.strip())

    def reset_category(self, category_name):
        category = self.get_category(category_name)
        category['status'] = 'initial'
        new_references = []
        for old_reference in category['reference']:
            if isinstance(old_reference, str):
                name = old_reference
            else:
                name = old_reference['name']

            new_references.append({'name': name,
                                   'file_name': '',
                                   'file_url': '',
                                   'file_size': 0,
                                   'status': 'initial'})

        new_targets = []
        for old_target in category['target']:
            if isinstance(old_target, str):
                name = old_target
            else:
                name = old_target['name']

            new_targets.append({'name': name,
                                'file_name': '',
                                'file_url': '',
                                'file_size': 0,
                                'status': 'initial'})

        category['reference'] = new_references
        category['target'] = new_targets

    def reset(self):
        """
        Reset relmon and zero-out references and targets
        """
        self.set_status('new')
        self.set_condor_status('<unknown>')
        self.set_condor_id(0)
        for category in self.data['categories']:
            self.reset_category(category['name'])

        return self.data

    def get_id(self):
        """
        Getter for id
        """
        return self.data.get('id')

    def get_name(self):
        """
        Getter for name
        """
        return self.data.get('name')

    def get_cpu(self):
        """
        Return number of CPUs required based on number of references and targets
        """
        number_of_relvals = 0
        for category in self.data['categories']:
            if category['status'] != 'initial':
                continue

            number_of_relvals += len(category['reference'])
            number_of_relvals += len(category['target'])

        # Pairs       CPU
        #  0 -  5   -   1
        #  6 - 15   -   2
        # 16 - 45   -   4
        # 46 - 90   -   8
        # 90+       -  16

        cpus = 1
        if number_of_relvals <= 10:
            # Max 5 vs 5
            cpus = 1
        elif number_of_relvals <= 30:
            # Max 15 vs 15
            cpus = 2
        elif number_of_relvals <= 90:
            # Max 45 vs 45
            cpus = 4
        elif number_of_relvals <= 180:
            # Max 90 vs 90
            cpus = 8
        else:
            # > 90 vs 90
            cpus = 16

        return cpus

    def get_memory(self):
        """
        Return amount of memory required based on number of CPUs
        """
        memory = str(self.get_cpu() * 2) + 'G'
        return memory

    def get_disk(self):
        """
        Return amount of disk space required based on number of references and targets
        """
        number_of_relvals = 0
        for category in self.data['categories']:
            if category['status'] != 'initial':
                continue

            number_of_relvals += len(category['reference'])
            number_of_relvals += len(category['target'])

        # At lest 300M
        number_of_relvals = max(number_of_relvals, 1)
        disk = '%sM' % (number_of_relvals * 300)
        return disk

    def get_json(self):
        """
        Return object's dictionary
        """
        return self.data

    def get_status(self):
        """
        Getter for status
        """
        return self.data['status']

    def get_condor_status(self):
        """
        Getter for condor status
        """
        return self.data.get('condor_status', '')

    def get_condor_id(self):
        """
        Getter for condor id
        """
        return self.data.get('condor_id', 0)

    def set_status(self, status):
        """
        Setter for status
        """
        self.data['status'] = status

    def set_condor_status(self, condor_status):
        """
        Setter for condor status
        """
        self.data['condor_status'] = condor_status

    def set_condor_id(self, condor_id):
        """
        Setter for condor id
        """
        self.data['condor_id'] = condor_id

    def get_category(self, category_name):
        """
        Get a category dictionary
        """
        for category in self.data.get('categories', []):
            if category['name'] == category_name:
                return category

        self.data['categories'] = self.data.get('categories', [])
        self.data['categories'].append({'name': category_name, 'reference': [], 'target': []})
        return self.get_category(category_name)

    def __str__(self):
        return '%s (%s)' % (self.get_name(), self.get_id())

    def __repr__(self):
        return str(self)

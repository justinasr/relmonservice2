"""
Module for RelMon class
"""
import os


class RelMon():
    """
    This class represents a single RelMon object and has some convenience methods
    such as required resources and reset
    """

    def __init__(self, data):
        self.data = data
        relmon_path = 'relmons/%s/' % (self.get_id())
        if not os.path.isdir(relmon_path):
            os.mkdir(relmon_path)

        for category in self.data.get('categories', []):
            category['status'] = category.get('status', 'initial')
            new_references = []
            for old_reference in category['reference']:
                if isinstance(old_reference, str):
                    new_references.append({'name': old_reference,
                                           'file_name': '',
                                           'file_url': '',
                                           'file_size': 0,
                                           'status': 'initial'})
                else:
                    new_references.append({'name': old_reference['name'],
                                           'file_name': old_reference.get('file_name', ''),
                                           'file_url': old_reference.get('file_url', ''),
                                           'file_size': old_reference.get('file_size', 0),
                                           'status': old_reference.get('status', 'initial')})

            new_targets = []
            for old_target in category['target']:
                if isinstance(old_target, str):
                    new_targets.append({'name': old_target,
                                        'file_name': '',
                                        'file_url': '',
                                        'file_size': 0,
                                        'status': 'initial'})
                else:
                    new_targets.append({'name': old_target['name'],
                                        'file_name': old_target.get('file_name', ''),
                                        'file_url': old_target.get('file_url', ''),
                                        'file_size': old_target.get('file_size', 0),
                                        'status': old_target.get('status', 'initial')})

            category['reference'] = new_references
            category['target'] = new_targets

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

    def __remove_empty_categories(self):
        non_empty_categories = []
        for category in self.data.get('categories', []):
            reference_length = len(category['reference'])
            target_length = len(category['target'])
            if reference_length > 0 and target_length > 0:
                non_empty_categories.append(category)

        self.data['categories'] = non_empty_categories

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

        # Comparisons CPU
        #  0- 10     -  1
        # 11- 25     -  2
        # 26- 60     -  4
        # 61-150     -  8
        # 151+       - 16

        cpus = 1
        if number_of_relvals <= 20:
            # Max 10 vs 10
            cpus = 1
        elif number_of_relvals <= 50:
            # Max 25 vs 25
            cpus = 2
        elif number_of_relvals <= 120:
            # Max 60 vs 60
            cpus = 4
        elif number_of_relvals <= 300:
            # Max 150 vs 150
            cpus = 8
        else:
            # > 150 vs 150
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
        Return amount of disk space reuired based on number of references and targets
        """
        number_of_relvals = 0
        for category in self.data['categories']:
            number_of_relvals += len(category['reference'])
            number_of_relvals += len(category['target'])

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

        return {}

    def __str__(self):
        return '%s (%s)' % (self.get_name(), self.get_id())

    def __repr__(self):
        return str(self)

"""
RelMon report production controller
Runs main loop that checks status and acts accordingly
"""

import logging
from persistent_storage import PersistentStorage
import json
import os
import random
from ssh_executor import SSHExecutor
import shutil


class Controller():

    # Directory in remote host to keep files for submission and collect output
    __remote_directory = 'relmon_test/'
    # Directory where to move done comparisons
    __web_path = '/eos/user/j/jrumsevi/www/relmon/'
    # Directory where user certificate and key for GRID authentication is located
    __grid_location = '/afs/cern.ch/user/j/jrumsevi/private/'
    # GRID certificate file
    __cert_file_name = 'user.crt.pem'
    # GRID key file
    __key_file_name = 'user.key.pem'

    def __init__(self):
        self.is_tick_running = False
        self.persistent_storage = PersistentStorage()
        self.ssh_executor = SSHExecutor()
        self.logger = logging.getLogger('logger')

    def tick(self):
        """
        Controller works by doing "ticks" every once in a while
        During a tick it shoud check all existing relmon's and
        their status and, if necessary, perform actions like
        submission or output collection
        """
        self.logger.info('Controller tick')
        if self.is_tick_running:
            self.logger.warning('Tick is already running')
            return

        self.is_tick_running = True
        data = self.persistent_storage.get_all_data()
        self.logger.info('Found %s relmons' % (len(data)))
        for relmon in data:
            status = relmon.get('status')
            self.logger.info('%s status is %s' % (relmon['name'], status))
            if status == 'new':
                self.__submit_to_condor(relmon)
            elif status == 'terminating':
                self.__terminate_relmon(relmon)
            elif status == 'resetting':
                self.__reset_relmon(relmon)
            elif status == 'deleting':
                self.__delete_relmon(relmon)
            elif status == 'submitted' or status == 'running':
                self.__check_if_running(relmon)
            elif status == 'moving' or (status != 'done' and relmon.get('condor_status') == 'DONE'):
                self.__check_if_running(relmon)
                self.__collect_output(relmon)

        self.ssh_executor.close_connections()
        self.is_tick_running = False
        self.logger.info('Controller tick finished')

    def __submit_to_condor(self, relmon):
        self.logger.info('Will submit %s to HTCondor' % (relmon['name']))
        relmon = self.reset_relmon(relmon)
        relmon['status'] = 'submitting'
        relmon['secret_hash'] = '%032x' % (random.getrandbits(128))

        self.persistent_storage.update_relmon(relmon)
        try:
            self.logger.info('%s status is %s' % (relmon['name'], relmon['status']))

            relmon_file = self.__create_relmon_file(relmon)
            condor_file = self.__create_condor_job_file(relmon, relmon_file)
            script_file = self.__create_job_script_file(relmon, relmon_file)

            relmon_id = relmon['id']
            remote_relmon_directory = '%s%s' % (self.__remote_directory, relmon_id)
            self.ssh_executor.execute_command(['rm -rf %s' % (remote_relmon_directory),
                                               'mkdir -p %s' % (remote_relmon_directory)])

            self.ssh_executor.upload_file(relmon_file, '%s/%s' % (remote_relmon_directory, relmon_file))
            self.ssh_executor.upload_file(condor_file, '%s/%s' % (remote_relmon_directory, condor_file))
            self.ssh_executor.upload_file(script_file, '%s/%s' % (remote_relmon_directory, script_file))

            os.remove(relmon_file)
            os.remove(condor_file)
            os.remove(script_file)
            shutil.rmtree('logs/%s' % (relmon_id), ignore_errors=True)

            stdout, stderr = self.ssh_executor.execute_command(['cd %s' % (remote_relmon_directory),
                                                                'condor_submit %s' % (condor_file)])
            relmon = self.persistent_storage.get_relmon_by_id(relmon_id)
            if not stderr and '1 job(s) submitted to cluster' in stdout:
                # output is "1 job(s) submitted to cluster 801341"
                relmon['status'] = 'submitted'
                condor_id = int(float(stdout.split()[-1]))
                relmon['condor_id'] = condor_id
                relmon['condor_status'] = 'IDLE'
                self.logger.info('Submitted %s (%s)' % (relmon['name'], relmon_id))
            else:
                self.logger.error('Error submitting %s (%s)' % (relmon['name'], relmon_id))
                relmon['status'] = 'failed'
        except Exception as ex:
            relmon['status'] = 'failed'
            self.logger.error('Exception while trying to submit %s (%s): %s' % (relmon.get('name', 'NoName'),
                                                                                relmon.get('id', 'NoId'),
                                                                                str(ex)))

        self.logger.info('%s status is %s' % (relmon['name'], relmon['status']))
        self.persistent_storage.update_relmon(relmon)

    def __check_if_running(self, relmon):
        condor_id = relmon['condor_id']
        self.logger.info('Will check if %s is running in HTCondor, id: %s' % (relmon['name'], condor_id))
        stdout, stderr = self.ssh_executor.execute_command('condor_q -af:h ClusterId JobStatus | grep %s' % (condor_id))
        if not stderr and not stdout:
            self.logger.warning('Could not find %s (%s) in condor queue' % (relmon['name'], relmon['id']))
            relmon['condor_status'] = '<unknown>'
        elif not stderr:
            status_number = stdout.split()[-1]
            if status_number == '0':
                relmon['condor_status'] = 'UNEXPLAINED'
            elif status_number == '1':
                relmon['condor_status'] = 'IDLE'
            elif status_number == '2':
                relmon['condor_status'] = 'RUN'
            elif status_number == '3':
                relmon['condor_status'] = 'REMOVED'
            elif status_number == '4':
                relmon['condor_status'] = 'DONE'
            elif status_number == '5':
                relmon['condor_status'] = 'HOLD'
            elif status_number == '6':
                relmon['condor_status'] = 'SUBMISSION ERROR'
            else:
                relmon['condor_status'] = '<unknown>'
                self.logger.info('Unknown status %s of %s (%s)?' % (status_number,
                                                                    relmon['name'],
                                                                    relmon['id']))
        else:
            self.logger.error('Error with HTCondor?')
            relmon['condor_status'] = '<unknown>'

        self.logger.info('Saving %s (%s) condor status as %s' % (relmon['name'],
                                                                 relmon['id'],
                                                                 relmon.get('condor_status')))
        self.persistent_storage.update_relmon(relmon)

    def __collect_output(self, relmon):
        if relmon['condor_status'] != 'DONE':
            self.logger.info('%s (%s) is still running, will not try to collect' % (relmon['name'], relmon['id']))
            return

        remote_relmon_directory = '%s%s/' % (self.__remote_directory, relmon['id'])
        relmon_logs = 'logs/%s/' % (relmon['id'])
        shutil.rmtree(relmon_logs, ignore_errors=True)
        os.mkdir(relmon_logs)

        self.ssh_executor.download_file('%svalidation_matrix.log' % (remote_relmon_directory),
                                        '%svalidation_matrix.log' % (relmon_logs))
        self.ssh_executor.download_file('%sRELMON_%s.out' % (remote_relmon_directory, relmon['id']),
                                        '%sRELMON_%s.out' % (relmon_logs, relmon['id']))
        self.ssh_executor.download_file('%sRELMON_%s.log' % (remote_relmon_directory, relmon['id']),
                                        '%sRELMON_%s.log' % (relmon_logs, relmon['id']))
        self.ssh_executor.download_file('%sRELMON_%s.err' % (remote_relmon_directory, relmon['id']),
                                        '%sRELMON_%s.err' % (relmon_logs, relmon['id']))

        stdout, stderr = self.ssh_executor.execute_command(['cd %s' % (remote_relmon_directory),
                                                            'cd ..',
                                                            'rm -r %s' % (relmon['id'])])
        relmon['status'] = 'done'
        self.persistent_storage.update_relmon(relmon)

    def __create_relmon_file(self, relmon):
        relmon_file_name = '%s.json' % (relmon['id'])
        with open(relmon_file_name, 'w') as json_file:
            json.dump(relmon, json_file, indent=4, sort_keys=True)

        return relmon_file_name

    def __create_condor_job_file(self, relmon, relmon_file_name):
        relmon_id = relmon['id']
        cpus, memory, disk = self.__get_cpus_memory_disk_for_relmon(relmon)
        condor_file_name = 'RELMON_%s.sub' % (relmon_id)
        condor_file_content = ['executable              = RELMON_%s.sh' % (relmon_id),
                               'output                  = RELMON_%s.out' % (relmon_id),
                               'error                   = RELMON_%s.err' % (relmon_id),
                               'log                     = RELMON_%s.log' % (relmon_id),
                               'transfer_input_files    = %s,%s%s,%s%s' % (relmon_file_name,
                                                                           self.__grid_location,
                                                                           self.__cert_file_name,
                                                                           self.__grid_location,
                                                                           self.__key_file_name,),
                               'when_to_transfer_output = on_exit',
                               'request_cpus            = %s' % (cpus),
                               'request_memory          = %s' % (memory),
                               'request_disk            = %s' % (disk),
                               '+JobFlavour             = "tomorrow"',
                               'requirements            = (OpSysAndVer =?= "SLCern6")',
                               # Leave in queue when status is DONE for two hours
                               'leave_in_queue          = JobStatus == 4 && (CompletionDate =?= UNDEFINED || ((CurrentTime - CompletionDate) < 7200))',
                               'queue']

        condor_file_content = '\n'.join(condor_file_content)
        with open(condor_file_name, 'w') as file:
            file.write(condor_file_content)

        return condor_file_name

    def __create_job_script_file(self, relmon, relmon_file_name):
        cpus, _, _ = self.__get_cpus_memory_disk_for_relmon(relmon)
        script_file_name = 'RELMON_%s.sh' % (relmon['id'])
        script_file_content = ['#!/bin/bash',
                               'DIR=$(pwd)',
                               'git clone https://github.com/justinasr/relmonservice2.git',
                               'scramv1 project CMSSW CMSSW_10_4_0',
                               'cd CMSSW_10_4_0/src',
                               'eval `scramv1 runtime -sh`',
                               'cd $DIR',
                               'mkdir -p Reports',
                               'python3 relmonservice2/remote_apparatus.py '  # No newline here
                               '--relmon %s --cert %s --key %s --cpus %s' % (relmon_file_name,
                                                                             self.__cert_file_name,
                                                                             self.__key_file_name,
                                                                             cpus),
                               # Remove all root files
                               'rm *.root',
                               # Copy sqlitify to Reports directory
                               'cp relmonservice2/sqltify.py Reports/sqltify.py',
                               # Go to reports directory
                               'cd Reports',
                               # Run sqltify
                               'python3 sqltify.py',
                               # Remove sql file from web path
                               'rm -rf %s%s.sqlite' % (self.__web_path, relmon['name']),
                               # Checksum for created sqlite
                               'echo "MD5 Sum"',
                               'md5sum reports.sqlite',
                               # Copy reports sqlite to web path
                               'time cp -v reports.sqlite %s%s.sqlite' % (self.__web_path, relmon['name'])]

        script_file_content = '\n'.join(script_file_content)
        with open(script_file_name, 'w') as file:
            file.write(script_file_content)

        return script_file_name

    def reset_relmon(self, relmon):
        relmon['status'] = 'new'
        if 'condor_status' in relmon:
            del relmon['condor_status']

        if 'condor_id' in relmon:
            del relmon['condor_id']

        for category in relmon['categories']:
            category['status'] = 'initial'
            category['reference'] = [{'name': (x['name'].strip() if isinstance(x, dict) else x.strip()),
                                      'file_name': '',
                                      'file_url': '',
                                      'file_size': 0,
                                      'status': 'initial'} for x in category['reference']]
            category['target'] = [{'name': (x['name'].strip() if isinstance(x, dict) else x.strip()),
                                   'file_name': '',
                                   'file_url': '',
                                   'file_size': 0,
                                   'status': 'initial'} for x in category['target']]

        return relmon

    def __reset_relmon(self, relmon):
        self.reset_relmon(relmon)
        self.persistent_storage.update_relmon(relmon)

    def __terminate_relmon(self, relmon):
        status = relmon.get('status')
        remote_relmon_directory = '%s%s' % (self.__remote_directory, relmon['id'])
        if 'condor_id' in relmon and relmon.get('condor_id', -1) > 0:
            self.ssh_executor.execute_command('condor_rm %s' % (relmon['condor_id']))

        self.ssh_executor.execute_command('rm -r %s' % (remote_relmon_directory))
        relmon['status'] = 'terminated'
        relmon['condor_id'] = -1
        if 'condor_status' in relmon:
            del relmon['condor_status']

        self.persistent_storage.update_relmon(relmon)

    def __delete_relmon(self, relmon):
        self.persistent_storage.delete_relmon(relmon['id'])

    def __get_cpus_memory_disk_for_relmon(self, relmon):
        number_of_relvals = 0
        for category in relmon['categories']:
            number_of_relvals += len(category['reference'])
            number_of_relvals += len(category['target'])

        # 300MB per relval - to fit root files and generated report
        disk = '%sM' % (number_of_relvals * 300)
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

        memory = str(cpus * 2) + 'G'
        self.logger.info('Resources for %s (%s) are %s CPUs, %s memory, %s disk space. Number of relvals %s' % (relmon['name'],
                                                                                                                relmon['id'],
                                                                                                                cpus,
                                                                                                                memory,
                                                                                                                disk,
                                                                                                                number_of_relvals))
        return cpus, memory, disk

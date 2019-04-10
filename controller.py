"""RelMon report production controller. From workflow names to
completed report
"""

import logging
import time
import threading
from persistent_storage import PersistentStorage
import paramiko
import json
import os
import random


class Controller(threading.Thread):

    __credentials_file_path = '/home/jrumsevi/auth.txt'
    __remote_host = 'lxplus.cern.ch'

    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.persistent_storage = PersistentStorage()
        self.ssh_client = None
        self.ftp_client = None
        self.grid_location = '/afs/cern.ch/user/j/jrumsevi/private/'
        self.cert_file_name = 'user.crt.pem'
        self.key_file_name = 'user.key.pem'
        self.start()

    def setup_ssh(self):
        if self.ssh_client:
            self.close_connections()

        with open(self.__credentials_file_path) as json_file:
            credentials = json.load(json_file)

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(self.__remote_host,
                                username=credentials["username"],
                                password=credentials["password"],
                                timeout=30)

    def setup_ftp(self):
        if self.ftp_client:
            self.close_connections()

        if not self.ssh_client:
            self.setup_ssh()

        self.ftp_client = self.ssh_client.open_sftp()

    def execute_command(self, command):
        if not self.ssh_client:
            self.setup_ssh()

        (_, stdout, stderr) = self.ssh_client.exec_command(command)
        stdout = stdout.read().decode('utf-8').strip()
        stderr = stderr.read().decode('utf-8').strip()
        logging.info("STDOUT (%s): %s" % (command, stdout))
        logging.info("STDERR (%s): %s" % (command, stderr))
        return stdout, stderr

    def copy_file(self, copy_from, copy_to):
        if not self.ftp_client:
            self.setup_ftp()

        self.ftp_client.put(copy_from, copy_to)

    def close_connections(self):
        if self.ftp_client:
            self.ftp_client.close()
            self.ftp_client = None

        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def run(self):
        return
        sleep_duration = 120
        while self.running:
            logging.info('Doing main loop')
            loop_start = time.time()
            try:
                self.tick()
            except Exception as e:
                logging.error(e)

            loop_end = time.time()
            logging.info('Finishing main loop')
            time.sleep(max(3, sleep_duration - (loop_end - loop_start)))

    def stop(self):
        self.running = False
        self.join()

    def tick(self):
        data = self.persistent_storage.get_all_data()
        for relmon in data:
            logging.info('%s status is %s' % (relmon['name'], relmon['status']))
            if relmon['status'] == 'new':
                self.submit_to_condor(relmon)
            elif relmon['status'] == 'submitted' or relmon['status'] == 'running':
                self.check_if_running(relmon)
            elif relmon['status'] == 'finished':
                self.collect_output(relmon)

            self.close_connections()

    def submit_to_condor(self, relmon):
        logging.info('Will submit %s to HTCondor' % (relmon['name']))
        relmon['status'] = 'submitting'
        relmon['condor_id'] = -1
        relmon['condor_status'] = '<unknown>'
        relmon['secret_hash'] = '%032x' % (random.getrandbits(128))
        for category in relmon['categories']:
            category['status'] = 'initial'
            category['reference'] = [{'name': x['name'],
                                      'file_name': '',
                                      'file_url': '',
                                      'file_size': 0,
                                      'status': 'initial'} for x in category['reference']]
            category['target'] = [{'name': x['name'],
                                   'file_name': '',
                                   'file_url': '',
                                   'file_size': 0,
                                   'status': 'initial'} for x in category['target']]

        self.persistent_storage.update_relmon(relmon)
        logging.info('%s status is %s' % (relmon['name'], relmon['status']))
        relmon_file = '%s.json' % (relmon['id'])
        remote_relmon_directory = 'relmon_test/%s' % (relmon['id'])
        with open(relmon_file, 'w') as json_file:
            json.dump(relmon, json_file, indent=4, sort_keys=True)

        condor_file = 'RELMON_%s.sub' % (relmon['id'])
        condor_file_content = ['executable              = RELMON_%s.sh' % (relmon['id']),
                               'output                  = RELMON_%s_$(ClusterId)_$(ProcId).out' % (relmon['id']),
                               'error                   = RELMON_%s_$(ClusterId)_$(ProcId).err' % (relmon['id']),
                               'log                     = RELMON_%s_$(ClusterId).log' % (relmon['id']),
                               'transfer_input_files    = %s,%s%s,%s%s' % (relmon_file,
                                                                           self.grid_location,
                                                                           self.cert_file_name,
                                                                           self.grid_location,
                                                                           self.key_file_name,),
                               'when_to_transfer_output = on_exit',
                               'request_cpus            = 2',
                               '+JobFlavour             = "tomorrow"',
                               'queue']

        condor_file_content = '\n'.join(condor_file_content)
        with open(condor_file, 'w') as file:
            file.write(condor_file_content)

        script_file = 'RELMON_%s.sh' % (relmon['id'])
        script_file_content = ['#!/bin/bash',
                               'DIR=$(pwd)',
                               'git clone https://github.com/justinasr/relmonservice2.git',
                               'scramv1 project CMSSW CMSSW_10_4_0',
                               'cd CMSSW_10_4_0/src',
                               'eval `scramv1 runtime -sh`',
                               'cd $DIR',
                               'mkdir -p Reports',
                               'python3 relmonservice2/remote_apparatus.py --relmon %s --cert %s --key %s' % (relmon_file,
                                                                                                              self.cert_file_name,
                                                                                                              self.key_file_name),
                               'rm *.root',
                               'tar -zcvf %s.tar.gz Reports' % (relmon['id'])]

        script_file_content = '\n'.join(script_file_content)
        with open(script_file, 'w') as file:
            file.write(script_file_content)

        stdout, stderr = self.execute_command('rm -rf %s; mkdir -p %s' % (remote_relmon_directory,
                                                                          remote_relmon_directory))

        self.copy_file(relmon_file, '%s/%s' % (remote_relmon_directory, relmon_file))
        self.copy_file(condor_file, '%s/%s' % (remote_relmon_directory, condor_file))
        self.copy_file(script_file, '%s/%s' % (remote_relmon_directory, script_file))

        os.remove(relmon_file)
        os.remove(condor_file)
        os.remove(script_file)

        stdout, stderr = self.execute_command('cd %s; condor_submit %s' % (remote_relmon_directory, condor_file))
        if not stderr and '1 job(s) submitted to cluster' in stdout:
            # output is "1 job(s) submitted to cluster 801341"
            relmon['status'] = 'submitted'
            condor_id = int(float(stdout.split()[-1]))
            relmon['condor_id'] = condor_id
            relmon['condor_status'] = '<unknown>'
        else:
            logging.error('Error submitting: %s. Output: %s' % (stderr, stdout))
            relmon['status'] = 'failed'

        logging.info('%s status is %s' % (relmon['name'], relmon['status']))
        self.persistent_storage.update_relmon(relmon)

    def check_if_running(self, relmon):
        logging.info('Will check if %s is running in HTCondor' % (relmon['name']))
        stdout, stderr = self.execute_command('condor_q -af:h ClusterId JobStatus | grep %s' % (relmon['condor_id']))
        if not stderr and not stdout:
            relmon['status'] = 'failed'
            relmon['condor_status'] = ''
        elif not stderr:
            status_number = stdout.split()[-1]
            if status_number == '4':
                relmon['condor_status'] = 'DONE'
            elif status_number == '2':
                relmon['condor_status'] = 'RUN'
            elif status_number == '1':
                relmon['condor_status'] = 'IDLE'
            else:
                relmon['condor_status'] = '<unknown>'
                logging.info('Unknown status %s?' % (status_number))
        else:
            logging.error('Error with HTCondor?')
            return

        self.persistent_storage.update_relmon(relmon)

    def collect_output(self, relmon):
        relmon['status'] = 'done'
        self.persistent_storage.update_relmon(relmon)

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


def uncaught_exception_to_log_decorator(func):
    """Decorate methods to log uncaught exceptions"""
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            logging.exception("Uncaught exception in " + func.__name__)
            raise
    return decorator


class Controller(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.persistent_storage = PersistentStorage()
        self.start()

    @uncaught_exception_to_log_decorator
    def run(self):
        sleep_duration = 30
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

    def submit_to_condor(self, relmon):
        logging.info('Will submit %s to HTCondor' % (relmon['name']))
        relmon['status'] = 'submitting'
        for category in relmon['categories']:
            category['lists']['reference'] = [{'name': x['name'], 'file_name': '-', 'file_status': 'initial', 'file_size': 0} for x in category['lists']['reference']]
            category['lists']['target'] = [{'name': x['name'], 'file_name': '-', 'file_status': 'initial', 'file_size': 0} for x in category['lists']['target']]

        self.persistent_storage.update_relmon(relmon)
        logging.info('Setting %s to %s' % (relmon['name'], relmon['status']))




        with open('/home/jrumsevi/auth.txt') as json_file:  
            credentials = json.load(json_file)

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect('lxplus.cern.ch',
                           username=credentials["username"],
                           password=credentials["password"],
                           timeout=15)

        relmon_file = '%s.json' % (relmon['id'])
        remote_relmon_directory = 'relmon_test/%s' % (relmon['id'])
        with open(relmon_file, 'w') as json_file:  
            json.dump(relmon, json_file, indent=4, sort_keys=True)

        condor_file = 'RELMON_%s.sub' % (relmon['id'])
        condor_file_content = ['executable            = RELMON_%s.sh' % (relmon['id']),
                               'arguments             = $(ClusterId) $(ProcId)',
                               'output                = job.$(ClusterId).$(ProcId).out',
                               'error                 = job.$(ClusterId).$(ProcId).err',
                               'log                   = job.$(ClusterId).log',
                               'transfer_input_files  = %s,%s,%s' % (relmon_file, '/afs/cern.ch/user/j/jrumsevi/private/user.crt.pem', '/afs/cern.ch/user/j/jrumsevi/private/user.key.pem'),
                               # 'transfer_output_files = job.$(ClusterId).$(ProcId).out',
                               # By default all files will be trasferred
                               'request_cpus          = 4',
                               '+JobFlavour           = "longlunch"',
                               'queue']

        condor_file_content = '\n'.join(condor_file_content)
        with open(condor_file, 'w') as file:
            file.write(condor_file_content)

        script_file = 'RELMON_%s.sh' % (relmon['id'])
        script_file_content = ['#!/bin/bash',
                               'DIR=$(pwd)',
                               'git clone https://github.com/justinasr/relmonservice2.git',
                               'scramv1 project CMSSW CMSSW_7_4_0',
                               'cd CMSSW_7_4_0/src',
                               'eval `scramv1 runtime -sh`',
                               'cd $DIR',
                               'mkdir Reports',
                               'python3 relmonservice2/downloader.py --config %s --cert user.crt.pem --key user.key.pem' % (relmon_file),
                               'rm *.root',
                               'tar -zcvf %s.tar.gz Reports' % (relmon['id'])]

        script_file_content = '\n'.join(script_file_content)
        with open(script_file, 'w') as file:
            file.write(script_file_content)

        (_, stdout, stderr) = ssh_client.exec_command('mkdir -p %s' % (remote_relmon_directory))
        ftp_client = ssh_client.open_sftp()
        ftp_client.put(relmon_file, '%s/%s' % (remote_relmon_directory, relmon_file))
        ftp_client.put(condor_file, '%s/%s' % (remote_relmon_directory, condor_file))
        ftp_client.put(script_file, '%s/%s' % (remote_relmon_directory, script_file))

        # NOTE exec_command timeout does not work. Think of something..
        (_, stdout, stderr) = ssh_client.exec_command('ls -lh %s' % (remote_relmon_directory))
        logging.info("STDOUT: %s" % (stdout.read().decode('utf-8')))
        logging.info("STDERR: %s" % (stderr.read()))

        (_, stdout, stderr) = ssh_client.exec_command('cd %s; condor_submit %s' % (remote_relmon_directory, condor_file))
        logging.info("STDOUT: %s" % (stdout.read().decode('utf-8')))
        logging.info("STDERR: %s" % (stderr.read()))

        ftp_client.close()
        ssh_client.close()

        os.remove(relmon_file)
        os.remove(condor_file)
        os.remove(script_file)


        # output is "1 job(s) submitted to cluster 801341"
        relmon['status'] = 'submitted'
        self.persistent_storage.update_relmon(relmon)
        logging.info('Setting %s to %s' % (relmon['name'], relmon['status']))

"""
RelMon report production controller
Runs main loop that checks status and acts accordingly
"""

import logging
from persistent_storage import PersistentStorage
import json
import os
import shutil
from ssh_executor import SSHExecutor
from relmon import RelMon
from file_creator import FileCreator


class Controller():

    # Directory in remote host to keep files for submission and collect output
    __remote_directory = 'relmon_test/'
    # GRID certificate file
    __grid_cert = '/afs/cern.ch/user/j/jrumsevi/private/user.crt.pem'
    # GRID key file
    __grid_key = '/afs/cern.ch/user/j/jrumsevi/private/user.key.pem'
    # Place where results should be moved
    __web_location = '/eos/project/c/cmsweb/www/pdmv-web-test/relmon_test/'

    def __init__(self):
        self.is_tick_running = False
        self.persistent_storage = PersistentStorage()
        self.ssh_executor = SSHExecutor()
        self.logger = logging.getLogger('logger')
        self.file_creator = FileCreator(self.__grid_cert,
                                        self.__grid_key,
                                        self.__remote_directory,
                                        self.__web_location)
        self.relmons_to_reset = []
        self.relmons_to_delete = []

    def tick(self):
        """
        Controller works by doing "ticks" every once in a while
        During a tick it shoud check all existing relmon's and
        their status and, if necessary, perform actions like
        submission or output collection
        """
        self.logger.info('Controller tick')
        data = self.persistent_storage.get_all_data()
        self.logger.info('Found %s relmons for reset, termination, deletion' % (len(data)))
        for relmon_json in data:
            relmon = RelMon(relmon_json)
            relmon_id = relmon.get_id()
            if relmon_id in self.relmons_to_reset:
                self.relmons_to_reset.remove(relmon_id)
                self.__reset_relmon(relmon)

            if relmon_id in self.relmons_to_delete:
                self.relmons_to_delete.remove(relmon_id)
                self.__delete_relmon(relmon)

        data = self.persistent_storage.get_all_data()
        self.logger.info('Found %s relmons' % (len(data)))

        for relmon_json in data:
            relmon = RelMon(relmon_json)
            status = relmon.get_status()
            condor_status = relmon.get_condor_status()
            self.logger.info('%s status is %s, HTCondor status %s' % (relmon, status, condor_status))
            if status == 'new':
                # If it is new, submit it
                self.__submit_to_condor(relmon)
            elif status == 'submitted' or status == 'running' or status == 'finishing':
                # If it is running, check on it's condor status
                self.__check_if_running(relmon)
            elif status == 'finished' or condor_status == 'DONE':
                # Check status once again and collect logs
                self.__check_if_running(relmon)
                self.__collect_output(relmon)

        self.ssh_executor.close_connections()
        self.logger.info('Controller tick finished')

    def add_to_reset_list(self, relmon_id):
        if relmon_id not in self.relmons_to_reset:
            self.relmons_to_reset.append(relmon_id)

    def add_to_delete_list(self, relmon_id):
        if relmon_id not in self.relmons_to_delete:
            self.relmons_to_delete.append(relmon_id)

    def __submit_to_condor(self, relmon):
        relmon_id = relmon.get_id()
        relmon_name = relmon.get_name()
        remote_relmon_directory = '%s%s' % (self.__remote_directory, relmon_id)
        self.logger.info('Will submit %s to HTCondor' % (relmon))
        self.logger.info('Remote directory: %s' % (remote_relmon_directory))
        relmon.reset()
        self.persistent_storage.update_relmon(relmon.get_json())
        self.logger.info('%s status is %s' % (relmon, relmon.get_status()))
        try:
            # Dump the json to a file
            relmon_file = self.file_creator.create_relmon_file(relmon)
            # Create HTCondor submit file
            condor_file = self.file_creator.create_condor_job_file(relmon, relmon_file)
            # Create actual job script file
            script_file = self.file_creator.create_job_script_file(relmon, relmon_file)

            # Prepare remote directory. Delete old one and create a new one
            self.ssh_executor.execute_command([
                'rm -rf %s' % (remote_relmon_directory),
                'mkdir -p %s' % (remote_relmon_directory)
            ])

            # Upload relmon json, submit file and script to run
            self.ssh_executor.upload_file(relmon_file, '%s/%s' % (remote_relmon_directory, relmon_file))
            self.ssh_executor.upload_file(condor_file, '%s/%s' % (remote_relmon_directory, condor_file))
            self.ssh_executor.upload_file(script_file, '%s/%s' % (remote_relmon_directory, script_file))

            # Delete files locally
            os.remove(relmon_file)
            os.remove(condor_file)
            os.remove(script_file)

            # Run condor_submit
            # Submission happens through lxplus as condor is not available on website machine
            # It is easier to ssh to lxplus than set up condor locally
            stdout, stderr = self.ssh_executor.execute_command([
                'cd %s' % (remote_relmon_directory),
                'condor_submit %s' % (condor_file)
            ])
            # Parse result of condor_submit
            if not stderr and '1 job(s) submitted to cluster' in stdout:
                # output is "1 job(s) submitted to cluster 801341"
                relmon.set_status('submitted')
                condor_id = int(float(stdout.split()[-1]))
                relmon.set_condor_id(condor_id)
                relmon.set_condor_status('IDLE')
                self.logger.info('Submitted %s. Condor job id %s' % (relmon, condor_id))
            else:
                self.logger.error('Error submitting %s' % (relmon))
                relmon.set_status('failed')

        except Exception as ex:
            relmon.set_status('failed')
            self.logger.error('Exception while trying to submit %s: %s' % (relmon,
                                                                           str(ex)))

        self.logger.info('%s status is %s' % (relmon, relmon.get_status()))
        self.persistent_storage.update_relmon(relmon.get_json())

    def __check_if_running(self, relmon):
        relmon_condor_id = relmon.get_condor_id()
        self.logger.info('Will check if %s is running in HTCondor, id: %s' % (relmon, relmon_condor_id))
        stdout, stderr = self.ssh_executor.execute_command(
            'condor_q -af:h ClusterId JobStatus | grep %s' % (relmon_condor_id)
        )
        new_condor_status = '<unknown>'
        if stdout and not stderr:
            status_number = stdout.split()[-1]
            self.logger.info('Relmon %s status is %s' % (relmon, status_number))
            status_dict = {
                '0': 'UNEXPLAINED',
                '1': 'IDLE',
                '2': 'RUN',
                '3': 'REMOVED',
                '4': 'DONE',
                '5': 'HOLD',
                '6': 'SUBMISSION ERROR'
            }
            new_condor_status = status_dict.get(status_number, 'REMOVED')
        else:
            self.logger.error('Error with HTCondor? Check if running returned:\nstdout: %s,\nstderr: %s' % (stdout, stderr))

        self.logger.info('Saving %s condor status as %s' % (relmon, new_condor_status))
        relmon.set_condor_status(new_condor_status)
        self.persistent_storage.update_relmon(relmon.get_json())

    def __collect_output(self, relmon):
        condor_status = relmon.get_condor_status()
        if condor_status not in ['DONE', 'REMOVED', '<unknown>']:
            self.logger.info('%s is still running, will not try to collect' % (relmon))
            return

        relmon_id = relmon.get_id()
        remote_relmon_directory = '%s%s/' % (self.__remote_directory, relmon_id)
        relmon_logs = 'logs/%s/' % (relmon_id)
        shutil.rmtree(relmon_logs, ignore_errors=True)
        os.mkdir(relmon_logs)

        self.ssh_executor.download_file(
            '%svalidation_matrix.log' % (remote_relmon_directory),
            '%svalidation_matrix.log' % (relmon_logs)
        )
        self.ssh_executor.download_file(
            '%sRELMON_%s.out' % (remote_relmon_directory, relmon_id),
            '%sRELMON_%s.out' % (relmon_logs, relmon_id)
        )
        self.ssh_executor.download_file(
            '%sRELMON_%s.log' % (remote_relmon_directory, relmon_id),
            '%sRELMON_%s.log' % (relmon_logs, relmon_id)
        )
        self.ssh_executor.download_file(
            '%sRELMON_%s.err' % (remote_relmon_directory, relmon_id),
            '%sRELMON_%s.err' % (relmon_logs, relmon_id)
        )

        stdout, stderr = self.ssh_executor.execute_command([
            'cd %s' % (remote_relmon_directory),
            'cd ..',
            'rm -r %s' % (relmon_id)]
        )
        relmon.set_status('done')
        self.persistent_storage.update_relmon(relmon.get_json())

    def __reset_relmon(self, relmon):
        self.__terminate_relmon(relmon)
        relmon.reset()
        self.persistent_storage.update_relmon(relmon.get_json())

    def __terminate_relmon(self, relmon):
        self.logger.info('Trying to terminate %s' % (relmon))
        condor_id = relmon.get_condor_id()
        if condor_id > 0:
            self.ssh_executor.execute_command('condor_rm %s' % (condor_id))
        else:
            self.logger.info('Relmon %s HTCondor id is not valid: %s' % (relmon, condor_id))

        self.logger.info('Finished terminating relmon %s' % (relmon))

    def __delete_relmon(self, relmon):
        self.__terminate_relmon(relmon)
        self.persistent_storage.delete_relmon(relmon.get_id())

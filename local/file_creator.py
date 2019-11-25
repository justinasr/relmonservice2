"""
Module for FileCreator
"""
import json


class FileCreator():
    """
    File creator creates bash executable for condor and condor submission job file
    """

    def __init__(self, config):
        self.remote_location = config['remote_directory']
        self.web_location = config['web_location']
        if self.web_location[-1] == '/':
            self.web_location = self.web_location[:-1]

        self.grid_cert_path = config['grid_certificate']
        self.grid_key_path = config['grid_key']
        self.grid_cert_file = self.grid_cert_path.split('/')[-1]
        self.grid_key_file = self.grid_key_path.split('/')[-1]
        self.cookie_url = config['cookie_url']
        self.callback_url = config['callback_url']

    def create_job_script_file(self, relmon):
        """
        Create bash executable for condor
        """
        relmon_id = relmon.get_id()
        cpus = relmon.get_cpu()
        relmon_name = relmon.get_name()
        script_file_name = f'relmons/{relmon_id}/{relmon_id}.sh'
        web_sqlite_path = f'"{self.web_location}/{relmon_name}.sqlite"'
        script_file_content = [
            '#!/bin/bash',
            'DIR=$(pwd)',
            # Clone the relmon service
            'git clone https://github.com/justinasr/relmonservice2.git',
            # Make a cookie for callbacks about progress
            f'cern-get-sso-cookie -u {self.cookie_url} -o cookie.txt',
            'cp cookie.txt relmonservice2/remote',
            # CMSSW environment setup
            'scramv1 project CMSSW CMSSW_10_4_0',
            'cd CMSSW_10_4_0/src',
            # Open scope for CMSSW
            '(',
            'eval `scramv1 runtime -sh`',
            'cd $DIR',
            # Create reports directory
            'mkdir -p Reports',
            # Run the remote apparatus
            'python3 relmonservice2/remote/remote_apparatus.py '  # No newlines here
            f'-r {relmon_id}.json '
            f'-c {self.grid_cert_file} '
            f'-k {self.grid_key_file} '
            f'--cpus {cpus}'
            f'--callback {self.callback_url}',
            # Close scope for CMSSW
            ')',
            'cd $DIR',
            # Remove all root files
            'rm *.root',
            # Copy sqlitify to Reports directory
            'cp relmonservice2/remote/sqltify.py Reports/sqltify.py',
            # Go to reports directory
            'cd Reports',
            # Run sqltify
            'python3 sqltify.py',
            # Checksum for created sqlite
            'echo "HTCondor workspace"',
            'echo "MD5 Sum"',
            'md5sum reports.sqlite',
            # List sizes
            'ls -l reports.sqlite',
            # Do integrity check
            'echo "Integrity check:"',
            'echo "PRAGMA integrity_check" | sqlite3 reports.sqlite',
            # Remove sql file from web path
            f'rm -rf {web_sqlite_path}',
            # Copy reports sqlite to web path
            f'time rsync -v reports.sqlite {web_sqlite_path}',
            # Checksum for created sqlite
            'echo "EOS space"',
            'echo "MD5 Sum"',
            f'md5sum {web_sqlite_path}',
            # List sizes
            f'ls -l {web_sqlite_path}',
            # Do integrity check
            'echo "Integrity check:"',
            f'echo "PRAGMA integrity_check" | sqlite3 {web_sqlite_path}',
            'cd $DIR',
            f'cern-get-sso-cookie -u {self.cookie_url} -o cookie.txt',
            'cp cookie.txt relmonservice2/remote',
            'python3 relmonservice2/remote/remote_apparatus.py '  # No newlines here
            f'-r {relmon_id}.json '
            f'--callback {self.callback_url}'
            '--notifyfinished'
        ]

        script_file_content_string = '\n'.join(script_file_content)
        with open(script_file_name, 'w') as output_file:
            output_file.write(script_file_content_string)

    @classmethod
    def create_relmon_file(cls, relmon):
        """
        Dump relmon to a JSON file
        """
        relmon_id = relmon.get_id()
        relmon_data = relmon.get_json()
        relmon_file_name = f'relmons/{relmon_id}/{relmon_id}.json'
        with open(relmon_file_name, 'w') as output_file:
            json.dump(relmon_data, output_file, indent=2, sort_keys=True)

    def create_condor_job_file(self, relmon):
        """
        Create a condor job file for a relmon
        """
        relmon_id = relmon.get_id()
        cpus = relmon.get_cpu()
        memory = relmon.get_memory()
        disk = relmon.get_disk()
        condor_file_name = f'relmons/{relmon_id}/{relmon_id}.sub'
        condor_file_content = [
            f'executable            = RELMON_{relmon_id}.sh',
            f'output                = {relmon_id}.out',
            f'error                 = {relmon_id}.err',
            f'log                   = {relmon_id}.log',
            f'transfer_input_files  = {relmon_id}.json,{self.grid_cert_path},{self.grid_key_path}',
            'when_to_transfer_output = on_exit',
            f'request_cpus          = {cpus}',
            f'request_memory        = {memory}',
            f'request_disk          = {disk}',
            '+JobFlavour            = "tomorrow"',
            '+JobPrio               = 1',
            'requirements           = (OpSysAndVer =?= "SLCern6")',
            # Leave in queue when status is DONE for two hours - 7200 seconds
            'leave_in_queue         = JobStatus == 4 && (CompletionDate =?= UNDEFINED'
            '                         || ((CurrentTime - CompletionDate) < 7200))',
            'queue'
        ]

        condor_file_content_string = '\n'.join(condor_file_content)
        with open(condor_file_name, 'w') as output_file:
            output_file.write(condor_file_content_string)

import json


class FileCreator():
    def __init__(self, grid_cert, grid_key, remote_location, web_location):
        self.grid_cert = grid_cert
        self.grid_key = grid_key
        self.remote_location = remote_location
        self.web_location = web_location
        self.grid_cert_file = grid_cert.split('/')[-1]
        self.grid_key_file = grid_key.split('/')[-1]

    def create_job_script_file(self, relmon, relmon_data_file_name):
        relmon_id = relmon.get_id()
        cpus = relmon.get_cpu()
        relmon_name = relmon.get_name()
        script_file_name = 'RELMON_%s.sh' % (relmon_id)
        web_sqlite_path = '"%s%s.sqlite"' % (self.web_location, relmon_name)
        script_file_content = [
            '#!/bin/bash',
            'DIR=$(pwd)',
            'git clone https://github.com/justinasr/relmonservice2.git',
            'cern-get-sso-cookie -u https://cms-pdmv.cern.ch/mcm -o cookie.txt',
            'mv cookie.txt relmonservice2',
            'scramv1 project CMSSW CMSSW_10_4_0',
            'cd CMSSW_10_4_0/src',
            '(',
            'eval `scramv1 runtime -sh`',
            'cd $DIR',
            'mkdir -p Reports',
            'python3 relmonservice2/remote_apparatus.py '  # No newline here
            '--relmon %s --cert %s --key %s --cpus %s' % (relmon_data_file_name,
                                                          self.grid_cert_file,
                                                          self.grid_key_file,
                                                          cpus),
            ')',
            'cd $DIR',
            # Remove all root files
            'rm *.root',
            # Copy sqlitify to Reports directory
            'cp relmonservice2/sqltify.py Reports/sqltify.py',
            # Go to reports directory
            'cd Reports',
            # Run sqltify
            'python3 sqltify.py',
            # Remove sql file from web path
            'rm -rf %s' % (web_sqlite_path),
            # Checksum for created sqlite
            'echo "HTCondor workspace"',
            'echo "MD5 Sum"',
            'md5sum reports.sqlite',
            # List sizes
            'ls -l reports.sqlite',
            # Do integrity check
            'echo "Integrity check:"',
            'echo "PRAGMA integrity_check" | sqlite3 reports.sqlite',
            # Copy reports sqlite to web path
            'time rsync -v reports.sqlite %s' % (web_sqlite_path),
            # Checksum for created sqlite
            'echo "EOS space"',
            'echo "MD5 Sum"',
            'md5sum %s' % (web_sqlite_path),
            # List sizes
            'ls -l %s' % (web_sqlite_path),
            # Do integrity check
            'echo "Integrity check:"',
            'echo "PRAGMA integrity_check" | sqlite3 %s' % (web_sqlite_path),
            'cd $DIR',
            'cern-get-sso-cookie -u https://cms-pdmv.cern.ch/mcm -o cookie.txt',
            'mv cookie.txt relmonservice2',
            'python3 relmonservice2/remote_apparatus.py --relmon %s.json --notify-finished' % (relmon_id)
        ]

        script_file_content = '\n'.join(script_file_content)
        with open(script_file_name, 'w') as file:
            file.write(script_file_content)

        return script_file_name

    def create_relmon_file(self, relmon):
        relmon_id = relmon.get_id()
        relmon_data = relmon.get_json()
        relmon_file_name = '%s.json' % (relmon_id)
        with open(relmon_file_name, 'w') as json_file:
            json.dump(relmon_data, json_file, indent=2, sort_keys=True)

        return relmon_file_name

    def create_condor_job_file(self, relmon, relmon_data_file_name):
        relmon_id = relmon.get_id()
        cpus = relmon.get_cpu()
        memory = relmon.get_memory()
        disk = relmon.get_disk()
        condor_file_name = 'RELMON_%s.sub' % (relmon_id)
        condor_file_content = [
            'executable              = RELMON_%s.sh' % (relmon_id),
            'output                  = RELMON_%s.out' % (relmon_id),
            'error                   = RELMON_%s.err' % (relmon_id),
            'log                     = RELMON_%s.log' % (relmon_id),
            'transfer_input_files    = %s,%s,%s' % (relmon_data_file_name,
                                                    self.grid_cert,
                                                    self.grid_key),
            'when_to_transfer_output = on_exit',
            'request_cpus            = %s' % (cpus),
            'request_memory          = %s' % (memory),
            'request_disk            = %s' % (disk),
            '+JobFlavour             = "tomorrow"',
            'requirements            = (OpSysAndVer =?= "SLCern6")',
            # Leave in queue when status is DONE for two hours - 7200 seconds
            'leave_in_queue          = JobStatus == 4 && (CompletionDate =?= UNDEFINED || ((CurrentTime - CompletionDate) < 7200))',
            'queue'
        ]

        condor_file_content = '\n'.join(condor_file_content)
        with open(condor_file_name, 'w') as file:
            file.write(condor_file_content)

        return condor_file_name
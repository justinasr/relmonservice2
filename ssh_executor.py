import paramiko
import logging
import json


class SSHExecutor():

    # Path to credentials, used to connect to lxplus
    __credentials_file_path = '/home/jrumsevi/auth.txt'
    # lxplus host name
    __remote_host = 'lxplus.cern.ch'

    def __init__(self):
        self.ssh_client = None
        self.ftp_client = None
        self.logger = logging.getLogger('logger')

    def setup_ssh(self):
        """
        Initiate SSH connection and save it as self.ssh_client
        """
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
        """
        Initiate SFTP connection and save it as self.ftp_client
        If needed, SSH connection will be automatically set up
        """
        if self.ftp_client:
            self.close_connections()

        if not self.ssh_client:
            self.setup_ssh()

        self.ftp_client = self.ssh_client.open_sftp()

    def execute_command(self, command):
        """
        Execute command over SSH
        """
        if not self.ssh_client:
            self.setup_ssh()

        if isinstance(command, list):
            command = '; '.join(command)

        self.logger.info('Executing %s' % (command))
        (_, stdout, stderr) = self.ssh_client.exec_command(command)
        stdout = stdout.read().decode('utf-8').strip()
        stderr = stderr.read().decode('utf-8').strip()
        if stdout:
            self.logger.info("STDOUT (%s): %s" % (command, stdout))

        if stderr:
            self.logger.error("STDERR (%s): %s" % (command, stderr))

        return stdout, stderr

    def upload_file(self, copy_from, copy_to):
        """
        Upload a file
        """
        if not self.ftp_client:
            self.setup_ftp()

        try:
            self.ftp_client.put(copy_from, copy_to)
        except Exception as ex:
            self.logger.error('Error uploading file from %s to %s. %s' % (copy_from, copy_to, ex))

    def download_file(self, copy_from, copy_to):
        """
        Download file from remote host
        """
        if not self.ftp_client:
            self.setup_ftp()

        try:
            self.ftp_client.get(copy_from, copy_to)
        except Exception as ex:
            self.logger.error('Error downloading file from %s to %s. %s' % (copy_from, copy_to, ex))

    def close_connections(self):
        """
        Close any active connections
        """
        if self.ftp_client:
            self.ftp_client.close()
            self.ftp_client = None

        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

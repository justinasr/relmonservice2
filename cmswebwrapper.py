import http.client
import logging
import json


class CMSWebWrapper():

    __cache = {}

    def __init__(self, cert_file, key_file):
        self.cert_file = cert_file
        self.key_file = key_file

    def get_connection(self):
        if self.cert_file is None or self.key_file is None:
            raise Exception('Missing USERCRT or USERKEY environment variables')

        return http.client.HTTPSConnection('cmsweb.cern.ch',
                                           port=443,
                                           cert_file=self.cert_file,
                                           key_file=self.key_file)

    def get(self, path, cache=True):
        logging.info('Will try to GET %s' % (path))
        if cache and path in self.__cache:
            return self.__cache[path]

        connection = self.get_connection()
        connection.request('GET', path, headers={"Accept": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            logging.error("Problems (%d) with %s: %s" % (response.status, path, response.read()))
            connection.close()
            return None

        decoded_response = response.read().decode('utf-8')
        if cache:
            self.__cache[path] = decoded_response

        connection.close()
        return decoded_response

    def get_big_file(self, path, filename=None):
        logging.info('Will try to download file %s' % (path))
        if filename is None:
            filename = path.split('/')[-1]
            logging.info('Using file name %s for %s' % (filename, path))

        connection = self.get_connection()
        connection.request('GET', path)
        response = connection.getresponse()
        chunk_size = 1024 * 1024 * 4 # 4 megabytes
        with open(filename, "wb") as file:
            while True:
                chunk = response.read(chunk_size)
                if chunk:
                    file.write(chunk)
                    file.flush()
                else:
                    break

        connection.close()
        return filename

    def get_workflow(self, workflow_name):
        workflow_string = self.get('/reqmgr2/data/request?name=%s' % (workflow_name))
        if not workflow_string:
            return None

        try:
            workflow = json.loads(workflow_string)
            # 'result' is a list of elements and each of them is dictionary that has workflow name as key
            return workflow.get('result', [{}])[0].get(workflow_name)
        except:
            logging.error('Failed to parse workflow %s JSON %s' % (workflow_name, workflow_string))
            return None

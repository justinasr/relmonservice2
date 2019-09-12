from urllib.request import Request, urlopen
from urllib.error import HTTPError
import logging
import json
import time


class Database:
    PAGE_SIZE = 25

    def __init__(self):
        self.logger = logging.getLogger('logger')
        self.database_url = 'http://localhost:5984'
        self.relmons_table = self.database_url + '/relmons'
        self.relmons_status_view = self.relmons_table + '/_design/_designDoc/_view/status'

    def update_relmon(self, relmon, update_timestamp=True):
        try:
            relmon_json = relmon.get_json()
            relmon_json['last_update'] = int(time.time())
            url = '%s/%s' % (self.relmons_table, relmon_json['id'])
            self.make_request(url, relmon_json, 'PUT')
        except HTTPError as err:
            self.logger.error(str(err))

    def delete_relmon(self, relmon):
        relmon_id = relmon.get_id()
        relmon_json = self.get_relmon(relmon_id)
        if relmon_json is not None and relmon_json.get('_rev') is not None:
            rev = relmon_json['_rev']
            url = '%s/%s?rev=%s' % (self.relmons_table, relmon_id, rev)
            self.make_request(url, method='DELETE')

    def get_relmon_count(self):
        return self.make_request(self.relmons_table)['doc_count']

    def get_relmon(self, relmon_id):
        url = self.relmons_table + '/' + relmon_id
        try:
            return self.make_request(url)
        except HTTPError as err:
            if err.code != 404:
                self.logger.error(str(err))

            return None

    def get_relmons(self, page=0, page_size=PAGE_SIZE, include_docs=False):
        url = '%s/_all_docs?limit=%d&skip=%d&include_docs=%s' % (self.relmons_table,
                                                                 page_size,
                                                                 page * page_size,
                                                                 'True' if include_docs else 'False')
        rows = self.make_request(url)['rows']
        if include_docs:
            return [x['doc'] for x in rows if '_design' not in x['id']]
        else:
            return [x['id'] for x in rows if '_design' not in x['id']]

    def get_relmons_with_status(self, status, page=0, page_size=PAGE_SIZE, include_docs=False):
        url = '%s?key="%s"&limit=%d&skip=%d&include_docs=%s' % (self.relmons_status_view,
                                                                status,
                                                                page_size,
                                                                page * page_size,
                                                                'True' if include_docs else 'False')
        rows = self.make_request(url)['rows']
        if include_docs:
            return [x['doc'] for x in rows]
        else:
            return [x['id'] for x in rows]

    def make_request(self, url, data=None, method='GET'):
        if data is not None:
            data = json.dumps(data)

        req = Request(url, data=data, method=method)
        if (method == 'POST' or method == 'PUT') and data is not None:
            data = data.encode("utf-8")

        req.add_header('Content-Type', 'application/json')
        response = json.loads(urlopen(req, data=data).read().decode('utf-8'))
        return response
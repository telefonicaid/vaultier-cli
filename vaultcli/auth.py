#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrián López Tejedor <adrianlzt@gmail.com>
#                  Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

from vaultcli.workspacecypher import WorkspaceCypher
from vaultcli.exceptions import ResourceUnavailable, Unauthorized, Forbidden

from Cryptodome.Hash import SHA
from urllib.parse import urljoin

import binascii
import json
import requests

class Auth(object):
    """Base class for get Vaultier auth token"""
    def __init__(self, server, email, key, verify=True):
        self.server = server
        self.email = email
        self.key = key
        self.verify = verify

    def get_token(self):
        """
        Returns user token

        :return: user token string
        :rtype: string
        """
        work_space_cypher = WorkspaceCypher(self.key)
        server_time = self.fetch_json('/api/server-time').get('datetime')
        sha = SHA.new('{}{}'.format(self.email, server_time).encode('utf-8'))
        signature = binascii.b2a_base64(work_space_cypher.sign(sha))
        data = {'email': self.email, 'date': server_time, 'signature': signature}
        return self.fetch_json('/api/auth/auth', http_method='POST', data=data)['token']

    def fetch_json(self, uri_path, http_method='GET', headers={}, params={}, data=None, files=None):
        """Fetch JSON from API"""
        if self.verify == False:
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

        """Construct the full URL"""
        url = urljoin(self.server, uri_path)

        """Perform the HTTP request"""
        try:
            response = requests.request(http_method, url, params=params, headers=headers, data=data, files=files, verify=self.verify)
        except requests.exceptions.SSLError as e:
            err = 'SSL certificate error: {}'.format(e)
            raise SystemExit(err)

        if response.status_code == 401:
            raise Unauthorized('{0} at {1}'.format(response.text, url), response)
        if response.status_code == 403:
            raise Forbidden('{0} at {1}'.format(response.text, url), response)
        if response.status_code not in {200, 206}:
            raise ResourceUnavailable('{0} at {1}'.format(response.text, url), response)

        return response.json()

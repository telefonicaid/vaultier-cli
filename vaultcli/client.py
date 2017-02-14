#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrián López Tejedor <adrianlzt@gmail.com>
#                  Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

from vaultcli.workspace import Workspace
from vaultcli.vault import Vault
from vaultcli.card import Card
from vaultcli.secret import Secret
from vaultcli.cypher import Cypher
from vaultcli.exceptions import ResourceUnavailable, Unauthorized, Forbidden

from urllib.parse import urljoin

import json
import requests

class Client(object):
    """Base class for Vaultier API access"""
    def __init__(self, server, token, key=None):
        self.server = server
        self.token = token
        self.key = key

    def list_workspaces(self):
        """
        Returns all Workspaces for your user

        :return: a list of Python objects representing the workspaces
        :rtype: Workspace

        Each workspace has the following atributes:
            - id: workspace unique id
            - slug: workspace name slugged
            - name: workspace name
            - description: workspace description
            - workspaceKey: workspace key
        """
        json_obj = self.fetch_json('/api/workspaces')
        return [Workspace.from_json(obj) for obj in json_obj]

    def list_vaults(self, workspace_id):
        """
        Returns all Vaults from a Workspace

        :param workspace_id: Workspace unique ID given by list_workspaces
        :return: a list of Python objects representing the vaults
        :rtype: Vault

        Each vault has the following atributes:
            - id: vault unique id
            - slug: vault name slugged
            - name: vault name
            - description: vault description
            - color: vault color
            - workspace: workspace that contains this vault
        """
        json_obj = self.fetch_json('/api/vaults/?workspace={}'.format(workspace_id))
        return [Vault.from_json(obj) for obj in json_obj]

    def list_cards(self, vault_id):
        """
        Returns all Cards from a Vault

        :param vault_id: Vault unique ID given by list_vaults
        :return: a list of Python objects representing the cards
        :rtype: Card

        Each card has the following atributes:
            - id: card unique id
            - slug: card name slugged
            - name: card name
            - description: card description
            - vault: vault that contains this card
        """
        json_obj = self.fetch_json('/api/cards/?vault={}'.format(vault_id))
        return [Card.from_json(obj) for obj in json_obj]

    def list_secrets(self, card_id):
        """
        Returns all Secrets from a Card

        :param card_id: Card unique ID given by list_vaults
        :return: a list of Python objects representing the secrets
        :rtype: Secret

        Each secret has the following atributes:
            - id: secret unique id
            - type: secret type (100: Note, 200: Password, 300: File)
            - name: secret name
            - data: secret data
            - blobMeta: secret meta (only in type 300/file)
            - card: card that contains this secret
        """
        json_obj = self.fetch_json('/api/secrets/?card={}'.format(card_id))
        return [Secret.from_json(obj) for obj in json_obj]

    def get_secret(self, secret_id):
        """
        Returns a Secret desencrypted from an secret ID

        :param secret_id: Secret unique ID given by list_secrets
        :return: a secret object
        :rtype: Secret
        """
        secret = Secret.from_json(self.fetch_json('/api/secrets/{}'.format(secret_id)))
        vault_id = self.fetch_json('/api/cards/{}'.format(secret.card))['vault']
        workspace_id = self.fetch_json('/api/vaults/{}'.format(vault_id))['workspace']
        workspace_key = self.fetch_json('/api/workspaces/{}'.format(workspace_id))['membership']['workspace_key']

        # If has data decrypt it with workspace_key
        if secret.data:
            secret.data = json.loads(Cypher(self.key).decrypt(workspace_key, secret.data))
        # If has meta decrypt it with workspace_key
        if secret.blobMeta:
            secret.blobMeta = json.loads(Cypher(self.key).decrypt(workspace_key, secret.blobMeta))

        return secret

    def get_file(self, secret_id):
        """
        Returns a secret file desencrypted from an secret ID

        :param secret_id: Secret unique ID given by list_secrets
        :return: data
        :rtype: binary data
        """
        secret = Secret.from_json(self.fetch_json('/api/secrets/{}'.format(secret_id)))
        if secret.blobMeta:
            vault_id = self.fetch_json('/api/cards/{}'.format(secret.card))['vault']
            workspace_id = self.fetch_json('/api/vaults/{}'.format(vault_id))['workspace']
            workspace_key = self.fetch_json('/api/workspaces/{}'.format(workspace_id))['membership']['workspace_key']
            data = self.fetch_json('/api/secret_blobs/{}'.format(secret_id))['blob_data']
            file_name = json.loads(Cypher(self.key).decrypt(workspace_key, secret.blobMeta))['filename']
            file_data = bytes(json.loads(Cypher(self.key).decrypt(workspace_key, data))['filedata'], "iso-8859-1")
            return [file_name, file_data]
        else:
            return [None, None]

    def set_secret(self, secret):
        """
        Send secret contents to existing secret ID

        :param secret: secret object that contains the data
        """
        vault_id = self.fetch_json('/api/cards/{}'.format(secret.card))['vault']
        workspace_id = self.fetch_json('/api/vaults/{}'.format(vault_id))['workspace']
        workspace_key = self.fetch_json('/api/workspaces/{}'.format(workspace_id))['membership']['workspace_key']
        encrypted_data = Cypher(self.key).encrypt(workspace_key, json.dumps(secret.data))
        data = {
                'name': secret.name,
                'type': secret.type,
                'card': secret.card,
                'id': secret.id,
                'data': encrypted_data
               }
        self.fetch_json('/api/secrets/{}/'.format(secret.id), http_method='PUT', data=json.dumps(data))

    def fetch_json(self, uri_path, http_method='GET', headers={}, params={}, data=None, files=None, verify=False):
        """Fetch JSON from API"""
        headers['X-Vaultier-Token'] = self.token
        if http_method in ('POST', 'PUT', 'DELETE') and not files:
            headers['Content-Type'] = 'application/json; charset=utf-8'

        """Construct the full URL"""
        url = urljoin(self.server, uri_path)

        """Perform the HTTP request"""
        response = requests.request(http_method, url, params=params, headers=headers, data=data, files=files, verify=verify)

        if response.status_code == 401:
            raise Unauthorized('{0} at {1}'.format(response.text, url), response)
        if response.status_code == 403:
            raise Forbidden('{0} at {1}'.format(response.text, url), response)
        if response.status_code not in {200, 206}:
            raise ResourceUnavailable('{0} at {1}'.format(response.text, url), response)

        return response.json()

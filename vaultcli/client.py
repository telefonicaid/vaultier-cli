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
from os.path import basename
from mimetypes import MimeTypes

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

    def get_workspace_name(self, workspace_id):
        """
        Returns a Workspace name form id

        :param workspace_id: Workspace unique ID given by list_workspaces
        :return: workspace name
        :rtype: string
        """
        json_obj = self.fetch_json('/api/workspaces/{}/'.format(workspace_id))
        return json_obj['name']

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

    def set_workspace(self, workspace_id, workspace_data):
        """
        Send workspace contents to existing workspace ID

        :param workspace_id: workspace unique ID given by list_workspaces
        :param workspace_data: Python dict with new contents
        """
        current_workspace_data = self.fetch_json('/api/workspaces/{}'.format(workspace_id))
        if workspace_data.get('name', None) == None: workspace_data['name'] = current_workspace_data['name']
        if workspace_data.get('description', None) == None: workspace_data['description'] = current_workspace_data['description']
        self.fetch_json('/api/workspaces/{}/'.format(workspace_id), http_method='PUT', data=json.dumps(workspace_data))


    def set_vault(self, vault_id, vault_data):
        """
        Send vault contents to existing vault ID

        :param vault_id: Vault unique ID given by list_vaults
        :param vault_data: Python dict with new contents
        """
        current_vault_data = self.fetch_json('/api/vaults/{}'.format(vault_id))
        if vault_data.get('name', None) == None: vault_data['name'] = current_vault_data['name']
        if vault_data.get('description', None) == None: vault_data['description'] = current_vault_data['description']
        if vault_data.get('color', None) == None: vault_data['color'] = current_vault_data['color']
        vault_data['workspace'] = current_vault_data['workspace']
        self.fetch_json('/api/vaults/{}/'.format(vault_id), http_method='PUT', data=json.dumps(vault_data))

    def set_card(self, card_id, card_data):
        """
        Send card contents to existing card ID

        :param card_id: Card unique ID given by list_cards
        :param card_data: Python dict with new contents
        """
        current_card_data = self.fetch_json('/api/cards/{}'.format(card_id))
        if card_data.get('name', None) == None: card_data['name'] = current_card_data['name']
        if card_data.get('description', None) == None: card_data['description'] = current_card_data['description']
        card_data['vault'] = current_card_data['vault']
        self.fetch_json('/api/cards/{}/'.format(card_id), http_method='PUT', data=json.dumps(card_data))

    def set_secret(self, secret, file=None):
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
        if file:
            self.upload_file(secret.id, workspace_key, file)

    def add_workspace(self, ws_name, ws_description=None):
        """
        Create new workspace

        :param ws_name: workspace name
        :param ws_description: workspace description (optional)
        """
        data = { 'name': ws_name }
        if ws_description: data['description'] = ws_description
        # Create new workspace
        json_obj = self.fetch_json('/api/workspaces/', http_method='POST', data=json.dumps(data))
        workspace_id = json_obj['membership']['id']
        # Set a new key for the new workspace
        data = {
                'id': workspace_id,
                'workspace_key': Cypher(self.key).gen_workspace_key()
               }
        self.fetch_json('/api/workspace_keys/{}/'.format(workspace_id), http_method='PUT', data=json.dumps(data))

    def add_vault(self, ws_id, v_name, v_description=None, v_color=None):
        """
        Create new vault

        :param ws_id: workspace id
        :param v_name: vault name
        :param v_description: vault description (optional)
        :param v_color: vault color (optional)
        """
        data = {
                'workspace': ws_id,
                'name': v_name
               }
        if v_description: data['description'] = v_description
        if v_color: data['color'] = v_color
        self.fetch_json('/api/vaults/', http_method='POST', data=json.dumps(data))

    def add_card(self, v_id, c_name, c_description=None):
        """
        Create new card

        :param v_id: vault id
        :param c_name: card name
        :param c_description: card description (optional)
        """
        data = {
                'vault': v_id,
                'name': c_name
               }
        if c_description: data['description'] = c_description
        self.fetch_json('/api/cards/', http_method='POST', data=json.dumps(data))

    def add_secret(self, card_id, secret_name, json_obj, type='password', file=None):
        """
        Create new secret

        :param card_id: card id
        :param secret_name: secret name
        :param json_obj: json object with secret contents
        :param type: type of secret (note, password or file)
        """
        types = {'note':100, 'password': 200, 'file': 300}
        vault_id = self.fetch_json('/api/cards/{}'.format(card_id))['vault']
        workspace_id = self.fetch_json('/api/vaults/{}'.format(vault_id))['workspace']
        workspace_key = self.fetch_json('/api/workspaces/{}'.format(workspace_id))['membership']['workspace_key']
        encrypted_data = Cypher(self.key).encrypt(workspace_key, json.dumps(json_obj))
        data = {
                'card': card_id,
                'type': types[type],
                'name': secret_name,
                'data': encrypted_data
               }
        new_secret = self.fetch_json('/api/secrets/', http_method='POST', data=json.dumps(data))
        if type == 'file' and file:
            self.upload_file(new_secret['id'], workspace_key, file)

    def delete_secret(self, secret_id):
        """
        Delete a Secret

        :param secret_id: Secret unique ID given by list_secrets
        """
        self.fetch_json('/api/secrets/{}/'.format(secret_id), http_method='DELETE')

    def delete_card(self, card_id):
        """
        Delete a card

        :param card_id: card unique ID given by list_cards
        """
        self.fetch_json('/api/cards/{}/'.format(card_id), http_method='DELETE')

    def delete_vault(self, vault_id):
        """
        Delete a vault

        :param vault_id: vault unique ID given by list_vaults
        """
        self.fetch_json('/api/vaults/{}/'.format(vault_id), http_method='DELETE')

    def delete_workspace(self, workspace_id):
        """
        Delete a workspace

        :param workspace_id: workspace unique ID given by list_workspaces
        """
        self.fetch_json('/api/workspaces/{}/'.format(workspace_id), http_method='DELETE')

    def upload_file(self, secret_id, workspace_key, file):
        with file as f:
            filedata = {'filedata': str(f.read(), "iso-8859-1")}
            filemeta = {'filename': basename(f.name), 'filesize': f.tell()}
            filemeta['filetype'] = MimeTypes().guess_type(f.name)[0] if MimeTypes().guess_type(f.name)[0] else ''
        encrypted_filedata = Cypher(self.key).encrypt(workspace_key, json.dumps(filedata))
        encrypted_filemeta = Cypher(self.key).encrypt(workspace_key, json.dumps(filemeta))
        files = {'blob_data': ('blob', encrypted_filedata, 'application/octet-stream'), 'blob_meta': (None, encrypted_filemeta)}
        self.fetch_json('/api/secret_blobs/{}/'.format(secret_id), http_method='PUT', headers={}, files=files)

    def fetch_json(self, uri_path, http_method='GET', headers={}, params={}, data=None, files=None, verify=False):
        """Fetch JSON from API"""
        if verify != True:
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
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
        if response.status_code not in {200, 201, 204, 206}:
            raise ResourceUnavailable('{0} at {1}'.format(response.text, url), response)

        if response.status_code == 204:
            return {}
        else:
            return response.json()

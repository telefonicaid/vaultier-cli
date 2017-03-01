#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrián López Tejedor <adrianlzt@gmail.com>
#                  Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

from vaultcli.auth import Auth
from vaultcli.client import Client
from vaultcli.config import Config
from vaultcli.secret import Secret
from vaultcli.views import print_tree, print_workspaces, print_vaults, print_cards, print_secrets, print_secret
from vaultcli.helpers import query_yes_no

import argparse
import json
import os
import sys

def get_config_file(args):
    if args.config:
        return args.config
    else:
        config_files = [
                os.path.join(os.path.expanduser('~'), '.config/vaultcli/vaultcli.conf'),
                os.path.join(os.path.expanduser('~'), '.vaultcli.conf')
                ]
        config_file = [file for file in config_files if os.access(file, os.R_OK)]
        if config_file == []:
            # No config file found, promt to generate default one
            if query_yes_no('No config file found. You want create new one?'):
                try:
                    os.makedirs(os.path.join(os.path.expanduser('~'), '.config/vaultcli'), exist_ok=True)
                except Exception as e:
                    err = 'vaultcli cannot create path to new config file.\n{0}'.format(e)
                    raise SystemExit(err)
                config_file = os.path.join(os.path.expanduser('~'), '.config/vaultcli/vaultcli.conf')
                config = Config(config_file)
                config.set_default('email', 'user@example.com')
                config.set_default('server', 'https://example.com')
                config.set_default('key','vaultier.key')
                msg = 'New config file created in \'{}\'.\nPlease edit it and set your custom parameters.'.format(config_file)
                raise SystemExit(msg)
            else:
                raise SystemExit()
        else:
            return config_file[0]

def config(args):
    # Get config in object
    config = Config(get_config_file(args))

    if '.' in args.option:
        try:
            section, option = args.option.split('.')
        except ValueError as e:
            err = 'You can only specify an \'option\' or \'section.option\'.\n{0}'.format(e)
            raise SystemExit(err)
    else:
        section = 'DEFAULT'
        option = args.option

    if args.value:
        config.set(section, option, args.value)
    else:
        err = config.get(section, option) if config.get(section, option) else '{0} is not defined in config'.format(args.option)
        raise SystemExit(err)

def write_binary_file(file_name, file_contents):
    try:
        with open(file_name, 'wb') as file:
            file.write(file_contents)
    except Exception as e:
        err = 'vaultcli cannot write file.\n{0}'.format(e)
        raise SystemExit(err)

def write_json_file(file_name, file_contents):
    try:
        with open(file_name, 'w') as file:
            json.dump(file_contents, file)
    except Exception as e:
        err = 'vaultcli cannot write file.\n{0}'.format(e)
        raise SystemExit(err)

def configure_client(args):
    # Get config in object
    config_file = get_config_file(args)
    config = Config(config_file)

    # Get config vaules from config file
    email = config.get_default('email')
    server = config.get_default('server')
    key = config.get_default('key')

    # Check if main values have data
    if not email or not server or not key:
        err = 'Your config file \'{}\' is invalid, please check it.'.format(config_file)
        raise SystemExit(err)

    try:
        key = open(key, "r").read()
    except Exception as e:
        err = 'vaultcli have a problem reading your keyfile.\n{0}'.format(e)
        raise SystemExit(err)

    token = Auth(server, email, key).get_token()
    return Client(server, token, key)

def import_workspace(args):
    try:
        with args.file as file:
            data = json.load(file)
    except Exception as e:
        err = 'vaultcli cannot read json file.\n{0}'.format(e)
        raise SystemExit(err)
    if 'name' in data:
        client = configure_client(args)
        if args.use_ids:
            if 'id' in data:
                workspace_data = {
                        'id': data['id'],
                        'name': data['name'],
                        'description': data.get('description')
                                 }
                try:
                    client.set_workspace(data['id'], workspace_data)
                except Exception as e:
                    raise SystemExit(e)
            else:
                err = 'Cannot use workspace ID because not provided in file'
                raise SystemExit(err)
        else:
            try:
                new_workspace = client.add_workspace(data['name'], data.get('description'))
            except Exception as e:
                raise SystemExit(e)
        if 'vaults' in data:
            if isinstance(data['vaults'], list):
                for vault in data['vaults']:
                    if 'name' in vault:
                        if args.use_ids:
                            if 'id' in vault:
                                vault_data = {
                                        'id': vault['id'],
                                        'name': vault['name'],
                                        'description': vault.get('description'),
                                        'color': vault.get('color')
                                             }
                                try:
                                    client.set_vault(vault['id'], vault_data)
                                except Exception as e:
                                    raise SystemExit(e)
                            else:
                                err = 'Cannot use vault ID because not provided in file'
                                raise SystemExit(err)
                        else:
                            try:
                                new_vault = client.add_vault(new_workspace['workspace']['id'], vault['name'], vault.get('description'), vault.get('color'))
                            except Exception as e:
                                raise SystemExit(e)
                        if 'cards' in vault:
                            if isinstance(vault['cards'], list):
                                for card in vault['cards']:
                                    if 'name' in card:
                                        if args.use_ids:
                                            if 'id' in card:
                                                card_data = {
                                                        'id': card['id'],
                                                        'name': card['name'],
                                                        'description': card.get('description')
                                                            }
                                                client.set_card(card['id'], card_data)
                                            else:
                                                err = 'Cannot use card ID because not provided in file'
                                                raise SystemExit(err)
                                        else:
                                            try:
                                                new_card = client.add_card(new_vault['id'], card['name'], card.get('description'))
                                            except Exception as e:
                                                raise SystemExit(e)
                                        if 'secrets' in card:
                                            if isinstance(card['secrets'], list):
                                                for secret in card['secrets']:
                                                    if ('type' and 'name') in secret:
                                                        if 'data' in secret:
                                                            # Complete missing data
                                                            if secret['type'] == 100:
                                                                secret_data = {'note': secret['data'].get('note', '')}
                                                            else:
                                                                secret_data = {
                                                                        'url': secret['data'].get('url', ''),
                                                                        'username': secret['data'].get('username', ''),
                                                                        'password': secret['data'].get('password', ''),
                                                                        'note': secret['data'].get('note', '')
                                                                              }
                                                            secret['data'] = secret_data
                                                        else:
                                                            secret['data'] = {}
                                                        if secret['type'] == 300 and 'blob_meta' in secret and secret['blob_meta'].get('filename') != None:
                                                            # Secret has an attached file, try to open it
                                                            attachments_directory = os.path.dirname(os.path.realpath(args.file.name))
                                                            attached_file_name = str(secret['blob_meta'].get('filename'))
                                                            attached_file_path = os.path.join(attachments_directory, str(secret['id']), attached_file_name)
                                                            try:
                                                                attached_file = open(attached_file_path, 'rb')
                                                            except Exception as e:
                                                                print('WARNING: ignoring \'{}\' because cannot attach data, {}'.format(secret['name'], e), file=sys.stderr)
                                                                attached_file = ''
                                                        else:
                                                            attached_file = None
                                                        # Secret blob_meta is now unnecesary at this point cause is generated from attached_file
                                                        secret['blob_meta'] = {}
                                                        secret['card'] = card['id']
                                                        if args.use_ids:
                                                            if 'id' in secret:
                                                                secret_obj = Secret.from_json(secret)
                                                                if attached_file != '':
                                                                    try:
                                                                        client.set_secret(secret_obj, attached_file)
                                                                    except Exception as e:
                                                                        raise SystemExit(e)
                                                            else:
                                                                err = 'Cannot use secret ID because not provided in file'
                                                                raise SystemExit(err)
                                                        else:
                                                            if attached_file != '':
                                                                types = {100: 'note', 200: 'password', 300: 'file'}
                                                                try:
                                                                    client.add_secret(new_card['id'], secret['name'], secret['data'], types[secret['type']], attached_file)
                                                                except Exception as e:
                                                                    raise SystemExit(e)
                                                    else:
                                                        err = 'Seems that provided file has not correct format in one secret'
                                                        raise SystemExit(err)
                                            else:
                                                err = 'Seems that provided file has not correct format in secrets'
                                                raise SystemExit(err)
                                    else:
                                        err = 'Seems that provided file has not correct format in one card'
                                        raise SystemExit(err)
                            else:
                                err = 'Seems that provided file has not correct format in cards'
                                raise SystemExit(err)
                    else:
                        err = 'Seems that provided file has not correct format in one vault'
                        raise SystemExit(err)
            else:
                err = 'Seems that provided file has not correct format in vaults'
                raise SystemExit(err)
    else:
        err = 'Seems that provided file has not correct format'
        raise SystemExit(err)

def export_workspace(args):
    client = configure_client(args)
    try:
        workspace = client.get_workspace(args.id)
    except Exception as e:
        raise SystemExit(e)
    directory = os.path.abspath(args.directory)
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            raise SystemExit(e)
    workspace_data = {
            'id': workspace.id,
            'name': workspace.name,
            'description': workspace.description,
            'vaults': []
                     }
    vaults = client.list_vaults(args.id)
    for vault in vaults:
        vault_data = {
                'id': vault.id,
                'name': vault.name,
                'description': vault.description,
                'color': vault.color,
                'cards': []
                     }
        cards = client.list_cards(vault.id)
        for card in cards:
            card_data = {
                    'id': card.id,
                    'name': card.name,
                    'description': card.description,
                    'secrets': []
                        }
            secrets = client.list_secrets(card.id)
            for secret in secrets:
                secret = client.decrypt_secret(secret, workspace.workspaceKey)
                secret_data = {
                        'id': secret.id,
                        'name': secret.name,
                        'type': secret.type
                              }
                if secret.data: secret_data['data'] = secret.data
                if secret.blobMeta:
                    secret_data['blob_meta'] = secret.blobMeta
                    secret_file = client.get_file(secret.id)
                    if secret_file != [None, None]:
                        os.makedirs(os.path.join(directory, str(secret.id)), exist_ok=True)
                        file_name = os.path.join(directory, str(secret.id), secret_file[0])
                        write_binary_file(file_name, secret_file[1])
                card_data['secrets'].append(secret_data)
            vault_data['cards'].append(card_data)
        workspace_data['vaults'].append(vault_data)
    json_file = os.path.join(directory, '{}.json'.format(workspace.name))
    write_json_file(json_file, workspace_data)

def tree_workspace(args):
    client = configure_client(args)
    vault_list = []
    try:
        workspace_name = client.get_workspace(args.id).name
    except Exception as e:
        raise SystemExit(e)
    vaults = client.list_vaults(args.id)
    for vault in vaults:
        card_list = []
        cards = client.list_cards(vault.id)
        for card in cards:
            secret_list = []
            secrets = client.list_secrets(card.id)
            for secret in secrets:
                secret_list.append('{}: {}'.format(secret.name, secret.id))
            card_list.append(['{}: {}'.format(card.name, card.id), secret_list])
        vault_list.append(['{}: {}'.format(vault.name, vault.id), card_list])
    print_tree([workspace_name, vault_list])

def list_workspaces(args):
    client = configure_client(args)
    print_workspaces(client.list_workspaces())

def list_vaults(args):
    client = configure_client(args)
    print_vaults(client.list_vaults(args.id))

def list_cards(args):
    client = configure_client(args)
    print_cards(client.list_cards(args.id))

def list_secrets(args):
    client = configure_client(args)
    print_secrets(client.list_secrets(args.id))

def show_secret(args):
    client = configure_client(args)
    try:
        secret = client.get_secret(args.id)
    except Exception as e:
        raise SystemExit(e)
    if (
            args.url or args.username or args.password or args.note or
            args.name or args.file_name or args.file_size or args.type
       ):
        if args.url or args.username or args.password or args.note:
            if secret.data:
                if args.url: print(secret.data.get('url', 'no data'))
                if args.username: print(secret.data.get('username', 'no data'))
                if args.password: print(secret.data.get('password', 'no data'))
                if args.note: print(secret.data.get('note', 'no data'))
            else:
                print('Empty secret')
        if args.name: print(secret.name)
        if args.file_name or args.file_size:
            if secret.blobMeta:
                if args.file_name: print(secret.blobMeta.get('filename', 'no data'))
                if args.file_size: print(secret.blobMeta.get('filesize', 'no data'))
            else:
                print('No file')
        if args.type: print(secret.type)
    else:
        print_secret(secret)

def get_file(args):
    client = configure_client(args)
    try:
        file = client.get_file(args.id)
    except Exception as e:
        raise SystemExit(e)
    if file == [None, None]:
        msg = 'No file'
        raise SystemExit(msg)
    else:
        if args.output:
            file_name = os.path.abspath(args.output)
            if os.path.isdir(file_name): file_name = os.path.join(file_name, file[0])
            write_binary_file(file_name, file[1])
        else:
            if query_yes_no('Do you want store \'{}\' in current directory?'.format(file[0])):
                write_binary_file(file[0], file[1])
            else:
                msg = 'Nothing to do'
                raise SystemExit(msg)

def edit_workspace(args):
    if args.name == None and args.description == None:
        err = 'No action requested'
        raise SystemExit(err)
    client = configure_client(args)
    workspace_data = {
            'id': args.id,
            'name': args.name,
            'description': args.description
                }
    try:
        client.set_workspace(args.id, workspace_data)
    except Exception as e:
        raise SystemExit(e)

def edit_vault(args):
    if args.name == None and args.description == None and args.color == None:
        err = 'No action requested'
        raise SystemExit(err)
    client = configure_client(args)
    vault_data = {
            'id': args.id,
            'name': args.name,
            'description': args.description,
            'color': args.color
                 }
    try:
        client.set_vault(args.id, vault_data)
    except Exception as e:
        raise SystemExit(e)

def edit_card(args):
    if args.name == None and args.description == None:
        err = 'No action requested'
        raise SystemExit(err)
    client = configure_client(args)
    card_data = {
            'id': args.id,
            'name': args.name,
            'description': args.description
                }
    try:
        client.set_card(args.id, card_data)
    except Exception as e:
        raise SystemExit(e)

def edit_secret(args):
    if all(arg == None for arg in (args.url, args.username, args.password, args.note, args.file, args.name)):
        err = 'No action requested'
        raise SystemExit(err)
    client = configure_client(args)
    try:
        secret = client.get_secret(args.id)
    except Exception as e:
        raise SystemExit(e)
    if (args.url != None or args.username != None or args.password != None or args.file != None) and secret.type == 100:
        err = 'Sorry, but secret notes cannot handle URLs, usernames, passwords or files.'
        raise SystemExit(err)
    if args.file != None and secret.type == 200:
        err = 'Sorry, but secret passwords cannot handle files.'
        raise SystemExit(err)
    else:
        if not secret.data:
            secret.data = {}
        if args.url != None: secret.data['url'] = args.url
        if args.username != None: secret.data['username'] = args.username
        if args.password != None: secret.data['password'] = args.password
        if args.note != None: secret.data['note'] = args.note
        if args.name != None: secret.name = args.name
        try:
            client.set_secret(secret, args.file)
        except Exception as e:
            raise SystemExit(e)

def add_workspace(args):
    client = configure_client(args)
    try:
        client.add_workspace(args.name, args.description)
    except Exception as e:
        raise SystemExit(e)

def add_vault(args):
    client = configure_client(args)
    try:
        client.add_vault(args.id, args.name, args.description, args.color)
    except Exception as e:
        raise SystemExit(e)

def add_card(args):
    client = configure_client(args)
    try:
        client.add_card(args.id, args.name, args.description)
    except Exception as e:
        raise SystemExit(e)

def add_secret_note(args):
    client = configure_client(args)
    json_obj = {'note': args.note}
    try:
        client.add_secret(args.id, args.name, json_obj, 'note')
    except Exception as e:
        raise SystemExit(e)

def add_secret_password(args):
    client = configure_client(args)
    json_obj = {
            'password': args.password,
            'url': args.url,
            'username': args.username,
            'note': args.note
               }
    try:
        client.add_secret(args.id, args.name, json_obj, 'password')
    except Exception as e:
        raise SystemExit(e)

def add_secret_file(args):
    client = configure_client(args)
    json_obj = {
            'password': args.password,
            'url': args.url,
            'username': args.username,
            'note': args.note
               }
    try:
        client.add_secret(args.id, args.name, json_obj, 'file', args.file)
    except Exception as e:
        raise SystemExit(e)

def delete_secret(args):
    client = configure_client(args)
    try:
        client.delete_secret(args.id)
    except Exception as e:
        raise SystemExit(e)

def delete_card(args):
    client = configure_client(args)
    try:
        client.delete_card(args.id)
    except Exception as e:
        raise SystemExit(e)

def delete_vault(args):
    client = configure_client(args)
    try:
        client.delete_vault(args.id)
    except Exception as e:
        raise SystemExit(e)

def delete_workspace(args):
    client = configure_client(args)
    try:
        client.delete_workspace(args.id)
    except Exception as e:
        raise SystemExit(e)

def main():
    """Create an arparse and subparse to manage commands"""
    parser = argparse.ArgumentParser(description='Manage your Vaultier secrets from cli.')
    parser.add_argument('-c', '--config', metavar='file', help='custom configuration file')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    """Add all options for config command"""
    parser_config = subparsers.add_parser('config', help='Configure vaultcli')
    parser_config.add_argument('option', metavar='option', help='option name')
    parser_config.add_argument('value', metavar='value', nargs='?', help='option value')
    parser_config.set_defaults(func=config)

    """Add all options for tree command"""
    parser_tree_workspace = subparsers.add_parser('tree-workspace', help='List workspace as tree')
    parser_tree_workspace.add_argument('id', metavar='id', help='workspace id')
    parser_tree_workspace.set_defaults(func=tree_workspace)

    """Add all options for export command"""
    parser_export_workspace = subparsers.add_parser('export-workspace', help='Export all contents of a workspace')
    parser_export_workspace.add_argument('id', metavar='id', help='workspace id')
    parser_export_workspace.add_argument('directory', metavar='directory' , help='output directory (will be created if not exists)')
    parser_export_workspace.set_defaults(func=export_workspace)

    """Add all options for import command"""
    parser_import_workspace = subparsers.add_parser('import-workspace', help='Import a workspace from a JSON file')
    parser_import_workspace.add_argument('file', metavar='file', type=argparse.FileType('r'), help='file itself')
    parser_import_workspace.add_argument('-i', '--use-ids', action='store_true', help='try to use IDs to modify existing data')
    parser_import_workspace.set_defaults(func=import_workspace)

    """Add all options for list workspaces command"""
    parser_list_workspaces = subparsers.add_parser('list-workspaces', help='List Vaultier workspaces')
    parser_list_workspaces.set_defaults(func=list_workspaces)

    """Add all options for list vaults command"""
    parser_list_vaults = subparsers.add_parser('list-vaults', help='List vaults from a workspace')
    parser_list_vaults.add_argument('id', metavar='id', help='workspace id')
    parser_list_vaults.set_defaults(func=list_vaults)

    """Add all options for list cards command"""
    parser_list_cards = subparsers.add_parser('list-cards', help='List cards from a vault')
    parser_list_cards.add_argument('id', metavar='id', help='vault id')
    parser_list_cards.set_defaults(func=list_cards)

    """Add all options for list secrets command"""
    parser_list_secrets = subparsers.add_parser('list-secrets', help='List secrets from a card')
    parser_list_secrets.add_argument('id', metavar='id', help='card id')
    parser_list_secrets.set_defaults(func=list_secrets)

    """Add all options for get secret command"""
    parser_show_secret = subparsers.add_parser('show-secret', help='Show secret contents')
    parser_show_secret.add_argument('id', metavar='id', help='secret id')
    parser_show_secret.add_argument('-l', '--url', action='store_true', help='show url')
    parser_show_secret.add_argument('-u', '--username', action='store_true', help='show username')
    parser_show_secret.add_argument('-p', '--password', action='store_true', help='show password')
    parser_show_secret.add_argument('-n', '--note', action='store_true', help='show note')
    parser_show_secret.add_argument('--name', action='store_true', help='show name')
    parser_show_secret.add_argument('--file-name', action='store_true', help='show file name')
    parser_show_secret.add_argument('--file-size', action='store_true', help='show file size')
    parser_show_secret.add_argument('--type', action='store_true', help='show type (numeric)')
    parser_show_secret.set_defaults(func=show_secret)

    """Add all options for get file command"""
    parser_get_file = subparsers.add_parser('get-file', help='Get binary file from a secret')
    parser_get_file.add_argument('id', metavar='id', help='secret id')
    parser_get_file.add_argument('-o', '--output', metavar='file' , help='output file (path must exists)')
    parser_get_file.set_defaults(func=get_file)

    """Add all options for edit workspace command"""
    parser_edit_workspace = subparsers.add_parser('edit-workspace', help='Edit workspace name or description')
    parser_edit_workspace.add_argument('id', metavar='id', help='workspace id')
    parser_edit_workspace.add_argument('-n', '--name', metavar='name', help='workspace name')
    parser_edit_workspace.add_argument('-d', '--description', metavar='description', help='workspace description')
    parser_edit_workspace.set_defaults(func=edit_workspace)

    """Add all options for edit vault command"""
    parser_edit_vault = subparsers.add_parser('edit-vault', help='Edit vault name, description or color')
    parser_edit_vault.add_argument('id', metavar='id', help='vault id')
    parser_edit_vault.add_argument('-n', '--name', metavar='name', help='vault name')
    parser_edit_vault.add_argument('-d', '--description', metavar='description', help='vault description')
    parser_edit_vault.add_argument('--color', choices=['blue', 'orange', 'purple', 'green', 'red'], help='vault color')
    parser_edit_vault.set_defaults(func=edit_vault)

    """Add all options for edit card command"""
    parser_edit_card = subparsers.add_parser('edit-card', help='Edit card name or description')
    parser_edit_card.add_argument('id', metavar='id', help='card id')
    parser_edit_card.add_argument('-n', '--name', metavar='name', help='card name')
    parser_edit_card.add_argument('-d', '--description', metavar='description', help='card description')
    parser_edit_card.set_defaults(func=edit_card)

    """Add all options for edit secret command"""
    parser_edit_secret = subparsers.add_parser('edit-secret', help='Edit secret contents')
    parser_edit_secret.add_argument('id', metavar='id', help='secret id')
    parser_edit_secret.add_argument('-l', '--url', metavar='url', help='edit url')
    parser_edit_secret.add_argument('-u', '--username', metavar='username', help='edit username')
    parser_edit_secret.add_argument('-p', '--password', metavar='password', help='edit password')
    parser_edit_secret.add_argument('-n', '--note', metavar='note', help='edit note')
    parser_edit_secret.add_argument('-f', '--file', metavar='file', type=argparse.FileType('rb'), help='change file')
    parser_edit_secret.add_argument('--name', metavar='name', help='edit name')
    parser_edit_secret.set_defaults(func=edit_secret)

    """Add all options for add workspace command"""
    parser_add_workspace = subparsers.add_parser('add-workspace', help='Add new Vaultier workspace')
    parser_add_workspace.add_argument('name', metavar='name', help='workspace name')
    parser_add_workspace.add_argument('-d', '--description', metavar='description', help='workspace description')
    parser_add_workspace.set_defaults(func=add_workspace)

    """Add all options for add vault command"""
    parser_add_vault = subparsers.add_parser('add-vault', help='Add new vault to a workspace')
    parser_add_vault.add_argument('id', metavar='id', help='workspace id')
    parser_add_vault.add_argument('name', metavar='name', help='vault name')
    parser_add_vault.add_argument('-d', '--description', metavar='description', help='vault description')
    parser_add_vault.add_argument('--color', choices=['blue', 'orange', 'purple', 'green', 'red'], help='vault color (default blue)')
    parser_add_vault.set_defaults(func=add_vault)

    """Add all options for add card command"""
    parser_add_card = subparsers.add_parser('add-card', help='Add new card to a vault')
    parser_add_card.add_argument('id', metavar='id', help='vault id')
    parser_add_card.add_argument('name', metavar='name', help='card name')
    parser_add_card.add_argument('-d', '--description', metavar='description', help='card description')
    parser_add_card.set_defaults(func=add_card)

    """Add all options for add secret command"""
    parser_add_secret = subparsers.add_parser('add-secret', help='Add new secret to a card')
    add_secret_subparsers = parser_add_secret.add_subparsers(dest='command')
    add_secret_subparsers.required = True

    """Add all options for add secret note command"""
    parser_add_secret_note = add_secret_subparsers.add_parser('note', help='Add new secret note')
    parser_add_secret_note.add_argument('id', metavar='id', help='card id')
    parser_add_secret_note.add_argument('name', metavar='name', help='name of secret note')
    parser_add_secret_note.add_argument('note', metavar='note', help='note contents')
    parser_add_secret_note.set_defaults(func=add_secret_note)

    """Add all options for add secret password command"""
    parser_add_secret_password = add_secret_subparsers.add_parser('password', help='Add new secret password')
    parser_add_secret_password.add_argument('id', metavar='id', help='card id')
    parser_add_secret_password.add_argument('name', metavar='name', help='name of secret password')
    parser_add_secret_password.add_argument('password', metavar='password', help='password itself')
    parser_add_secret_password.add_argument('-l', '--url', metavar='url', help='optional url')
    parser_add_secret_password.add_argument('-u', '--username', metavar='username', help='optional username')
    parser_add_secret_password.add_argument('-n', '--note', metavar='note', help='optional note')
    parser_add_secret_password.set_defaults(func=add_secret_password)

    """Add all options for add secret file command"""
    parser_add_secret_file = add_secret_subparsers.add_parser('file', help='Add new secret file')
    parser_add_secret_file.add_argument('id', metavar='id', help='card id')
    parser_add_secret_file.add_argument('name', metavar='name', help='name of secret file')
    parser_add_secret_file.add_argument('file', metavar='file', type=argparse.FileType('rb'), help='file itself')
    parser_add_secret_file.add_argument('-l', '--url', metavar='url', help='optional url')
    parser_add_secret_file.add_argument('-u', '--username', metavar='username', help='optional username')
    parser_add_secret_file.add_argument('-p', '--password', metavar='password', help='optional password')
    parser_add_secret_file.add_argument('-n', '--note', metavar='note', help='optional note')
    parser_add_secret_file.set_defaults(func=add_secret_file)

    """Add all options for delete secret command"""
    parser_delete_secret = subparsers.add_parser('delete-secret', help='Delete a secret')
    parser_delete_secret.add_argument('id', metavar='id', help='secret id')
    parser_delete_secret.set_defaults(func=delete_secret)

    """Add all options for delete card command"""
    parser_delete_card = subparsers.add_parser('delete-card', help='Delete a card')
    parser_delete_card.add_argument('id', metavar='id', help='card id')
    parser_delete_card.set_defaults(func=delete_card)

    """Add all options for delete vault command"""
    parser_delete_vault = subparsers.add_parser('delete-vault', help='Delete a vault')
    parser_delete_vault.add_argument('id', metavar='id', help='vault id')
    parser_delete_vault.set_defaults(func=delete_vault)

    """Add all options for delete workspace command"""
    parser_delete_workspace = subparsers.add_parser('delete-workspace', help='Delete a workspace')
    parser_delete_workspace.add_argument('id', metavar='id', help='workspace id')
    parser_delete_workspace.set_defaults(func=delete_workspace)

    """Parse command arguments"""
    args = parser.parse_args()

    args.func(args)

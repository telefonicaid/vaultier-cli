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
from vaultcli.views import print_tree, print_workspaces, print_vaults, print_cards, print_secrets, print_secret
from vaultcli.helpers import query_yes_no

import argparse
import os

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

def tree_workspace(args):
    client = configure_client(args)
    vault_list = []
    workspace_name = client.get_workspace_name(args.id)
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

def get_secret(args):
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
    if not file:
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

def edit_secret(args):
    if not (args.url or args.username or args.password or args.note or args.name):
        err = 'No action requested'
        raise SystemExit(err)
    client = configure_client(args)
    try:
        secret = client.get_secret(args.id)
    except Exception as e:
        raise SystemExit(e)
    if (args.url or args.username or args.password) and secret.type == 100:
        err = 'Sorry, but secret notes cannot handle URLs, usernames or passwords.'
        raise SystemExit(err)
    else:
        if not secret.data:
            secret.data = {}
        if args.url: secret.data['url'] = args.url
        if args.username: secret.data['username'] = args.username
        if args.password: secret.data['password'] = args.password
        if args.note: secret.data['note'] = args.note
        if args.name: secret.name = args.name
        try:
            client.set_secret(secret)
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
    parser_get_secret = subparsers.add_parser('get-secret', help='Get secret contents')
    parser_get_secret.add_argument('id', metavar='id', help='secret id')
    parser_get_secret.add_argument('-l', '--url', action='store_true', help='get url')
    parser_get_secret.add_argument('-u', '--username', action='store_true', help='get username')
    parser_get_secret.add_argument('-p', '--password', action='store_true', help='get password')
    parser_get_secret.add_argument('-n', '--note', action='store_true', help='get note')
    parser_get_secret.add_argument('--name', action='store_true', help='get name')
    parser_get_secret.add_argument('--file-name', action='store_true', help='get file name')
    parser_get_secret.add_argument('--file-size', action='store_true', help='get file size')
    parser_get_secret.add_argument('--type', action='store_true', help='get type (numeric)')
    parser_get_secret.set_defaults(func=get_secret)

    """Add all options for get file command"""
    parser_get_file = subparsers.add_parser('get-file', help='Get binary file from a secret')
    parser_get_file.add_argument('id', metavar='id', help='secret id')
    parser_get_file.add_argument('-o', '--output', metavar='file' , help='output file (path must exists)')
    parser_get_file.set_defaults(func=get_file)

    """Add all options for edit secret command"""
    parser_edit_secret = subparsers.add_parser('edit-secret', help='Edit secret contents')
    parser_edit_secret.add_argument('id', metavar='id', help='secret id')
    parser_edit_secret.add_argument('-l', '--url', metavar='url', help='edit url')
    parser_edit_secret.add_argument('-u', '--username', metavar='username', help='edit username')
    parser_edit_secret.add_argument('-p', '--password', metavar='password', help='edit password')
    parser_edit_secret.add_argument('-n', '--note', metavar='note', help='edit note')
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

    """Parse command arguments"""
    args = parser.parse_args()

    args.func(args)

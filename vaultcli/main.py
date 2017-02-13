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
from vaultcli.views import print_workspaces, print_vaults, print_cards, print_secrets, print_secret

import argparse

config_file = 'vaultcli.conf' # TODO: Seek for config file in different locations

def config(args):
    # Get config in object
    config = Config(config_file)

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

def configure_client():
    # Get config in object
    config = Config(config_file)

    # Get config vaules from config file
    email = config.get_default('email')
    server = config.get_default('server')
    priv_key = config.get_default('priv_key')
    pub_key = config.get_default('pub_key') # TODO: Gen pub key from private key

    token = Auth(server, email, priv_key, pub_key).get_token()
    return Client(server, token, priv_key, pub_key)

def list_workspaces(args):
    client = configure_client()
    print_workspaces(client.list_workspaces())

def list_vaults(args):
    client = configure_client()
    print_vaults(client.list_vaults(args.id))

def list_cards(args):
    client = configure_client()
    print_cards(client.list_cards(args.id))

def list_secrets(args):
    client = configure_client()
    print_secrets(client.list_secrets(args.id))

def get_secret(args):
    client = configure_client()
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

def main():
    """Create an arparse and subparse to manage commands"""
    parser = argparse.ArgumentParser(description='Manage your Vaultier secrets from cli.')
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    """Add all options for config command"""
    parser_config = subparsers.add_parser('config', help='Configure vaultier-cli')
    parser_config.add_argument('option', metavar='option', help='option name')
    parser_config.add_argument('value', metavar='value', nargs='?', help='option value')
    parser_config.set_defaults(func=config)

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
    parser_get_secret = subparsers.add_parser('get-secret', help='Get secret contents from an ID')
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

    """Parse command arguments"""
    args = parser.parse_args()

    args.func(args)

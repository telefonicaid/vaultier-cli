#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrián López Tejedor <adrianlzt@gmail.com>
#                  Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

from vaultier.auth import Auth
from vaultier.client import Client
from vaultier.views import print_workspaces, print_vaults, print_cards, print_secrets, print_secret

def main():
    email = "user@example.com"
    server = "https://vaultier.example.com"
    priv_key = "vaultier.key"
    pub_key = "vaultier.key.pub" # TODO: Gen pub key from private key

    token = Auth(server, email, priv_key, pub_key).get_token()
    client = Client(server, token)

    print_workspaces (client.list_workspaces())

    print_vaults (client.list_vaults(21))

    print_cards (client.list_cards(78))

    print_secrets (client.list_secrets(395))

    print_secret (client.get_secret(858, priv_key, pub_key))
    print_secret (client.get_secret(860, priv_key, pub_key))
    print_secret (client.get_secret(862, priv_key, pub_key))

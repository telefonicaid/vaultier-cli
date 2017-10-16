#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrián López Tejedor <adrianlzt@gmail.com>
#
# Distributed under terms of the GNU GPLv3 license.

"""
Read a kdbx file and import data into a Vaultier server
"""

from pykeepass import PyKeePass
from vaultcli import main as vaultier_main
from functools import lru_cache
from tqdm import tqdm
import argparse
import sys
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)

# Ignore SSL warnings
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def remove_postfix(text, postfix):
  if text.endswith(postfix):
    return text[0:len(text)-len(postfix)]
  return text

def get_path(entry):
    """
    Given a keepass entry return the path of the parent in 'normal' order
    """
    title = entry.title if entry.title else "None"
    reversed_path = remove_postfix(entry.path, title).rstrip("/").split("/")
    reversed_path.reverse()
    path = "/".join(reversed_path)
    return path

def normalize(name):
    """
    Given a name, return the version without incompatible chars
    """
    return name.replace("/", "_")

def get_title(entry):
    """
    Given an entry return a value to use as the vaultier secret name
    """
    name = entry.title if entry.title else entry.username
    if not name:
        raise Exception("Entry without title neither username. Incompatible!")
    return normalize(name)

def flatten_dir(path):
    """
    Given a path to a keepass directory, flatten to map the top level to a vault and
    the rest to a card with names separated by dots

    Will not work if a dot already exists in the path
    """
    if "." in path:
        raise Exception("Directory with a dot in the name. Incompatible!")
    path_list = path.split("/")
    vault = path_list.pop(0)
    card = ".".join(path_list)
    return vault, card

@lru_cache(maxsize=128)
def add_vault(vault):
    """
    Create a vault in workspace if name does not exists yet
    Return the id of the vault
    """
    for v in vaultier.list_vaults(workspace):
        if v.name == vault:
            logger.debug(f"Vault {vault} already exists")
            return v.id

    desc = "Automatic import from Keepass"
    logger.debug(f"Creating vault {vault} in workspace {workspace}")
    r = vaultier.add_vault(workspace, vault, desc)
    return r['id']

@lru_cache(maxsize=128)
def add_card(vault, card):
    """
    Create a card in workspace/vault if name does not exists yet
    Param vault should be the id of the vault
    Return the id of the card
    """
    for c in vaultier.list_cards(vault):
        if c.name == card:
            logger.debug(f"Card {card} already exists")
            return c.id

    desc = "Automatic import from Keepass"
    logger.debug(f"Creating card {card} in {vault}, workspace {workspace}")
    r = vaultier.add_card(vault, card, desc)
    return r['id']

def add_secret(vault, card, name, username, password, url, notes):
    """
    Create a secret in workspace/vault/card
    If some secret already exists with the same name log an error.
    Param vault just passed to track dups
    Param card should be the id of the card
    Return the id of the secret
    """
    logger.debug(f"Creating secret {name} in card {card}, workspace {workspace}")
    data = {
            'username': username,
            'password': password,
            'url': url,
            'note': notes
    }
    r = vaultier.add_secret(card, name, data)
    return r['id']

def save_to_vaultier(vault, card, name, user, password, url, notes):
    """
    Store the entry from keepass into Vaultier server
    """
    logger.debug(f"Store: Vault: {vault}, Card: {card}, Name: {name}, User: {user}, Pass: {password}, URL: {url}, Notes: {notes}")
    vault_id = add_vault(vault)
    logger.debug(f"Vault id {vault_id}")
    card_id = add_card(vault_id, card)
    logger.debug(f"Card id {card_id}")
    secret_id = add_secret(vault_id, card_id, name, user, password, url, notes)
    logger.debug(f"Secret id {secret_id}")

# Parse arguments
p = argparse.ArgumentParser(prog="keepass_to_vault", description='Import Keepass to Vaultier')
p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
p.add_argument("-f", "--file", action="store", dest="keepass_file", required=True,
                   help="Path to the Keepass file.", default=None)
p.add_argument("-p", "--password", action="store", dest="keepass_pass", required=True,
                   help="Password to open the Keepass file.", default=None)
p.add_argument("-w", "--workspace", action="store", dest="workspace", required=True,
                   help="Name of the Vaultier Workspace where to store data.", default=None)

args = p.parse_args(sys.argv[1:])
if args.verbose > 1:
    logger.setLevel(logging.DEBUG)
elif args.verbose > 0:
    logger.setLevel(logging.INFO)

# Vaultier, using config file
class FakeConf(object):
    config = None
    insecure = True
vaultier = vaultier_main.configure_client(FakeConf())

# Get workspace id by name
workspace = None
for w in vaultier.list_workspaces():
    logger.debug(f"Workspace available: {w.name}")
    if w.name == args.workspace:
        logger.info(f"Mapped workspace {args.workspace} to id {w.id}")
        workspace = w.id
        break

if not workspace:
    raise Exception(f"Not found any workspace available with name '{args.workspace}'")


# Keepass
logger.debug(f"Opening keepass file {args.keepass_file} with password {args.keepass_pass}")
kp = PyKeePass(args.keepass_file, password=args.keepass_pass)

logger.info(f"Processing {len(kp.entries)} entries")
for e in tqdm(kp.entries):
    logger.debug(f"Entry {e}")
    title = get_title(e)
    path = get_path(e)
    vault, card = flatten_dir(path)
    user = e.username
    password = e.password
    url = e.url.strip() if e.url else e.url
    notes = e.notes
    if b"Binary" in e.dump_xml():
        logger.warn(f"'{path}/{title}' have a binary file attached. Should be added to Vaultier by hand")

    save_to_vaultier(vault, card, title, user, password, url, notes)

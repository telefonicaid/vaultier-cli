#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrián López Tejedor <adrianlzt@gmail.com>
#                  Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

from vaultcli.workspacecypher import WorkspaceCypher
from vaultcli.datacypher import DataCypher

class Cypher(object):
    def __init__(self, key):
        self.key = key

    def decrypt (self, workspace_key, data_encrypted):
        work_space_cypher = WorkspaceCypher(self.key)
        decrypted_workspace_key = work_space_cypher.decrypt(workspace_key)
        data_cypher = DataCypher(decrypted_workspace_key)
        return data_cypher.decrypt(data_encrypted)

#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrián López Tejedor <adrianlzt@gmail.com>
#                  Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

class Secret(object):
    """
    Class representing a Card
    """
    def __init__(self, id, type, name, data, blobMeta, card, workspaceKey=None):
        self.id = id
        self.type = type
        self.name = name
        self.data = data
        self.blobMeta = blobMeta
        self.card = card
        self.workspaceKey = workspaceKey

    def from_json(json_obj):
        secret = Secret(json_obj['id'], json_obj['type'], json_obj['name'], json_obj['data'], json_obj['blob_meta'], json_obj['card'])
        return secret

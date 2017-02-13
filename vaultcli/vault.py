#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrián López Tejedor <adrianlzt@gmail.com>
#                  Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

class Vault(object):
    """
    Class representing a Vault
    """
    def __init__(self, id, slug, name, description, color, workspace):
        self.id = id
        self.slug = slug
        self.name = name
        self.description = description
        self.color = color
        self.workspace = workspace

    def from_json(json_obj):
        vault = Vault(json_obj['id'], json_obj['slug'], json_obj['name'], json_obj['description'], json_obj['color'], json_obj['workspace'])
        return vault

#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2017 Adrián López Tejedor <adrianlzt@gmail.com>
#                  Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

class Workspace(object):
    """
    Class representing a Workspace
    """
    def __init__(self, id, slug, name, description, workspaceKey):
        self.id = id
        self.slug = slug
        self.name = name
        self.description = description
        self.workspaceKey = workspaceKey

    def from_json(json_obj):
        workspace = Workspace(json_obj['id'], json_obj['slug'], json_obj['name'], json_obj['description'], json_obj['membership']['workspace_key'])
        return workspace

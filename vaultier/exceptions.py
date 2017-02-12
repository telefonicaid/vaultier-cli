#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 Adrián López Tejedor <adrianlzt@gmail.com>
#                  Óscar García Amor <ogarcia@connectical.com>
#
# Distributed under terms of the GNU GPLv3 license.

class ResourceUnavailable(Exception):
    """Exception representing a failed request to a resource"""
    def __init__(self, msg, http_response):
        Exception.__init__(self)
        self._msg = msg
        self._status = http_response.status_code

    def __str__(self):
        return '{0} (HTTP status: {1})'.format(self._msg, self._status)

class Unauthorized(ResourceUnavailable):
    pass

class Forbidden(ResourceUnavailable):
    pass

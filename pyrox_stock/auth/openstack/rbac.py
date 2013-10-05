# Copyright (c) 2013 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR ONDITIONS OF ANY KIND, either express or
# implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Adapted from: https://github.com/racker/eom
#

import re

import simplejson as json

import pyrox.http as model
import pyrox.log as logging
import pyrox.filtering as filtering

from oslo.config import cfg

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

OPT_GROUP_NAME = 'eom:rbac'
OPTION_NAME = 'acls_file'

CONF.register_opt(cfg.StrOpt(OPTION_NAME), group=OPT_GROUP_NAME)

EMPTY_SET = set()


def _load_rules(path):
    full_path = CONF.find_file(path)
    if not full_path:
        raise cfg.ConfigFilesNotFoundError([path])

    with open(full_path) as fd:
        return json.load(fd)


def _create_acl_map(rules):
    acl_map = []
    for rule in rules:
        resource = rule['resource']
        route = re.compile(rule['route'] + '$')

        acl = rule['acl']

        if acl:
            can_read = set(acl.get('read', []))
            can_write = set(acl.get('write', []))
            can_delete = set(acl.get('delete', []))

            # Construct a lookup table
            lookup = {
                'GET': can_read,
                'HEAD': can_read,
                'OPTIONS': can_read,

                'PATCH': can_write,
                'POST': can_write,
                'PUT': can_write,

                'DELETE': can_delete,
            }
        else:
            lookup = None

        acl_map.append((resource, route, lookup))

    return acl_map


_403_FORBIDDEN = model.HttpResponse()
_403_FORBIDDEN.status = '403 Forbidden'
_403_FORBIDDEN.header('Content-Length').values.append('0')

CONF(args=[], default_config_files=['/etc/pyrox/eom/eom.conf'])


class RBACFilter(filtering.HttpFilter):

    def __init__(self):
        group = CONF[OPT_GROUP_NAME]
        rules_path = group[OPTION_NAME]
        rules = _load_rules(rules_path)
        self.acl_map = _create_acl_map(rules)

    @filtering.handles_request_head
    def on_request_head(self, request_head):
        path = request_head.url

        for resource, route, acl in self.acl_map:
            if route.match(path):
                break
        else:
            LOG.debug(_('Requested path not recognized. Skipping RBAC.'))
            return

        roles = request_head.get_header('X-Roles')

        if not roles:
            LOG.error(_('Request headers did not include X-Roles'))
            return filtering.reject(_403_FORBIDDEN)

        given_roles = set(roles.values) if roles else EMPTY_SET

        method = request_head.method
        try:
            authorized_roles = acl[method]
        except KeyError:
            LOG.error(_('HTTP method not supported: %s') % method)
            return filtering.reject(_403_FORBIDDEN)

        # The user must have one of the roles that
        # is authorized for the requested method.
        if (authorized_roles & given_roles):
            # Carry on
            return filtering.pass_event()

        logline = _('User not authorized to %(method)s '
                    'the %(resource)s resource')
        LOG.info(logline % {'method': method, 'resource': resource})
        return filtering.reject(_403_FORBIDDEN)

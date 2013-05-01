# Copyright (c) 2013, PagerDuty, Inc. <info@pagerduty.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of PagerDuty Inc nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL PAGERDUTY INC BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json
import urllib2

import logging
log = logging.getLogger("zen.pagerduty.actions")

import Globals

from zope.interface import implements, providedBy
from zenoss.protocols.protobufs.zep_pb2 import STATUS_ACKNOWLEDGED

from Products.ZenModel.UserSettings import GroupSettings
from Products.ZenUtils.guid.guid import GUIDManager
from Products.ZenUtils.ProcessQueue import ProcessQueue

from Products.ZenModel.interfaces import IAction
from Products.ZenModel.actions import IActionBase, TargetableAction, ActionExecutionException
from Products.ZenModel.actions import processTalSource, _signalToContextDict
from Products.ZenModel.ZVersion import VERSION as ZENOSS_VERSION

from ZenPacks.PagerDuty.APINotification.interfaces import IPagerDutyEventsAPIActionContentInfo
from ZenPacks.PagerDuty.APINotification.constants import EVENT_API_URI, EventType, enum
from ZenPacks.PagerDuty.APINotification import version as zenpack_version

NotificationProperties = enum(SERVICE_KEY='service_key', SUMMARY='summary', DESCRIPTION='description',
                              INCIDENT_KEY='incident_key', DETAILS='details')

REQUIRED_PROPERTIES = [NotificationProperties.SERVICE_KEY, NotificationProperties.SUMMARY,
                       NotificationProperties.DESCRIPTION, NotificationProperties.INCIDENT_KEY]

API_TIMEOUT_SECONDS = 40

class PagerDutyEventsAPIAction(IActionBase):
    """
    Derived class to contact PagerDuty's events API when a notification is
    triggered.
    """
    implements(IAction)

    id = 'pagerduty'
    name = 'PagerDuty'
    actionContentInfo = IPagerDutyEventsAPIActionContentInfo

    shouldExecuteInBatch = False

    def __init__(self):
        super(PagerDutyEventsAPIAction, self).__init__()

    def setupAction(self, dmd):
        self.guidManager = GUIDManager(dmd)
        self.dmd = dmd

    def execute(self, notification, signal):
        """
        Sets up the execution environment and POSTs to PagerDuty's Event API.
        """
        log.debug('Executing Pagerduty Events API action: %s', self.name)
        self.setupAction(notification.dmd)

        if signal.clear:
            eventType = EventType.RESOLVE
        elif signal.event.status == STATUS_ACKNOWLEDGED:
            eventType = EventType.ACKNOWLEDGE
        else:
            eventType = EventType.TRIGGER

        # Set up the TALES environment
        environ = {'dmd': notification.dmd, 'env':None}

        actor = signal.event.occurrence[0].actor

        device = None
        if actor.element_uuid:
            device = self.guidManager.getObject(actor.element_uuid)
        environ.update({'dev': device})

        component = None
        if actor.element_sub_uuid:
            component = self.guidManager.getObject(actor.element_sub_uuid)
        environ.update({'component': component})

        data = _signalToContextDict(signal, self.options.get('zopeurl'), notification, self.guidManager)
        environ.update(data)

        try:
            details_list = json.loads(notification.content['details'])
        except ValueError:
            raise ActionExecutionException('Invalid JSON string in details')

        details = dict()
        for kv in details_list:
            details[kv['key']] = kv['value']

        details['zenoss'] = {
            'version'        : ZENOSS_VERSION,
            'zenpack_version': zenpack_version()
        }
        body = {'event_type': eventType,
                'client'    : 'Zenoss',
                'client_url': '${urls/eventUrl}',
                'details'   : details}

        for prop in REQUIRED_PROPERTIES:
            if prop in notification.content:
                body[prop] = notification.content[prop]
            else:
                raise ActionExecutionException("Required property '%s' not found" % (prop))

        self._performRequest(body, environ)

    def _performRequest(self, body, environ):
        """
        Actually performs the request to PagerDuty's Event API.

        Raises:
            ActionExecutionException: Some error occurred while contacting
            PagerDuty's Event API (e.g., API down, invalid service key).
        """
        request_body = json.dumps(body)

        try:
            request_body = processTalSource(request_body, **environ)
        except Exception:
            raise ActionExecutionException('Unable to perform TALES evaluation on "%s" -- is there an unescaped $?' % request_body)

        headers = {'Content-Type' : 'application/json'}
        req = urllib2.Request(EVENT_API_URI, request_body, headers)
        try:
            f = urllib2.urlopen(req, None, API_TIMEOUT_SECONDS)
        except urllib2.URLError as e:
            if hasattr(e, 'reason'):
                msg = 'Failed to contact the PagerDuty server: %s' % (e.reason)
                raise ActionExecutionException(msg)
            elif hasattr(e, 'code'):
                msg = 'The PagerDuty server couldn\'t fulfill the request: HTTP %d (%s)' % (e.code, e.msg)
                raise ActionExecutionException(msg)
            else:
                raise ActionExecutionException('Unknown URLError occurred')

        response = f.read()
        f.close()

    def updateContent(self, content=None, data=None):
        updates = dict()

        for k in NotificationProperties.ALL:
            updates[k] = data.get(k)

        content.update(updates)

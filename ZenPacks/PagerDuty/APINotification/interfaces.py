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

"""
Actions in Zenoss define their properties through their 'actionContentInfo'
attribute. 'actionContentInfo' is a Zope interface which defines the names and
types of the properties of the action. 'actionContentInfo' is used by the
action to generate a block of JS that will render the action's content tab
in the UI (see Products.ZenModel.interfaces.IAction.generateJavascriptContent).

This module defines the Zope interface that is assigned to
actions.PagerDutyEventsAPIAction.actionContentInfo.

Other example Zope interfaces used to define action properties are:

  * Products.Zuul.interfaces.actions.IEmailActionContentInfo
  * Products.Zuul.interfaces.actions.IPageActionContentInfo
  * Products.Zuul.interfaces.actions.ICommandActionContentInfo
  * Products.Zuul.interfaces.actions.ISnmpTrapActionContentInfo
"""

import json

from Products.Zuul.interfaces import IInfo
from Products.Zuul.form import schema
from Products.Zuul.utils import ZuulMessageFactory as _t

from Products.ZenModel.ZVersion import VERSION as ZENOSS_VERSION
from Products.ZenUtils.Version import Version

import textwrap

# Make the UI look good in Zenoss 3 and Zenoss 4
if Version.parse('Zenoss %s' % ZENOSS_VERSION) >= Version.parse('Zenoss 4'):
    SingleLineText = schema.TextLine
    MultiLineText = schema.Text
else:
    SingleLineText = schema.Text
    MultiLineText = schema.TextLine

def _serialize(details):
    return [{u'key':a, u'value':b} for a,b in zip(details.keys(), details.values())] 

class IPagerDutyEventsAPIActionContentInfo(IInfo):
    """
    Zope interface defining the names and types of the properties used by
    actions.PagerDutyEventsAPIAction.

    The "implementation" of this interface is defined in
    info.PagerDutyEventsAPIActionContentInfo.
    """

    service_key = SingleLineText(
        title       = _t(u'Service API Key'),
        description = _t(u'The API Key for the PagerDuty Service you want to alert.'),
        xtype       = 'pagerduty-api-events-service-list'
    )

    summary = SingleLineText(
        title       = _t(u'Summary'),
        description = _t(u'The summary for the PagerDuty event.'),
        default     = u'${evt/summary}'
    )

    description = SingleLineText(
        title       = _t(u'Description'),
        description = _t(u'The description for the PagerDuty event.'),
        default     = u'${evt/device}: ${evt/summary}',
    )

    incident_key = SingleLineText(
        title       = _t(u'Incident Key'),
        description = _t(u'The incident key for the PagerDuty event.'),
        default     = u'${evt/evid}',
    )

    details = schema.List(
        title       = _t(u'Details'),
        description = _t(u'The incident key for the PagerDuty event.'),
        default     = [json.dumps(_serialize({
                    u'device':u'${evt/device}',
                    u'ipAddress':u'${evt/component}',
                    u'severity':u'${evt/severity}',
                    u'message':u'${evt/message}',
                    u'eventID':u'${evt/evid}',
                    }))],
        group       = _t(u'Details'),
        xtype='pagerduty-api-events-details-field')

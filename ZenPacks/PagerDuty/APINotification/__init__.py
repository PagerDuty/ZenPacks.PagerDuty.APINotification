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

import routers

import logging
log = logging.getLogger('zen.PagerDuty')

import Globals

from Products.ZenModel.ZenossSecurity import ZEN_MANAGE_DMD
from Products.ZenModel.DataRoot import DataRoot
from Products.ZenModel.UserSettings import UserSettingsManager
from Products.ZenModel.ZenossInfo import ZenossInfo
from Products.ZenModel.ZenPackManager import ZenPackManager
from Products.ZenModel.ZenPack import ZenPack as ZenPackBase
from Products.ZenUtils.Utils import monkeypatch, unused
unused(Globals)

import pkg_resources

BROWSER_PAGE = 'pd-import-services-page'
ACTION_NAME  = 'pagerduty'

# Add "PagerDuty" to left navigation on Advanced / Settings page. This
# is so ugly because the settings page is still a Zenoss 2 "back-compat"
# page.
for klass in (DataRoot, UserSettingsManager, ZenossInfo, ZenPackManager):
    action = BROWSER_PAGE
    if klass == ZenPackManager:
        action = '../%s' % action

    fti = klass.factory_type_information[0]
    fti['actions'] = fti['actions'] + ({
        'id': BROWSER_PAGE,
        'name': 'PagerDuty',
        'action': action,
        'permissions': (ZEN_MANAGE_DMD,)
    },)

@monkeypatch('Products.ZenUI3.navigation.menuitem.PrimaryNavigationMenuItem')
def update(self):
    '''
    Update subviews for this PrimaryNavigationMenuItem.

    Post-processes default behavior to add our subview. This allows the
    secondary navigation bar to be rendered properly when the user is
    looking at the PagerDuty settings screen.
    '''
    # original gets injected into locals by monkeypatch decorator.
    original(self)

    if '/zport/dmd/dataRootManage' in self.subviews:
        self.subviews.append('/zport/dmd/%s' % BROWSER_PAGE)

@monkeypatch('Products.Zuul.facades.triggersfacade.TriggersFacade')
def createNotification(self, id, action, *args, **kwargs):
    '''
    Overrides createNotification to provide reasonable defaults for PagerDuty
    notifications
    '''

    # original gets injected into locals by monkeypatch decorator.
    notification = original(self, id, action, *args, **kwargs)

    if notification.action.lower() == ACTION_NAME:
        notification.send_clear = True
        notification.repeat_seconds = 60
        notification.send_initial_occurrence = False

    return notification

def version():
    """
    Convenience function to determine the ZenPack version at runtime since
    it must be hardcoded in setup.py.
    """
    resources = pkg_resources.require(__name__)
    if not resources:
        return None

    return resources[0].version

class ZenPack(ZenPackBase):
    def remove(self, app, leaveObjects=False):
        """
        Remove PagerDuty account model on uninstall
        """
        if not leaveObjects:
            log.info('Removing PagerDuty account info')
            dmdRoot = routers._dmdRoot(app.zport.dmd)
            if hasattr(dmdRoot, routers.ACCOUNT_ATTR):
                delattr(dmdRoot, routers.ACCOUNT_ATTR)

            log.info('Removing PagerDuty notifications')
            allNotifications = app.zport.dmd.NotificationSubscriptions
            pagerDutyNotificationIDs = [allNotifications.findChild(notification).id
                                        for notification in allNotifications.keys()
                                            if allNotifications.findChild(notification).action == ACTION_NAME]

            for pdid in pagerDutyNotificationIDs:
                allNotifications.findChild(pdid).getPrimaryParent()._delObject(pdid)

        super(ZenPack, self).remove(app, leaveObjects=leaveObjects)

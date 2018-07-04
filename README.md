ZenPack.PagerDuty.APINotification
=================================

The official PagerDuty ZenPack extends Zenoss 4 and 5 by providing a new PagerDuty notification type that allows you to easily select which PagerDuty services you want Zenoss to send events to.

# Integration guides

* [Zenoss 4](https://www.pagerduty.com/docs/guides/zenoss-4-integration-guide/)
* [Zenoss 5](https://www.pagerduty.com/docs/guides/zenoss-5-integration-guide/)

# Build

The project can be build with default `python` tools.

To build project run the following command:

```sh
python setup.py bdist_egg
```

The command will create artifact `dist/ZenPacks.PagerDuty.APINotification-${plugin.version}-${py.version}.egg`. `${py.version}` better to be removed for distribution, but it is OK for development and testing

# ZenOss Installation

## Version 4

Installation of ZenOss Core v4 is pretty easy. You need to follow [the guide from this repo](https://github.com/ssvsergeyev/core-autodeploy)

## Version 5

Installation of ZenOss Core v5 is different. ZenOss introduce `Center Controller` which manage all deployments, including ZenOss Core. It uses [docker](https://www.docker.com/) to deploy it. To install and deploy ZenOss you can follow [the blog post](https://www.franken.pro/blog/how-to-install-zenoss-5-on-centos-7). Be sure that you give enough space resources if you deploy it locally for development or testing. The following table shows data that worked for me:

| Function          | Disk Space |
|-------------------|------------|
| Docker            | 40 Gb      |
| Control Center    | 30 Gb      |
| Core Data         | 20 Gb      |
| Core Data Backup  | 20 Gb      |

When you are installing docker be sure that ZenOss is compatible with it. To check compatibility versions you may run `yum` as the following:

```sh
yum --enablerepo=zenoss-stable deplist serviced-${your-version}
```

You may do the same for `zenoss-core-service`


#License
Copyright (c) 2013, PagerDuty, Inc. <info@pagerduty.com>
 All rights reserved.
 
 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:
* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
* Neither the name of PagerDuty Inc nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL PAGERDUTY INC BE LIABLE FOR ANY
 DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

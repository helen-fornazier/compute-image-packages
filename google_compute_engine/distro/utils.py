#!/usr/bin/python
# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities that are distro specific."""

import subprocess
import os
from google_compute_engine import constants


class Utils(object):
  """Utilities used by Linux guest services."""

  def __init__(self, debug=False):
    """Constructor.

    Args:
      debug: bool, True if debug output should write to the console.
    """
    self.debug = debug

  def EnableNetworkInterfaces(
      self, interfaces, logger, dhclient_script=None):
    """Enable the list of network interfaces.

    Args:
      interfaces: list of string, the output device names to enable.
      logger: logger object, used to write to SysLog and serial port.
      dhclient_script: string, the path to a dhclient script used by dhclient.
    """
    pass

  def HandleClockSync(self, logger):
    """Called when clock drift token changes."""
    command = ['/sbin/hwclock', '--hctosys']
    try:
      subprocess.check_call(command)
    except subprocess.CalledProcessError:
      logger.warning('Failed to sync system time with hardware clock.')
    else:
      logger.info('Synced system time with hardware clock.')

  def _StartSshd(self):
    """Initialize the SSH daemon."""
    # Exit as early as possible.
    # Instance setup systemd scripts block sshd from starting.
    if os.path.exists(constants.LOCALBASE + '/bin/systemctl'):
      return
    elif (os.path.exists('/etc/init.d/ssh') or
          os.path.exists('/etc/init/ssh.conf')):
      subprocess.call(['service', 'ssh', 'start'])
      subprocess.call(['service', 'ssh', 'reload'])
    elif (os.path.exists('/etc/init.d/sshd') or
          os.path.exists('/etc/init/sshd.conf')):
      subprocess.call(['service', 'sshd', 'start'])
      subprocess.call(['service', 'sshd', 'reload'])

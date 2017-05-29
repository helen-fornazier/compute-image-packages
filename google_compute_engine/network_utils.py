#!/usr/bin/python
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Utilities for configuring IP address forwarding."""

import logging
import os
import subprocess


class NetworkUtils(object):
  """System network Ethernet interface utilities."""

  def __init__(self, logger=logging):
    """Constructor.

    Args:
      logger: logger object, used to write to SysLog and serial port.
    """
    self.logger = logger
    self.interfaces = self._CreateInterfaceMap()

  def _CreateInterfaceMap(self):
    """Generate a dictionary mapping MAC address to Ethernet interfaces.

    Returns:
      dict, string MAC addresses mapped to the string network interface name.
    """

    interfaces = {}
    try:
      interfaces_list = subprocess.check_output('ifconfig -l', shell=True)
    except subprocess.CalledProcessError:
        return interfaces
    for interface in interfaces_list.split():
      try:
        mac_address = subprocess.check_output('ifconfig ' + interface + ' | grep -o -E "([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}"', shell=True)
      except subprocess.CalledProcessError:
        message = 'Unable to determine MAC address for %s.'
        self.logger.warning(message, interface)
      else:
        interfaces[mac_address[:-1]] = interface
    return interfaces

  def GetNetworkInterface(self, mac_address):
    """Get the name of the network interface associated with a MAC address.

    Args:
      mac_address: string, the hardware address of the network interface.

    Returns:
      string, the network interface associated with a MAC address or None.
    """
    return self.interfaces.get(mac_address)

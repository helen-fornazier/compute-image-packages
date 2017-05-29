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
import netifaces


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
    for interface in netifaces.interfaces():
        mac_address = netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
        if  mac_address == interface:
            message = 'Unable to determine MAC address for %s.'
            self.logger.warning(message, interface)
            continue
        interfaces[mac_address] = interface
    return interfaces

  def GetNetworkInterface(self, mac_address):
    """Get the name of the network interface associated with a MAC address.

    Args:
      mac_address: string, the hardware address of the network interface.

    Returns:
      string, the network interface associated with a MAC address or None.
    """
    return self.interfaces.get(mac_address)

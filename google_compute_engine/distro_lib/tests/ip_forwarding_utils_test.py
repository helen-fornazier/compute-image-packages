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

"""Unittest for ip_forwarding_utils.py module."""

from google_compute_engine.distro_lib import ip_forwarding_utils
from google_compute_engine.test_compat import mock
from google_compute_engine.test_compat import unittest


def _CreateMockProcess(returncode, stdout, stderr):
  mock_process = mock.Mock()
  mock_process.returncode = returncode
  mock_process.communicate.return_value = (stdout, stderr)
  return mock_process


class IpForwardingUtilsIprouteTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    self.options = {'hello': 'world'}
    with mock.patch(
        'google_compute_engine.distro_lib.ip_forwarding_utils'
        '.subprocess') as mock_subprocess:
      mock_subprocess.Popen.return_value = _CreateMockProcess(
          0, b'out', b'')
      self.mock_utils = ip_forwarding_utils.IpForwardingUtilsIproute(
          self.mock_logger)
    self.mock_utils.proto_id = 'proto'

  def testCreateRouteOptions(self):
    # Default options.
    expected_options = {
        'proto': 'proto',
        'scope': 'host',
    }
    self.assertEqual(self.mock_utils._CreateRouteOptions(), expected_options)

    # Update dictionary when arguments are specified.
    expected_options = {
        'proto': 'proto',
        'scope': 'host',
        'num': 1,
        'string': 'hello world',
    }
    self.assertEqual(
        self.mock_utils._CreateRouteOptions(num=1, string='hello world'),
        expected_options)

    # Update the default options.
    expected_options = {
        'proto': 'test 1',
        'scope': 'test 2',
    }
    self.assertEqual(
        self.mock_utils._CreateRouteOptions(proto='test 1', scope='test 2'),
        expected_options)

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.subprocess')
  def testRunIpRoute(self, mock_subprocess):
    mock_process = _CreateMockProcess(0, b'out', b'')
    mock_subprocess.Popen.return_value = mock_process
    args = ['foo', 'bar']
    options = {'one': 'two'}

    self.assertEqual(
        self.mock_utils._RunIpRoute(args=args, options=options), 'out')
    command = ['ip', 'route', 'foo', 'bar', 'one', 'two']
    mock_subprocess.Popen.assert_called_once_with(
        command, stdout=mock_subprocess.PIPE, stderr=mock_subprocess.PIPE)
    mock_process.communicate.assert_called_once_with()
    self.mock_logger.warning.assert_not_called()

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.subprocess')
  def testRunIpRouteReturnCode(self, mock_subprocess):
    mock_process = _CreateMockProcess(1, b'out', b'error\n')
    mock_subprocess.Popen.return_value = mock_process

    self.assertEqual(
        self.mock_utils._RunIpRoute(args=['foo', 'bar'], options=self.options),
        '')
    command = ['ip', 'route', 'foo', 'bar', 'hello', 'world']
    self.mock_logger.warning.assert_called_once_with(
        mock.ANY, command, b'error')

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.subprocess')
  def testRunIpRouteException(self, mock_subprocess):
    mock_subprocess.Popen.side_effect = OSError('Test Error')

    self.assertEqual(
        self.mock_utils._RunIpRoute(args=['foo', 'bar'], options=self.options),
        '')
    command = ['ip', 'route', 'foo', 'bar', 'hello', 'world']
    self.mock_logger.warning.assert_called_once_with(
        mock.ANY, command, 'Test Error')

  def testParseForwardedIps(self):
    self.assertEqual(self.mock_utils.ParseForwardedIps(None), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps([]), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps([None]), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['invalid']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1a1a1a1']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1.1.1.1.1']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1111.1.1.1']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1.1.1.1111']), [])
    expected_calls = [
        mock.call.warning(mock.ANY, None),
        mock.call.warning(mock.ANY, 'invalid'),
        mock.call.warning(mock.ANY, '1a1a1a1'),
        mock.call.warning(mock.ANY, '1.1.1.1.1'),
        mock.call.warning(mock.ANY, '1111.1.1.1'),
        mock.call.warning(mock.ANY, '1.1.1.1111'),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  def testParseForwardedIpsComplex(self):
    forwarded_ips = {
        '{{}}\n\"hello\"\n!@#$%^&*()\n\n': False,
        '1111.1.1.1': False,
        '1.1.1.1': True,
        'hello': False,
        '123.123.123.123': True,
        '1.1.1.': False,
        '1.1.1.a': False,
        None: False,
        '1.0.0.0': True,
        '1.1.1.1/1': True,
        '1.1.1.1/11': True,
        '123.123.123.123/1': True,
        '123.123.123.123/123': False,
        '123.123.123.123/a': False,
        '123.123.123.123/': False,
    }
    input_ips = forwarded_ips.keys()
    valid_ips = [ip for ip, valid in forwarded_ips.items() if valid]
    invalid_ips = [ip for ip, valid in forwarded_ips.items() if not valid]

    self.assertEqual(self.mock_utils.ParseForwardedIps(input_ips), valid_ips)
    expected_calls = [mock.call.warning(mock.ANY, ip) for ip in invalid_ips]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)

  def testParseForwardedIpsSubnet(self):
    forwarded_ips = {
        '1.1.1.1': '1.1.1.1',
        '1.1.1.1/32': '1.1.1.1',
        '1.1.1.1/1': '1.1.1.1/1',
        '1.1.1.1/10': '1.1.1.1/10',
        '1.1.1.1/24': '1.1.1.1/24',
    }
    for ip, value in forwarded_ips.items():
      self.assertEqual(self.mock_utils.ParseForwardedIps([ip]), [value])

  def testGetForwardedIps(self):
    mock_options = mock.Mock()
    mock_options.return_value = self.options
    mock_run = mock.Mock()
    mock_run.return_value = 'a\n b \nlocal c'
    mock_parse = mock.Mock()
    mock_parse.return_value = ['Test']
    self.mock_utils._CreateRouteOptions = mock_options
    self.mock_utils._RunIpRoute = mock_run
    self.mock_utils.ParseForwardedIps = mock_parse

    self.assertEqual(
        self.mock_utils.GetForwardedIps('interface', 'ip'), ['Test'])
    mock_options.assert_called_once_with(dev='interface')
    mock_run.assert_called_once_with(
        args=['ls', 'table', 'local', 'type', 'local'], options=self.options)
    mock_parse.assert_called_once_with(['a', 'b', 'c'])

  def testAddForwardedIp(self):
    mock_options = mock.Mock()
    mock_options.return_value = self.options
    mock_run = mock.Mock()
    self.mock_utils._CreateRouteOptions = mock_options
    self.mock_utils._RunIpRoute = mock_run

    self.mock_utils.AddForwardedIp('1.1.1.1', 'interface')
    mock_options.assert_called_once_with(dev='interface')
    mock_run.assert_called_once_with(
        args=['add', 'to', 'local', '1.1.1.1/32'], options=self.options)

  def testAddIpAlias(self):
    mock_options = mock.Mock()
    mock_options.return_value = self.options
    mock_run = mock.Mock()
    self.mock_utils._CreateRouteOptions = mock_options
    self.mock_utils._RunIpRoute = mock_run

    self.mock_utils.AddForwardedIp('1.1.1.1/24', 'interface')
    mock_options.assert_called_once_with(dev='interface')
    mock_run.assert_called_once_with(
        args=['add', 'to', 'local', '1.1.1.1/24'], options=self.options)

  def testRemoveForwardedIp(self):
    mock_options = mock.Mock()
    mock_options.return_value = self.options
    mock_run = mock.Mock()
    self.mock_utils._CreateRouteOptions = mock_options
    self.mock_utils._RunIpRoute = mock_run

    self.mock_utils.RemoveForwardedIp('1.1.1.1', 'interface')
    mock_options.assert_called_once_with(dev='interface')
    mock_run.assert_called_once_with(
        args=['delete', 'to', 'local', '1.1.1.1/32'], options=self.options)

  def testRemoveAliasIp(self):
    mock_options = mock.Mock()
    mock_options.return_value = self.options
    mock_run = mock.Mock()
    self.mock_utils._CreateRouteOptions = mock_options
    self.mock_utils._RunIpRoute = mock_run

    self.mock_utils.RemoveForwardedIp('1.1.1.1/24', 'interface')
    mock_options.assert_called_once_with(dev='interface')
    mock_run.assert_called_once_with(
        args=['delete', 'to', 'local', '1.1.1.1/24'], options=self.options)


class IpForwardingUtilsIfconfigTest(unittest.TestCase):

  def setUp(self):
    self.mock_logger = mock.Mock()
    with mock.patch(
        'google_compute_engine.distro_lib.ip_forwarding_utils'
        '.subprocess') as mock_subprocess:
      mock_subprocess.Popen.return_value = _CreateMockProcess(
          0, b'out', b'')
      self.mock_utils = ip_forwarding_utils.IpForwardingUtilsIfconfig(
          self.mock_logger)

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.subprocess')
  def testRunIfconfig(self, mock_subprocess):
    mock_process = _CreateMockProcess(0, b'out', b'')
    mock_subprocess.Popen.return_value = mock_process
    args = ['foo', 'bar']
    options = {'one': 'two'}

    self.assertEqual(
        self.mock_utils._RunIfconfig(args=args, options=options), 'out')
    command = ['ifconfig', 'foo', 'bar', 'one', 'two']
    mock_subprocess.Popen.assert_called_once_with(
        command, stdout=mock_subprocess.PIPE, stderr=mock_subprocess.PIPE)
    mock_process.communicate.assert_called_once_with()
    self.mock_logger.warning.assert_not_called()

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.subprocess')
  def testRunIfconfigReturnCode(self, mock_subprocess):
    mock_process = _CreateMockProcess(1, b'out', b'error\n')
    mock_subprocess.Popen.return_value = mock_process

    self.assertEqual(
        self.mock_utils._RunIfconfig(args=['foo', 'bar']),
        '')
    command = ['ifconfig', 'foo', 'bar']
    self.mock_logger.warning.assert_called_once_with(
        mock.ANY, command, b'error')

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.subprocess')
  def testRunIfconfigException(self, mock_subprocess):
    mock_subprocess.Popen.side_effect = OSError('Test Error')

    self.assertEqual(
        self.mock_utils._RunIfconfig(args=['foo', 'bar']),
        '')
    command = ['ifconfig', 'foo', 'bar']
    self.mock_logger.warning.assert_called_once_with(
        mock.ANY, command, 'Test Error')

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.netaddr')
  def testParseForwardedIps(self, mock_netaddr):
    self.assertEqual(self.mock_utils.ParseForwardedIps(None), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps([]), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps([None]), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['invalid']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1a1a1a1']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1.1.1.1.1']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1111.1.1.1']), [])
    self.assertEqual(self.mock_utils.ParseForwardedIps(['1.1.1.1111']), [])
    expected_calls = [
        mock.call.warning(mock.ANY, None),
        mock.call.warning(mock.ANY, 'invalid'),
        mock.call.warning(mock.ANY, '1a1a1a1'),
        mock.call.warning(mock.ANY, '1.1.1.1.1'),
        mock.call.warning(mock.ANY, '1111.1.1.1'),
        mock.call.warning(mock.ANY, '1.1.1.1111'),
    ]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)
    self.assertEqual(mock_netaddr.IPNetwork.mock_calls, [])

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.netaddr')
  def testParseForwardedIpsComplex(self, mock_netaddr):
    def side_effect(arg):
      return [arg]
    mock_netaddr.IPNetwork.side_effect = side_effect
    forwarded_ips = {
        '{{}}\n\"hello\"\n!@#$%^&*()\n\n': False,
        '1111.1.1.1': False,
        '1.1.1.1': True,
        'hello': False,
        '123.123.123.123': True,
        '1.1.1.': False,
        '1.1.1.a': False,
        None: False,
        '1.0.0.0': True,
        '1.1.1.1/1': True,
        '1.1.1.1/11': True,
        '123.123.123.123/1': True,
        '123.123.123.123/123': False,
        '123.123.123.123/a': False,
        '123.123.123.123/': False,
    }
    input_ips = forwarded_ips.keys()
    valid_ips = [ip for ip, valid in forwarded_ips.items() if valid]
    invalid_ips = [ip for ip, valid in forwarded_ips.items() if not valid]

    self.assertEqual(self.mock_utils.ParseForwardedIps(input_ips), valid_ips)
    expected_calls = [mock.call.warning(mock.ANY, ip) for ip in invalid_ips]
    self.assertEqual(self.mock_logger.mock_calls, expected_calls)
    expected_calls = [mock.call.IPNetwork(ip) for ip in valid_ips]
    self.assertEqual(mock_netaddr.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.netaddr')
  def testParseForwardedIpsSubnet(self, mock_netaddr):
    mock_netaddr.IPNetwork.return_value = ['1.1.1.1']
    forwarded_ips = [
        '1.1.1.1',
        '1.1.1.1/32',
        '1.1.1.1/1',
        '1.1.1.1/10',
        '1.1.1.1/24'
    ]
    for ip in forwarded_ips:
      self.assertEqual(self.mock_utils.ParseForwardedIps([ip]), ['1.1.1.1'])
    expected_calls = [mock.call.IPNetwork(ip) for ip in forwarded_ips]
    self.assertEqual(mock_netaddr.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.netifaces')
  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.netaddr')
  def testGetForwardedIps(self, mock_netaddr, mock_netifaces):
    mock_netifaces.AF_INET = 0
    mock_netifaces.ifaddresses.return_value = [[
        {'addr': 'a', 'netmask': 'a mask'},
        {'addr': 'b', 'netmask': 'b mask'},
        {'addr': 'c', 'netmask': 'c mask'},
    ]]
    mock_netaddr.IPAddress().netmask_bits.return_value = 32
    mock_parse = mock.Mock()
    mock_parse.return_value = ['Test']
    self.mock_utils.ParseForwardedIps = mock_parse

    self.assertEqual(
        self.mock_utils.GetForwardedIps('interface', 'ip'), ['Test'])
    mock_netifaces.ifaddresses.assert_called_once_with('interface')
    mock_parse.assert_called_once_with(['a/32', 'b/32', 'c/32'])

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.netaddr')
  def testAddForwardedIp(self, mock_netaddr):
    mock_netaddr.IPNetwork.return_value = ['1.1.1.1']
    mock_run = mock.Mock()
    self.mock_utils._RunIfconfig = mock_run

    self.mock_utils.AddForwardedIp('1.1.1.1', 'interface')
    mock_netaddr.IPNetwork.assert_called_once_with('1.1.1.1')
    mock_run.assert_called_once_with(
        args=['interface', 'alias', '1.1.1.1/32'])

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.netaddr')
  def testAddIpAlias(self, mock_netaddr):
    mock_netaddr.IPNetwork.return_value = [
       '1.1.1.0', '1.1.1.1', '1.1.1.2', '1.1.1.3'
    ]
    mock_run = mock.Mock()
    self.mock_utils._RunIfconfig = mock_run

    self.mock_utils.AddForwardedIp('1.1.1.1/30', 'interface')
    mock_netaddr.IPNetwork.assert_called_once_with('1.1.1.1/30')
    expected_calls = [
        mock.call(args=['interface', 'alias', '1.1.1.0/32']),
        mock.call(args=['interface', 'alias', '1.1.1.1/32']),
        mock.call(args=['interface', 'alias', '1.1.1.2/32']),
        mock.call(args=['interface', 'alias', '1.1.1.3/32'])
    ]
    self.assertEqual(mock_run.mock_calls, expected_calls)

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.netaddr')
  def testRemoveForwardedIp(self, mock_netaddr):
    mock_ip = mock.Mock()
    mock_ip.ip = '1.1.1.1'
    mock_netaddr.IPNetwork.return_value = mock_ip
    mock_run = mock.Mock()
    self.mock_utils._RunIfconfig = mock_run

    self.mock_utils.RemoveForwardedIp('1.1.1.1', 'interface')
    mock_netaddr.IPNetwork.assert_called_once_with('1.1.1.1')
    mock_run.assert_called_once_with(
        args=['interface', '-alias', '1.1.1.1'])

  @mock.patch('google_compute_engine.distro_lib.ip_forwarding_utils.netaddr')
  def testRemoveAliasIp(self, mock_netaddr):
    mock_ip = mock.Mock()
    mock_ip.ip = '1.1.1.1'
    mock_netaddr.IPNetwork.return_value = mock_ip
    mock_run = mock.Mock()
    self.mock_utils._RunIfconfig = mock_run

    self.mock_utils.RemoveForwardedIp('1.1.1.1/24', 'interface')
    mock_netaddr.IPNetwork.assert_called_once_with('1.1.1.1/24')
    mock_run.assert_called_once_with(
        args=['interface', '-alias', '1.1.1.1'])


if __name__ == '__main__':
  unittest.main()

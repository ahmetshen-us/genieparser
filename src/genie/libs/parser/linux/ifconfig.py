"""ifconfig.py

Linux parsers for the following commands:
    * ifconfig
    * ifconfig <interface>
"""

# python
import re

# metaparser
from genie.metaparser import MetaParser
from genie.metaparser.util.schemaengine import Schema, Any, Optional

# =======================================================
# Schema for 'ifconfig [<interface>]'
# =======================================================
class IfconfigSchema(MetaParser):
    """Schema for ifconfig [<interface>]"""

    schema = {
        Any(): {
            'interface': str,
            'flags': str,
            'mtu': int,
            Optional('ipv4'): {
                Any():{
                    'ip': str,
                    'netmask': str,
                    'broadcast': str,
                },
            },
            Optional('ipv6'): {
                Any():{
                    'ip': str,
                    'prefixlen': int,
                    'scopeid': str,
                },
            },
            'type': str,
            Optional('txqueuelen'): int,
            Optional('mac'): str,
            'destription': str,
            'counters': {
                'rx_pkts': int,
                'rx_bytes': int,
                'rx_value': str,
                'rx_errors': int,
                'rx_dropped': int,
                'rx_overruns': int,
                'rx_frame': int,
                'tx_pkts': int,
                'tx_bytes': int,
                'tx_value': str,
                'tx_errors': int,
                'tx_dropped': int,
                'tx_overruns': int,
                'tx_carrier': int,
                'tx_collisions': int,
            },
            Optional('device_interrupt'): int,
            Optional('device_memory'): str,
        }
    }

# =======================================================
# Parser for 'ifconfig [<interface>]'
# =======================================================
class Ifconfig(IfconfigSchema):
    """Parser for ifconfig [<interface>]"""

    cli_command = ['ifconfig {interface}','ifconfig' ]

    def cli(self, interface=None, output=None):
        if output is None:
            if interface:
                cmd = self.cli_command[0].format(interface=interface)
            else:
                cmd = self.cli_command[1]
            out = self.device.execute(cmd)
        else:
            out = output

        result_dict = {}

        # enp0s31f6: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        p1 = re.compile(r'^(?P<interface>\S+): +flags=(?P<flags>\S+) +mtu +(?P<mtu>\d+)$')

        #  inet 192.168.100.51  netmask 255.255.255.0  broadcast 192.168.100.255
        p2 = re.compile(r'^inet +(?P<ip>\S+) +netmask +(?P<netmask>\S+) '
                         '+broadcast +(?P<broadcast>\S+)$')

        #  inet6 fe80::39:1a5c:726d:b23e  prefixlen 64  scopeid 0x20<link>
        p3 = re.compile(r'^inet6 +(?P<ip>\S+) +prefixlen +(?P<prefixlen>\d+) '
                         '+scopeid +(?P<scopeid>\S+)$')

        #  ether 48:2a:e3:ff:58:55  txqueuelen 1000  (Ethernet)
        #  ether 00:50:b6:ff:4b:83  (Ethernet)
        #  loop  txqueuelen 1000  (Local Loopback)
        #  loop  (Local Loopback)
        p4 = re.compile(r'^(?P<type>\S+)( +(?P<mac>\S+))?( +txqueuelen +(?P<txqueuelen>\d+))? '
                         '+\((?P<destription>.*)\)$')

        #  RX packets 66766  bytes 4274334 (4.0 MiB)
        p5 = re.compile(r'^RX +packets +(?P<rx_pkts>\d+) +bytes +(?P<rx_bytes>\d+) '
                         '+\((?P<rx_value>.*)\)$')

        #  RX errors 0  dropped 0  overruns 0  frame 0
        p6 = re.compile(r'^RX +errors +(?P<rx_errors>\d+) +dropped +(?P<rx_dropped>\d+) '
                         '+overruns +(?P<rx_overruns>\d+) +frame +(?P<rx_frame>\d+)$')

        #  TX packets 365916  bytes 67689136 (64.5 MiB)
        p7 = re.compile(r'^TX +packets +(?P<tx_pkts>\d+) +bytes +(?P<tx_bytes>\d+) '
                         '+\((?P<tx_value>.*)\)$')

        #  TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
        p8 = re.compile(r'^TX +errors +(?P<tx_errors>\d+) +dropped +(?P<tx_dropped>\d+) '
                         '+overruns +(?P<tx_overruns>\d+) +carrier +(?P<tx_carrier>\d+) '
                         '+collisions +(?P<tx_collisions>\d+)$')

        #  device interrupt 16  memory 0xe9200000-e9220000
        #  device memory 0xdea00000-deafffff
        p9 = re.compile(r'^device( +interrupt +(?P<device_interrupt>\d+))? '
                         '+memory +(?P<device_memory>\S+)$')

        for line in out.splitlines():
            line = line.replace('\t', '    ')
            line = line.strip()
            if not line:
                continue

            # enp0s31f6: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
            m = p1.match(line)
            if m:
                group = m.groupdict()
                interface = group['interface']
                intf_dict = result_dict.setdefault(interface, {})
                intf_dict.update({k: (int(v) if v.isdigit() else v) for k, v in group.items()})
                continue

            #   inet 192.168.100.51  netmask 255.255.255.0  broadcast 192.168.100.255
            m = p2.match(line)
            if m:
                group = m.groupdict()
                ip = group['ip']
                ipv4_dict = intf_dict.setdefault('ipv4', {}).setdefault(ip, {})
                ipv4_dict.update({k: v for k, v in group.items()})
                continue

            #   inet6 fe80::39:1a5c:726d:b23e  prefixlen 64  scopeid 0x20<link>
            m = p3.match(line)
            if m:
                group = m.groupdict()
                ip = group['ip']
                ipv6_dict = intf_dict.setdefault('ipv6', {}).setdefault(ip, {})
                ipv6_dict.update({k: (int(v) if v.isdigit() else v) for k, v in group.items()})
                continue

            #   ether 48:2a:e3:ff:58:55  txqueuelen 1000  (Ethernet)
            m = p4.match(line)
            if m:
                group = m.groupdict()
                intf_dict.update({'type': group['type'],
                                  'destription': group['destription']})

                mac = group['mac']
                txqueuelen = group['txqueuelen']

                if mac:
                    intf_dict.update({'mac': mac})
                if txqueuelen:
                    intf_dict.update({'txqueuelen': int(txqueuelen)})
                continue

            #   RX packets 66766  bytes 4274334 (4.0 MiB)
            m = p5.match(line)
            if m:
                group = m.groupdict()
                counter_dict = intf_dict.setdefault('counters', {})
                counter_dict.update({k: (int(v) if v.isdigit() else v) for k, v in group.items()})
                continue

            #   RX errors 0  dropped 0  overruns 0  frame 0
            m = p6.match(line)
            if m:
                group = m.groupdict()
                counter_dict.update({k: int(v) for k, v in group.items()})
                continue

            #   TX packets 365916  bytes 67689136 (64.5 MiB)
            m = p7.match(line)
            if m:
                group = m.groupdict()
                counter_dict.update({k: (int(v) if v.isdigit() else v) for k, v in group.items()})
                continue

            #   TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
            m = p8.match(line)
            if m:
                group = m.groupdict()
                counter_dict.update({k: int(v) for k, v in group.items()})
                continue

            #   device interrupt 16  memory 0xe9200000-e9220000
            m = p9.match(line)
            if m:
                group = m.groupdict()
                interrupt = group['device_interrupt']
                memory = group['device_memory']
                if interrupt:
                    intf_dict.update({'device_interrupt': int(interrupt)})
                if memory:
                    intf_dict.update({'device_memory': memory})
                continue

        return result_dict

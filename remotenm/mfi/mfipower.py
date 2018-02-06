#!/usr/bin/env python
"""
power cycle the specified outlet on the
intellegent mfi power strip.

Connect to mfi mpower switch via ssh and copy over
busybox-ash scripts to power cycle the specified
outlet port. Additionally, trigger IP address renewal
of the power strip when power cycling the network router.

Tested with
    Ubiquiti Networks mPower-Pro External Power Control Unit: 
    8 AC Outlets with ethernet or wi-fi network.

The standard setup is to power the main router
via outlet #1 while the modem is powered via outlet #5.

Invocation
----------
::

    mfipower outlet-name

    where outlet-name is mapped to an outlet-position.
    
If the outlet-port is the router, trigger the
mfi mpower system to renew it ip address by
sending SIGUSR1 signal to udhcpc process.
"""
import sys
import argparse
import syslog
from mfi import *

# dictionary to name the outlets on the power strip
outlets = { 'modem': 5, 'router': 1 }
values = { 'cycle': 0, 'off': 1, 'on': 2 }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mfiport', type=str, choices=outlets.keys())
    #ap.add_argument('setting', type=str, choices=values.keys())
    args = ap.parse_args()
    portno = outlets[args.mfiport]
    relayid = "relay%d" % portno

    ipaddr = get_mfiaddr()
    if ipaddr is None:
        return 1

    syslog.syslog("Connecting to mfi(%s)" % ipaddr)
    client = mficonnect()
    if client is None:
        syslog.syslog("Failed to connect to mfi power strip")
        return 1

    syslog.syslog("Connected to mfi power strip")
    install_relaycmd(client)
    install_iprenew(client)
    
    cmdline = "%s %s" % (rspath, relayid)
    if args.mfiport == 'router':
        # add an argument to the cmdline to trigger
        # power-relay to renew dhcp address on the mfi mpower box
        cmdline += " 1"
    cmdline += " &"
    exec_cmdl(client, cmdline, wait=False)
        
    #
    # Disconnect from the host
    #
    syslog.syslog("Command done, closing connection to mfi power strip")
    client.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())

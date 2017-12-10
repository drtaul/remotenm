#!/usr/bin/env python
"""
Ping the internet connection, if ping fails
power cycle the network gateway (modem).
"""
import os
import sys
import syslog
import requests

def connected_to_internet(url='http://www.google.com/', timeout=5):
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        print("No internet connection available.")
    return False


if not connected_to_internet():
    syslog.syslog("Detected internet connection is down, reboot modem")
    mfidir = os.path.dirname(__file__)
    os.chdir(mfidir)
    import mfipower
    cmdline = "mfipower.py modem"
    sys.argv = cmdline.split()
    mfipower.main()
else:
    syslog.syslog("internet connection is ok")

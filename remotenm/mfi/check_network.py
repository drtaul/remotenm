#!/usr/bin/env python
"""
Ping the internet connection, if ping fails
power cycle the network gateway (modem).
"""
import os
import sys
import argparse
import time
import syslog
import signal
import requests
import daemon
from remotenm.mfi import mfipower

continue_running = True


def connected_to_internet(url='http://www.google.com/', timeout=5):
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        print("No internet connection available.")
    return False


def checknetwork(checkcnter):
    if not connected_to_internet():
        syslog.syslog("Detected internet connection is down, reboot modem")
        checkcnter = 0
        mfidir = os.path.dirname(__file__)
        os.chdir(mfidir)
        cmdline = "mfipower.py modem"
        sys.argv = cmdline.split()
        mfipower.main()
    else:
        if checkcnter == 0:
            syslog.syslog("internet connection is ok")
    return checkcnter


def daemon_main(sleeptime):
    global continue_running
    syslog.syslog("Starting network connection monitor daemon w/ period of %d secs" % sleeptime)
    while continue_running:
        callcounter = 0
        time.sleep(sleeptime)
        if continue_running:
            callcounter = checknetwork(callcounter) % 100
    sys.exit(0)


def programCleanup(signal, frame):
    global continue_running
    syslog.syslog("network connection monitor daemon exiting")
    continue_running = False
    
    
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--daemon', action='store_true', default=False)
    ap.add_argument('--chkperiod', type=int, default=30,
                    help="period in secs to wakeup and check")
    args = ap.parse_args()
    if args.daemon:
        sighandler_map = { signal.SIGTERM: programCleanup }
        with daemon.DaemonContext(signal_map=sighandler_map):
            daemon_main(args.chkperiod)
    else:
        checknetwork()
    return 0


if __name__ == '__main__':
    sys.exit(main())

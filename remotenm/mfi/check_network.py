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
import subprocess
import signal
import requests
from urlparse import urlparse
import daemon
from remotenm.mfi import mfipower

continue_running = True
MODEM_IP='192.168.5.1'
TEST_URL='http://www.google.com/'

def pingurl(rhost):
    try:
        output = subprocess.check_output("ping -{} 1 {}".format('c', rhost), shell=True)

    except Exception, e:
        return False

    return True


def wait_for_modem(modemip='192.168.1.5', mxwait=600):
    syslog.syslog("Waiting for modem at %s to ping" % modemip)
    waitim = 0
    while not pingurl(modemip):
        time.sleep(15)
        waitim += 15
        if waitim > mxwait:
            syslog.syslog("Mx time exceeded on Waiting for modem at %s to ping" % modemip)
            break


def wait_for_url(url=TEST_URL, mxwait=600):
    netloc = urlparse(url).netloc
    if len(netloc) > 0:
        url=netloc
    syslog.syslog("Waiting for URL at %s to ping" % url)
    waitim = 0
    while not pingurl(url):
        time.sleep(15)
        waitim += 15
        if waitim > mxwait:
            syslog.syslog("Mx time exceeded on Waiting for URL at %s to ping" % modemip)
            break


def connected_to_internet(url=TEST_URL, gwip=MODEM_IP, timeout=5):
    if gwip is not None:
        if not pingurl(gwip):
            return False
    netloc = urlparse(url).netloc
    if len(netloc) > 0:
        if not pingurl(netloc):
            return False
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        syslog.syslog("Connection Error: No internet connection available.")
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
        syslog.syslog("Modem power cycle completed")
        wait_for_modem()
        wait_for_url()
        syslog.syslog("Attempt at network modem recovery completed")
    else:
        if checkcnter == 0:
            syslog.syslog("internet connection is ok")
        checkcnter += 1
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
        checknetwork(0)
    syslog.syslog("Exiting network connection checker")
    return 0


if __name__ == '__main__':
    sys.exit(main())

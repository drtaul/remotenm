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
# TEST_URL='http://www.google.com/'
TEST_URL='fvfvpn.privatedns.org'

def pingurl(rhost, timeout=3):
    try:
        output = subprocess.check_output("ping -W {} -{} 1 {}".format(timeout, 'c', rhost), shell=True)

    except Exception, e:
        syslog.syslog("Failed to ping host %s" % rhost)
        return False

    return True


def wait_for_modem(modemip=MODEM_IP, mxwait=600, sleeptm=15):
    syslog.syslog("Waiting for modem at %s to ping" % modemip)
    waitim = 0
    while not pingurl(modemip):
        time.sleep(sleeptm)
        waitim += sleeptm
        if waitim > mxwait:
            syslog.syslog("Mx time exceeded on Waiting for modem at %s to ping" % modemip)
            return False
        syslog.syslog("Failed to ping modem")

    syslog.syslog("successfully pinged modem")
    return True
        

def wait_for_url(url=TEST_URL, mxwait=600, sleeptm=15):
    netloc = urlparse(url).netloc
    if len(netloc) > 0:
        url=netloc
    syslog.syslog("Waiting for URL at %s to ping" % url)
    waitim = 0
    while not pingurl(url):
        time.sleep(sleeptm)
        waitim += sleeptm
        if waitim > mxwait:
            syslog.syslog("Mx time exceeded on Waiting for URL at %s to ping" % url)
            return False
        syslog.syslog("Failed to ping URL:%s", url)
    return True


def connected_to_internet(url=TEST_URL, gwip=MODEM_IP, timeout=5):
    if gwip is not None:
        if not pingurl(gwip):
            return False
    netloc = urlparse(url).netloc
    if len(netloc) > 0:
        if not pingurl(netloc):
            return False
    #try:
    #    _ = requests.get(url, timeout=timeout)
    #    return True
    #except requests.ConnectionError:
    #    syslog.syslog("Connection Error: No internet connection available.")
    return True


def checknetwork(checkcnter):
    if not connected_to_internet():
        syslog.syslog("Detected internet connection is down, reboot modem")
        if wait_for_modem():
            checkcnter = 0
            mfidir = os.path.dirname(__file__)
            os.chdir(mfidir)
            cmdline = "mfipower.py modem"
            sys.argv = cmdline.split()
            rc = mfipower.main()
            time.sleep(10)
            if rc != 0:
                syslog.syslog("Failed to access mfi power strip, abort this attempt")
            else:
                syslog.syslog("Modem power cycle request submitted")
                if wait_for_modem():
                    if wait_for_url():
                        syslog.syslog("Attempt at network modem recovery completed")
                    else:
                        syslog.syslog("Failed network modem recovery")
                else:
                    syslog.syslog("Modem not available?")
        else:
            syslog.syslog("Modem does not repond to ping")
                    
    else:
        if checkcnter == 0:
            syslog.syslog("internet connection is ok")
        checkcnter += 1
    return checkcnter


def daemon_main(sleeptime):
    global continue_running
    syslog.syslog("Starting network connection monitor daemon w/ period of %d secs" % sleeptime)
    callcounter = 0
    while continue_running:
        time.sleep(sleeptime)
        if continue_running:
            callcounter = checknetwork(callcounter) % 100
    syslog.syslog("Daemon exiting")
    sys.exit(1)


def programCleanup(signal, frame):
    global continue_running
    syslog.syslog("network connection monitor daemon exiting")
    continue_running = False
    
    
def main():
    rc = 0
    ap = argparse.ArgumentParser()
    ap.add_argument('--daemon', action='store_true', default=False)
    ap.add_argument('--chkperiod', type=int, default=30,
                    help="period in secs to wakeup and check")
    args = ap.parse_args()
    if args.daemon:
        rc = 1
        sighandler_map = { signal.SIGTERM: programCleanup }
        with daemon.DaemonContext(signal_map=sighandler_map):
            daemon_main(args.chkperiod)
    else:
        checknetwork(0)
    syslog.syslog("Exiting network connection checker")
    return rc


if __name__ == '__main__':
    sys.exit(main())

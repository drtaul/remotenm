"""
Utility functions for connecting to mfi mpower
strip and issuing commands.

The mfi power strip was purchased on Amazon Nov, 2017

"""
import os
import sys
import traceback
import select
import paramiko
import socket

rscnam = 'relaypwroffon'
# path on mfi of relay-power-off-on script
rspath = "/tmp/" + rscnam
rnewnam = 'iprenew'
# path on mfi of ip-renew script
iprpath = "/tmp/" + rnewnam

_HOSTNAME = "mfi"
_USERNAME = "ubnt"
_PASSWORD = "ubnt"
port = 22

def get_mfiaddr():
    try:
        addr = socket.gethostbyaddr(_HOSTNAME)[0]
    except socket.error:
        print "ERROR: %s is not valid, refresh dhcp hostnames" % _HOSTNAME
        return None
    return addr

def initmfi(hostname=_HOSTNAME, username=_USERNAME, password=_PASSWORD):
    global _HOSTNAME, _USERNAME, _PASSWORD
    _HOSTNAME = hostname
    _USERNAME = username
    _PASSWORD = password
    socket.gethostbyaddr(_HOSTNAME)

def exec_cmdl(client, cmdline, wait=True):
    # print "running cmd %s" % cmdline
    stdin, stdout, stderr = client.exec_command(cmdline)

    if wait:
        while not stdout.channel.exit_status_ready():
            # Only print data if there is data to read in the channel
            if stdout.channel.recv_ready():
                rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
                # if len(rl) > 0:
                #    # Print data from stdout
                #    print stdout.channel.recv(1024),

def install_cmd(client, lfile, rpath):
    with open(lfile, 'r') as lfil:
        exec_cmdl(client, "echo '##' > %s" % rpath)
        for line in lfil.readlines():
            exec_cmdl(client, "echo '%s' >> %s" % (line, rpath))

    exec_cmdl(client, "chmod a+x %s" % rpath)        

    
def install_relaycmd(client):
    global rscnam, rspath
    local_fn = os.path.join(os.path.dirname(__file__), rscnam)
    install_cmd(client, local_fn, rspath)

def install_iprenew(client):
    global rnewnam, iprpath
    local_fn = os.path.join(os.path.dirname(__file__), rnewnam)
    install_cmd(client, local_fn, iprpath)
    
# The mfi busybox uses older gssapi authentication
#   - initially able to use the following with additional
#     security packages however lots of problems
#  Finally determined the option 'look_for_keys = False'
#  simply uses the user + passwd 
## enable "gssapi-with-mic" authentication,
## if supported by your python installation
#UseGSSAPI = paramiko.GSS_AUTH_AVAILABLE
## enable "gssapi-kex" key exchange,
## if supported by your python installation
#DoGSSAPIKeyExchange = paramiko.GSS_AUTH_AVAILABLE
DoGSSAPIKeyExchange = False
UseGSSAPI = False

def test_mficonnect(hname=None, to=5):
    client = mficonnect(hname, to)
    if client is not None:
        print "mfi power strip seems ok"
        client.close()
        return 0
    else:
        print "mfi power strip is not available"
        return 1


def mficonnect(hname=None, to=5):
    global _HOSTNAME, _USERNAME, _PASSWORD, port
    hostname = _HOSTNAME
    username = _USERNAME
    password = _PASSWORD

    if hname is not None:
        hostname = hname
        
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        if not UseGSSAPI and not DoGSSAPIKeyExchange:
            client.connect(hostname, port, username, password, timeout=to, look_for_keys=False)
        else:
            try:
                client.connect(hostname, port, username, gss_auth=UseGSSAPI,
                               gss_kex=DoGSSAPIKeyExchange, timeout=to)
            except Exception:
                # traceback.print_exc()
                password = getpass.getpass('Password for %s@%s: ' % (username, hostname))
                client.connect(hostname, port, username, password, timeout=to)
    except Exception as e:
        print('*** Caught exception: %s: %s' % (e.__class__, e))
        traceback.print_exc()
        try:
            client.close()
            client = None
        except:
            pass
    return client

if __name__ == '__main__':
    test_mficonnect()


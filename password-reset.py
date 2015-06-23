#!/usr/bin/env python

__author__ = "Vinny Valdez"
__copyright__ = "Copyright 2015"
#__credits__ = [""]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Vinny Valdez"
__email__ = "vvaldez@redhat.com"
__status__ = "Prototype"

metadata_url = "http://169.254.169.254/openstack/latest/meta_data.json"
timestamp_file = "password-reset.timestamp"
password_length = 8 # any length lower than this may not meet Windows complexity requirements

import json, urllib2, time, string, random, subprocess, os, platform, sys, ConfigParser
from time import sleep

def display_password(password):
    if osPlatform == "Windows":
        display_password_windows(password)
    elif osPlatform == "Linux":
        display_password_linux(password)
    else:
        print "ERROR: Unsupported OS '%s'" % osPlatform
        sys.exit(1)

def undisplay_password():
    if osPlatform == "Windows":
        undisplay_password_windows()
    elif osPlatform == "Linux":
        undisplay_password_linux()
    else:
        print "ERROR: Unsupported OS '%s'" % osPlatform
        sys.exit(1)

def reset_password(password_length):
    if osPlatform == "Windows":
        return reset_password_windows(password_length)
    elif osPlatform == "Linux":
        return reset_password_linux(password_length)
    else:
        print "ERROR: Unsupported OS '%s'" % osPlatform
        sys.exit(1)

def reboot_system():
    if osPlatform == "Windows":
        reboot_system_windows()
    elif osPlatform == "Linux":
        reboot_system_linux()
    else:
        print "ERROR: Unsupported OS '%s'" % osPlatform
        sys.exit(1)

def display_password_linux(password):
    undisplay_password()
    print "INFO: The new password is: %s" % password
    with open("/etc/issue", "a") as file:
        file.write("The new password is: %s\n" % password)

def set_reg(name, value):
    reg_path = "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon"
    try:
        _winreg.CreateKey(_winreg.HKEY_LOCAL_MACHINE, reg_path)
        _winreg.DisableReflectionKey(_winreg.HKEY_LOCAL_MACHINE)
        registry_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, reg_path, 0, _winreg.KEY_WRITE | _winreg.KEY_WOW64_64KEY)
        _winreg.SetValueEx(registry_key, name, 0, _winreg.REG_SZ, value)
        _winreg.EnableReflectionKey(registry_key)
        _winreg.CloseKey(registry_key)
        return True
    except WindowsError:
        return False

def get_reg(name):
    reg_path = "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon"
    try:
        _winreg.DisableReflectionKey(_winreg.HKEY_LOCAL_MACHINE)
        registry_key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, reg_path, 0, _winreg.KEY_READ | _winreg.KEY_WOW64_64KEY)
        value, regtype = _winreg.QueryValueEx(registry_key, name)
        _winreg.EnableReflectionKey(registry_key)
        _winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        return None

def load_reg():
    try:
        config = ConfigParser.RawConfigParser()
        config.read(timestamp_dir + "\\" + 'password-reset.reg')
        LegalNoticeText = config.get('Winlogon', 'LegalNoticeText')
        LegalNoticeCaption = config.get('Winlogon', 'LegalNoticeCaption')
        DisableCAD = config.get('Winlogon', 'DisableCAD')
    except:
        LegalNoticeText = ""
        LegalNoticeCaption = ""
        DisableCAD = "0"
    return LegalNoticeText, LegalNoticeCaption, DisableCAD

def save_reg():
    LegalNoticeText = get_reg("LegalNoticeText")
    LegalNoticeCaption = get_reg("LegalNoticeCaption")
    DisableCAD = get_reg("DisableCAD")
    config = ConfigParser.RawConfigParser()
    config.add_section('Winlogon')
    config.set('Winlogon','LegalNoticeText',LegalNoticeText)
    config.set('Winlogon','LegalNoticeCaption',LegalNoticeCaption)
    config.set('Winlogon','DisableCAD',DisableCAD)
    with open(timestamp_dir + "\\" + 'password-reset.reg','wb') as configfile:
        config.write(configfile)

def display_password_windows(password):
    print "INFO: The new password is: %s" % password
    save_reg()
    set_reg("LegalNoticeText", "The new password for admin is: %s" % password)
    set_reg("LegalNoticeCaption", "admin password was reset")
    set_reg("DisableCAD", "0")

def undisplay_password_windows():
    print "INFO: Removing password from being displayed at logon"
    LegalNoticeText, LegalNoticeCaption, DisableCAD = load_reg()
    set_reg("LegalNoticeText", LegalNoticeText)
    set_reg("LegalNoticeCaption", LegalNoticeCaption)
    set_reg("DisableCAD", DisableCAD)

def undisplay_password_linux():
    print "INFO: Removing password from being displayed at logon"
    with open("/etc/issue", "r") as file:
        lines = file.readlines()
    with open("/etc/issue", "w") as file:
        for line in lines:
            if not "The new password is:" in line:
                file.write(line)

def id_generator(password_length, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(password_length))

def reset_password_windows(password_length):
    password = id_generator(password_length)
    write_timestamp()
    print "INFO: Resetting password to: %s" % password
    os.system('net user admin %s' % password)
    return password

def reset_password_linux(password_length):
    password = id_generator(password_length)
    write_timestamp()
    print "INFO: Resetting password to: %s" % password
    cmd = ['/usr/bin/passwd', 'root']
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    p.stdin.write(u'%(p)s\n%(p)s\n' % { 'p': password })
    p.stdin.flush()
    for x in range(0, 10):
        if p.poll() is not None:
            break
        sleep(0.1)
    else:
        p.terminate()
        sleep(1)
        p.kill()
        raise RuntimeError('Setting password failed. '
            '`passwd` process did not terminate.')
    if p.returncode != 0:
        raise RuntimeError('Setting root password failed: %d' % p.returncode)
    return password

def reboot_system_linux():
    print "INFO: Rebooting system to execute cloud-init"
    os.system('reboot')

def reboot_system_windows():
    print "INFO: Rebooting system to execute cloudbase-init"
    os.system('shutdown /r /t 0')

def get_timestamp():
    try:
        with open(timestamp_file,'r') as infile:
            timestamp = infile.read()
    except:
        timestamp = ""
    return timestamp

def write_timestamp():
    with open(timestamp_file, 'w') as outfile:
        print "INFO: Writing to %s" % timestamp_file
        outfile.write(data['meta']['password-reset'])

# Main

osPlatform = platform.system()
if osPlatform == "Windows":
    import _winreg
    timestamp_dir = os.environ['PROGRAMDATA'] + "\\password-reset\\"
elif osPlatform == "Linux":
    timestamp_dir = "/var/lib/password-reset/"
else:
    print "ERROR: Unsupported OS '%s'" % osPlatform
    sys.exit(1)
try:
    os.makedirs(timestamp_dir)
except OSError:
    pass
timestamp_file = timestamp_dir + timestamp_file

# Get metadata timestamp
response = urllib2.urlopen(metadata_url)
data = json.load(response)   
print "INFO: Retrieved metadata: '%s'" % data
timestamp = get_timestamp()
try:
    password_reset = data['meta']['password-reset']
except:
    print "INFO: No metadata parameter set, nothing to do"
    sys.exit(0)
print "INFO: Checking metadata timestamp: '%s' against timestamp '%s'" % (password_reset, timestamp)
if str(password_reset) == str(timestamp).rstrip():
    print "INFO: Timestamps are the same, not resetting password"
    undisplay_password()
elif password_reset == "":
    print "INFO: Timestamp in metadata is blank, not resetting password"
    undisplay_password()
else:
    if timestamp == "":
        print "INFO: Timestamp on disk is blank, resetting password"
    else:
        print "INFO: Timesamps exist but differ, resetting password"
    password = reset_password(password_length)
    display_password(password)
    reboot_system()

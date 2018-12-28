#!/usr/bin/env python3

import apt
import os
import lsb_release as lsb

def check_OS():
    print("Checking for Ubuntu 18.04")
    info = lsb.get_lsb_information()
    if (info["ID"] == "Ubuntu" and info["RELEASE"] == "18.04"):
        print("Done")
        return True
    else:
        print("Ubuntu 18.04 not detected. You must be using a different operating system.")
        return False

def check_installed_package(package):
    print("Checking cache for", package)
    if cache[package].is_installed:
        print(package, "installed")
        return True
    else:
        print(package, "not found")
        return False
    
def install_postfix():
    print("Installing postfix with 'apt'...")
    os.system("sudo apt update")
    os.system("sudo DEBIAN_PRIORITY=low apt install postfix")

def configure_mailbox():
    mailbox = "Maildir"
    print("""\
Default location for the mailbox directory is 'Maildir'
Is this location acceptable? (y/n): """)
    cont= input()
    while True:
        while cont.lower() not in ("y", "n"):
            cont = input("(y/n): ")
        if cont == 'n':
            virtual = input("Input custom path: ")
            final = input("Is " + mailbox + " okay? (y/n)")
            if final == 'y':
                break
        else:
            break

    print("Configuring home_mailbox...")
    cmd = "sudo postconf -e 'home_mailbox= " + mailbox + "/'"
    os.system(cmd)
    return mailbox

def configure_alias_maps():
    virtual = "/etc/postfix/virtual"
    print("""\
Default location for virtual_alias_maps is '/etc/postfix/virtual'
Is this location acceptable? (y/n):""")
    cont= input()
    while True:
        while cont.lower() not in ("y", "n"):
            cont = input("(y/n): ")
        if cont == 'n':
            virtual = input("Input custom path: ")
            final = input("Is " + virtual + " okay? (y/n)")
            if final == 'y':
                break
        else:
            break
    cmd = "sudo postconf -e 'virtual_alias_maps= hash:" + virtual + "'"
    os.system(cmd)
    return virtual

def map_mail_addresses(virtualPath):
    input("Press enter to edit virtual maps text file.\nWhen you are finished, save and close the file.")
    cmd = "sudo nano " + virtualPath
    os.system(cmd)
    #os.system("%s %s" % (os.getenv("EDITOR"), virtualPath))
    input("Press enter to apply virtual maps.")
    os.system("sudo postmap /etc/postfix/virtual")
    print("Restarting postfix to ensure changes have been applied.")
    os.system("sudo systemctl restart postfix")

def configure_firewall():
    print("Configuring firewall...")
    os.system("sudo ufw allow Postfix")

def configure_mail_environment(mailbox):
    print("Configuring MAIL environment variable...")
    cmd="echo 'export MAIL=~/" + mailbox + "' | sudo tee -a /etc/bash.bashrc | sudo tee -a /etc/profile.d/mail.sh"
    os.system(cmd)

def install_mail_client(mailbox):
    cont = input("Would you like to install the s-nail package as a mail client? (y/n): ")
    while True:
        while cont.lower() not in ("y", "n"):
            cont = input("(y/n): ")
        if cont == 'y':
            os.system("sudo apt install s-nail")
            with open("/etc/s-nail.rc", 'a') as file:
                file.write("set emptystart")
                file.write("set folider=" + mailbox)
                file.write("set record=+sent")
            break
        else:
            break

def install_opendmarc():
    os.system("sudo apt install opendmarc")

def install_opendkim():
    os.system("sudo apt install opendkim opendkim-tools")

check_OS()

cache = apt.Cache()
cache.open()

if (not check_installed_package("postfix")):
    install_postfix()
    mailbox = configure_mailbox()
    virtualPath = configure_alias_maps()
    map_mail_addresses(virtualPath)
    configure_firewall()
    configure_mail_environment(mailbox)
    install_mail_client(mailbox)

if (not check_installed_package("opendmarc")):
    install_opendmarc()

if (not check_installed_package("opendkim")):
    install_opendkim()

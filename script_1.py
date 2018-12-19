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
    input("Press enter when finished with initial configurations.")
    mailbox = "";
    done = False;
    while (!done):
        mailbox = input("Enter valid mailbox directory name: ")
        try:
            os.mkdir(mailbox)
        except OSError:
            print("Invalid directory name...")
        else:
            os.rmdir(mailbox)
            done = True
            print("Configuring home_mailbox...")
            os.system("sudo postconf -e 'home_mailbox= " + mailbox + "/")
    return mailbox

def configure_alias_maps():
    virtual = "/etc/postfix/virtual"
    cont= input("""\
Default location for virtual_alias_maps is '/etc/postfix/virtual'
Is this location acceptable? (y/n): """)
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
    os.system("sudo postconf -e 'virtual_alias_maps= hash:" + virtual)
    return virtual

def map_mail_addresses(virtualPath):
    input("Press enter to open virtual maps text file.")
    os.system("%s %s" % (os.getenv("EDITOR"), virtualPath))
    print("When you are finished, save and close the file.")
    input("Press enter to apply virtual maps.")
    os.system("sudo postmap /etc/postfix/virtual")
    print("Restarting postfix to ensure changes have been applied.")
    os.system("sudo systemctl restart postfix")

def configure_firewall():
    input("Press enter to configure firewall.")
    os.system("sudo ufw allow Postfix")

def configure_mail_environment(mailbox):
    input("Press enter to configure MAIL environment variable.")
    os.system("echo 'export MAIL=~/" + mailbox + "' | sudo tee -a /etc/bash.bashrc | sudo tee -a /etc/profile.d/mail.sh")

def install_mail_client(mailbox):
    pass

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

#!/usr/bin/env python3

import apt
import os
import lsb_release as lsb
import re

def check_OS():
    print("Checking for Ubuntu 18.04")
    info = lsb.get_lsb_information()
    if (info["ID"] == "Ubuntu" and info["RELEASE"] == "18.04"):
        print("Done")
        return True
    else:
        print("Ubuntu 18.04 not detected. You must be using a different operating system.")
        exit()

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
    os.system("apt update")
    os.system("DEBIAN_PRIORITY=low apt install postfix")

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
    cmd = "postconf -e 'home_mailbox= " + mailbox + "/'"
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
    cmd = "postconf -e 'virtual_alias_maps= hash:" + virtual + "'"
    os.system(cmd)
    return virtual

def map_mail_addresses(virtualPath):
    input("Press enter to edit virtual maps text file.\nWhen you are finished, save and close the file.")
    cmd = "nano " + virtualPath
    os.system(cmd)
    input("Press enter to apply virtual maps.")
    os.system("postmap /etc/postfix/virtual")
    print("Restarting postfix to ensure changes have been applied.")
    os.system("systemctl restart postfix")

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
            os.system("apt install s-nail")
            with open("/etc/s-nail.rc", 'a') as file:
                file.write("set emptystart")
                file.write("set folider=" + mailbox)
                file.write("set record=+sent")
            break
        else:
            break

def install_opendmarc():
    os.system("apt install opendmarc")

def install_opendkim():
    os.system("apt install opendkim opendkim-tools")

def dns_recommendation_spf():
    domain_name = input("Input your domain name (e.g. domain.com): ")
    print("Add the following to your DNS record:")
    print('*.' + domain_name + '. 1800 IN TXT "v=spf1 mx ip4:YOUR_MX_IP -all"')
    print(domain_name + '.com. 1800 IN TXT "v=spf1 mx ip4:YOUR_MX_IP -all"')
    print("Remember to replace 'YOUR_MX_IP' with the IP address of your mail server.")
    return domain_name;

def generate_dkim_key(domain_name):
    cmd = "opendkim-genkey -b 2048 -d " + domain_name + "-s " + domain_name + ".dkim"
    os.system(cmd)

def configure_dkim():
    with open("/etc/opendkim.conf", 'w') as file:
        file.write("""
Socket local:/var/spool/postfix/private/opendkim
Syslog yes
UMask 002
UserID postfix

Selector mail
Mode sv
SubDomains yes
AutoRestart yes
Background yes
Canonicalization relaxed/relaxed
DNSTimeout 5
SignatureAlgorithm rsa-sha256
X-Header yes
Logwhy yes

InternalHosts /etc/internalhosts
KeyTable /etc/opendkim/keytable
SigningTable refile:/etc/opendkim/signtable

OversignHeaders From""")

def configure_signtable(domain_name):
    with open("/etc/opendkim/signtable", 'w') as file:
        file.write("*@" + domain_name + " " + domain_name)

def configure_keytable(domain_name):
    with open("/etc/opendkim/keytable", 'w') as file:
        wrt = domain_name + " " + domain_name + ":mail:/path/to/" + domain_name + ".dkim.private"
        file.write(wrt)

def configure_internalhosts(domain_name):
    with open("/etc/internalhosts") as file:
        file.write("your." + domain_name + "\n")
        file.write(domain_name + "\n")
        while True:
            ip = input("Enter the IP address of your domain: ")
            if (re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)):
                file.write(ip)
                break

def dns_recommendation_dkim(domain_name):
    print("Add the following to your DNS record:")
    path = "/etc/" + domain_name + ".dkim.txt"
    dns_entry = ""
    with open(path, 'r') as file:
        dns_entry = file.read()
    print("mail._domainkey." + domain_name + " 1800 IN TXT " + dns_entry)
        
        

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

domain_name = dns_recommendation_spf()
generate_dkim_key(domain_name)
configure_dkim()
configure_signtable(domain_name)
configure_keytable(domain_name)
configure_internalhosts(domain_name)
dns_recommendation_dkim(domain_name)

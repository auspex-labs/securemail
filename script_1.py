#!/usr/bin/env python3

#https://petermolnar.net/howto-spf-dkim-dmarc-postfix/
#https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-postfix-on-ubuntu-18-04

import apt
import os
import lsb_release as lsb
import re

def check_OS():
    print("Checking Operating System Version")
    info = lsb.get_lsb_information()
    if (info["ID"] == "Ubuntu" and info["RELEASE"] == "18.04"):
        print("Current operating system ({0}, {1}) is compatible".format(info["ID"], info["RELEASE"]))
        return True
    else:
        print("The current operating system is not a supported configuration.")
        exit()

def check_installed_package(cache, package):
    print("Checking cache for", package)
    if cache[package].is_installed:
        print(package, "installed")
        return True
    else:
        print(package, "not found")
        cmd = "apt install " + package
        os.system(cmd)
        path = "/etc/" + package
        if (not os.path.isdir(path)):
            os.mkdir(path)
        return False

def configure_firewall():
    print("Configuring firewall...")
    os.system("sudo ufw allow Postfix")

def get_domain_name():
    domain_name = input("Input your domain name (e.g. domain.com): ")
    return domain_name

def get_domain_ip():
    while True:
        ip = input("Enter the IP address of your mail server: ")
        if (re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)):
            return ip

def dns_recommendation_spf(domain_name, ip):
    print("Add the following TXT record to your DNS:")
    print('*.' + domain_name + '. 1800 IN TXT "v=spf1 mx ip4' + ip + ' -all"')
    print(domain_name + '.com. 1800 IN TXT "v=spf1 mx ip4:' + ip + ' -all"')

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
    with open("/etc/opendkim/signtable", 'w+') as file:
        file.write("*@" + domain_name + " " + domain_name)

def configure_keytable(domain_name):
    with open("/etc/opendkim/keytable", 'w+') as file:
        wrt = domain_name + " " + domain_name + ":mail:/path/to/" + domain_name + ".dkim.private"
        file.write(wrt)

def configure_internalhosts(domain_name, ip):
    with open("/etc/internalhosts", 'w+') as file:
        file.write("your." + domain_name + "\n")
        file.write(domain_name + "\n")
        file.write(ip)

def dns_recommendation_dkim(domain_name):
    print("Add the following TXT record to your DNS:")
    dns_entry = ""
    with open("default.txt", 'r') as file:
        dns_entry = file.read()
    entry = dns_entry[dns_entry.find("(")+2 : dns_entry.find(" )")]
    print("mail._domainkey." + domain_name + " 1800 IN TXT" + entry)

def dns_recommendation_dmarc(domain_name):
    print("Add the following TXT record to your DNS: ")
    print("_dmarc." + domain_name + ' 1800 IN TXT "v=DMARC1; p=reject; rua=mailto:postmaster@' +  domain_name + '"')
    print("Replace 'postmaster' with the email address which should collect aggregate reports.")

def configure_dmarc(domain_name):
    failureAddress = input("Enter the email address responsible for failure reports (e.g. postmaster@domain.com): ")
    with open("/etc/opendmarc.conf", 'w') as file:
        file.write("AuthservID mail." + domain_name + "\n")
        file.write("""\
PidFile /var/run/opendmarc.pid
RejectFailures true
Syslog true
SyslogFacility mail
""")
        file.write("TrustedAuthservIDs mail." + domain_name + "\n")
        file.write("""\
IgnoreHosts /etc/opendmarc/ignore.hosts
UMask 002
UserID postfix:postfix
TemporaryDirectory /tmp
Socket local:/var/spool/postfix/private/opendmarc
""")
        file.write("FailureReportsSentBy " + failureAddress + "\n")
        file.write("FailureReportsBcc " + failureAddress + "\n")
        file.write("""\
FailureReports true
AutoRestart true
PublicSuffixList /etc/effective_tld_names.dat
HistoryFile /var/log/opendmarc.log""")

def configure_ignorehosts(ip):
    with open("/etc/opendmarc/ignore.hosts", 'w+') as file:
        file.write("localhost\n")
        file.write("127.0.0.0/8\n")
        file.write(ip + "/24")

def integrate_dmarc_dkim():
    with open("/etc/postfix/main.cf", 'a') as file:
        file.write("""\
smtpd_milters = unix:private/opendkim unix:private/opendmarc
non_smtpd_milters = unix:private/opendkim unix:private/opendmarc""")
        

check_OS()

cache = apt.Cache()
cache.open()

domain_name = get_domain_name()
ip = get_domain_ip()

check_installed_package(cache, "postfix")
configure_firewall()
integrate_dmarc_dkim()
os.system("systemctl restart postfix")

if (not check_installed_package(cache, "opendkim")):
    check_installed_package(cache, "opendkim-tools")
    dns_recommendation_spf(domain_name, ip)
    generate_dkim_key(domain_name)
    configure_dkim()
    configure_signtable(domain_name)
    configure_keytable(domain_name)
    configure_internalhosts(domain_name, ip)
    dns_recommendation_dkim(domain_name)

if (not check_installed_package(cache, "opendmarc")):
    dns_recommendation_dmarc(domain_name)
    configure_dmarc(domain_name)
    configure_ignorehosts(ip)

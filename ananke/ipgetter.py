#!/usr/bin/python3

import itertools
import os
import re

import requests

def get_ip(external=True):
    # Are we inside Amazon EC2?
    if external:
        try:
            return requests.get('http://169.254.169.254/latest/meta-data/public-ipv4').text
        except:
            pass
        
    f = os.popen('ifconfig')
    for iface in [' '.join(i) for i in iter(lambda: list(itertools.takewhile(lambda l: not l.isspace(),f)), [])]:
        if re.findall('^(eth|wlan|wlp3s|enp0s)[0-9]',iface) and re.findall('RUNNING',iface):
            ip = re.findall('(?<=inet\saddr:)[0-9\.]+',iface)
            if ip:
                return ip[0]
    return False
    

        
    




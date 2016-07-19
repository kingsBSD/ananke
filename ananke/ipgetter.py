#!/usr/bin/python3

import itertools
import os
import re

def get_ip():
    f = os.popen('ifconfig')
    for iface in [' '.join(i) for i in iter(lambda: list(itertools.takewhile(lambda l: not l.isspace(),f)), [])]:
        if re.findall('^(eth|wlan)[0-9]',iface) and re.findall('RUNNING',iface):
            ip = re.findall('(?<=inet\saddr:)[0-9\.]+',iface)
            if ip:
                return ip[0]
    return False
    
if __name__ == '__main__':

    ip = get_ip()
    
    if ip:
        msg = "* Visit http://"+ip+":5000 *"
        border = len(msg) * "*"
    
        print(border)
        print(msg)
        print(border)
        
    




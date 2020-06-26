#!/usr/bin/python3
# ---------------------------
# (C) 2020 by Herby
#
# V 1.0

import requests
import json
import sys
import time
#import argparse
# import os


def ipv62mac(ipv6):
    # remove subnet info if given
    subnetIndex = ipv6.find("/")
    if subnetIndex != -1:
        ipv6 = ipv6[:subnetIndex]

    ipv6Parts = ipv6.split(":")
    macParts = []
    for ipv6Part in ipv6Parts[-4:]:
        while len(ipv6Part) < 4:
            ipv6Part = "0" + ipv6Part
        macParts.append(ipv6Part[:2])
        macParts.append(ipv6Part[-2:])

    # modify parts to match MAC value
    macParts[0] = "%02x" % (int(macParts[0], 16) ^ 2)
    del macParts[4]
    del macParts[3]

    return ":".join(macParts)

def extract_values(obj, key):
    """Pull all values of specified key from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    return results

def find_first(key,value,tf):
    """find first key/value in data and return found record and false/true
    best for uniqe IDs
    """
#    print ("k",key,"v",value)
    for a in tf:
        v = extract_values(a, key)
#        print(v)
        if value in v:
            return True, a
    return False, ""

def find_all(key,value,tf):
    """find all key/value in data and return found record and false/true
    best for name, city, country
    not for IPs, ...
    """
    fa=[]
    fr = False
    for a in tf:
        v = extract_values(a, key)
        if value in v:
            fr = True
            fa.append(a)
    return fr, fa

def find_text(text,tf):
    """find all records with comntaining text and return found records and false/true
    best for all
    """
    fa=[]
    fr = False
    for a in tf:
        v = json.dumps(a)
        if text in v:
            fr = True
            fa.append(a)
    return fr, fa

def get_from_tf(url):
    """ get all data for a type from explorer web-site
    and return a list
    """
    p=1
    tf = []
    while 1:
        resp = requests.get(url+str(p))
        r = resp.json()
        if len(resp.text) == 3:
            break
        for a in r:
            tf.append(a)
        p += 1
    #print(url," ---: ",p)
    return (tf)

def send_telegram(telegram,text):
    """
    Here is the list of all tags that you can use

    <b>bold</b>, <strong>bold</strong>
    <i>italic</i>, <em>italic</em>
    <a href="http://www.example.com/">inline URL</a>
    <code>inline fixed-width code</code>
    <pre>pre-formatted fixed-width code block</pre>

    """

    payload = {
    'chat_id': telegram["chat_id"],
    'text': text,
    'parse_mode': 'HTML'
    }

    resp=requests.post("https://api.telegram.org/bot{token}/sendMessage".format(token=telegram["token"]),data=payload).json()
    return resp["ok"],resp

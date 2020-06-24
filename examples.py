#!/usr/bin/python3
# ---------------------------
# (C) 2020 by Herby
#
# V 1.0

import requests
import json
import sys
import time
import ipaddress

import tf
#import argparse
import os

"""
NextActionCreate 0
NextActionSign 1
NextActionPay 2
NextActionDeploy 3
NextActionDelete 4
NextActionInvalid 5
NextActionDeleted 6
"""

# URLs
base_url    = "https://explorer.grid.tf/explorer/"
farms_url   = base_url + "farms?page="
gw_url      = base_url +"gateways?page="
nodes_url   = base_url + "nodes?page="
res_url     = base_url + "reservations?page="
users_url   = base_url + "users?page="


ts_now = time.time()

#colors
red = "\033[0;31;40m"
white = "\033[0;37;40m"

#symbol
s_red = "x"
s_white = "-"


def example1():
    """ example to find all nodes in Austria with farm name """
    i = 0
    b,found=tf.find_all("country","Austria",nodes)
    if b:
        for n in found:
            i += 1
            ts_pro = n["updated"]+offline_timeout
            c = white
            if ts_now > ts_pro: c = red
            ok,farm=tf.find_first("id",n['farm_id'],farms)
            if not ok:
                print (c,n['node_id'],n['farm_id'],' <------------problem!!!')
                #sys.exit(0)
            else:
                print (c,n['node_id'],n['farm_id'],farm['name'])
    print ('i:------',i)

def example2(allFarms):
    """ list all farms or only from GEC"""

    farmer = []
    for f in farms:
        farmer.append({
            'id':f['id'],
            'name':f['name'],
            'cnt':0,
            'online' : 0,
            'threebot_id' : f['threebot_id']
            })

    print ("-"*80)
#    print (farmer)
#    print ("-"*80)
    ni=0
    for n in nodes:
        ni += 1
        fid = n['farm_id']
        for f in farmer:
            if f['id'] == fid:
                f['cnt'] += 1
                if ts_now < n['updated']+offline_timeout:
                    f['online'] += 1

    fi = 0
    oi = 0
    ci = 0

    tg_text_down = ""
    line_text =  ""
    tg_text = "Daliy Nodes Statistic: "+ time.strftime('%Y-%m-%d %H:%M',time.localtime(ts_now))+"\n"
    tg_text += "<b>Farm_id \t on  cnt  name(3bot-id)</b>\n"
    tg_text += "<code>"
    farmer_sort = sorted(farmer,key=lambda x: x["id"])
    for f in farmer_sort:
        #if ('green_edge' in f['name']) or ('GEC' in f['name']):
        gec = ['green_edge','GEC','gec','GreenEdge']
        if any(e in f['name'] for e in gec) or allFarms==True:
            fi += 1
            oi += f['online']
            ci += f['cnt']
            line_text = str(f['id']).rjust(7)+str(f['online']).rjust(3)+str(f['cnt']).rjust(3)+" "+f['name']+"("+str(f["threebot_id"])+")\n"
            if f['online'] == f['cnt']:
                tg_text += line_text
            else:
                tg_text_down += line_text

    tg_text += "</code>Farms with nodes down\n<code>"
    tg_text += tg_text_down
    tg_text += "</code>--------------------\n"
    tg_text += "Farms:"+str(fi)+" Nodes> Online:"+str(oi)+" Total:"+str(ci)

    print (tg_text)
    return (tg_text)

def example3():
    """ find my reservtions"""
    rn = rk = rv = rc = rz = rp = rr = rs = rd = rg = 0

    b,found=tf.find_all("customer_tid",130,res)
#    b = True
#    found = res
    if b:
        for r in found:
            ts = r["epoch"]
            ts_pro = r["data_reservation"]["expiration_provisioning"]
            ts_res = r["data_reservation"]["expiration_reservation"]

            pts = time.strftime('%Y-%m-%d',time.localtime(ts))
            pts_pro = time.strftime('%Y-%m-%d',time.localtime(ts_pro))
            pts_res = time.strftime('%Y-%m-%d',time.localtime(ts_res))
            pts_now = time.strftime('%Y-%m-%d',time.localtime(ts_now))

            if ts_now > ts_res: continue

            res_text =""
            if (r["data_reservation"]["networks"] != [] ):
                rn += 1
                res_text += "network|"
                n0=r["data_reservation"]["networks"][0]
                res_text += n0["name"]+" |\t "+n0["iprange"]
            if (r["data_reservation"]["kubernetes"] != [] ):
                rk += 1
                k0 = r["data_reservation"]["kubernetes"][0]
                res_text += "kubernetes<"+k0["network_id"]+" |\t "+k0["ipaddress"]+"> "
            if (r["data_reservation"]["volumes"] != [] ):
                rv += 1
                res_text += "volumes "
            if (r["data_reservation"]["containers"] != [] ):
                rc += 1
                c0 = r["data_reservation"]["containers"][0]
                c1 = c0["flist"].rsplit('/', 1)[-1]
#                res_text += "containers:"+c0.rsplit('. ', 1)[-1] +" "
                res_text += "containers|\t"+c1.rpartition('.')[0] +"<"
                res_text += c0["network_connection"][0]["network_id"]+"|"
                res_text += c0["network_connection"][0]["ipaddress"]+">"
            if not (r["data_reservation"]["zdbs"] in (None, []) ):
                zz = 0
                for zb in r["data_reservation"]["zdbs"]:
                    zz += 1
                    rz += 1
                res_text += "zdbs|"+str(zz)+" "
            if not(r["data_reservation"]["proxies"] in (None, []) ):
                rp += 1
                res_text += "proxies "
            if not(r["data_reservation"]["reverse_proxies"] in (None, []) ):
                rr += 1
                res_text += "reserve_proxies "
            if not(r["data_reservation"]["subdomains"] in (None, []) ):
                rs += 1
                res_text += "subdomains "
            if not(r["data_reservation"]["domain_delegates"] in (None, []) ):
                rd += 1
                res_text += "domain_delegates "
            if not(r["data_reservation"]["gateway4to6"] in (None, []) ):
                rg += 1
                res_text += "gateway4to6 "
                #print (r["data_reservation"]["gateway4to6"])

            c = white
#            if ts_now > ts_res: c = red
#            print (c,r["id"],r["customer_tid"],pts,pts_pro,pts_res)
#            print (c,r["id"],r["next_action"],r["customer_tid"],pts_res,res_text)
#            if ts_now < ts_res:

            print (r["id"],r["next_action"],r["customer_tid"],pts_pro,pts_res,res_text)

#        print("rn  rk  rv  rc  rz  rp  rr  rs  rd  rg")
#        print(rn , rk , rv , rc , rz , rp , rr , rs , rd , rg)

        print ("Networks:",rn)
        print ("Kubernetes:",rk)
        print ("Conatiner:",rc)
        print ("ZDBs:",rz)
        print ("Proxys:",rp)
        print ("Reverse Proxys:",rr)
        print ("Subdomains:",rs)
        print ("Domaind Delegation:",rn)
        print ("gateway4to6:",rg)



def example5(text,rec):
    """ find all records with this text
    """

    b,res=tf.find_text(text,rec)
    #print(res)
    i=0
    if b:
        for r in res:
            i += 1
            print(r["id"],r["name"])
        print(i)

def example6(telegram,farm_id):
    """ example to find all offline nodes in Farm with farm name
    and send nr of down nodes via telegam to group
    """
    i = 0
    b,found=tf.find_all("farm_id",farm_id,nodes)
    if b:
        ok,farm=tf.find_first("id",farm_id,farms)
        if not ok:
            print ("farm not found")
            sys.exit(1)
        for n in found:
            ts_pro = n["updated"]+offline_timeout
            c = white
            if ts_now > ts_pro:
                c = red
                i += 1
                print (c,n['node_id'],n['farm_id'],farm['name'])
    print ('i:------',i)
    if i>0:
        text="<code><b>"+str(i)+" nodes down on Farm: "+farm['name']+"</b></code>"
        ok,resp = tf.send_telegram(telegram,text)
        if not ok:
            print ("ERROR: ",resp)

def example7():
    for f in farms:
        if f["wallet_addresses"][0]["asset"]=="TFT":
            print("tft")

def example8(userlist,res):
    for u in res:
        #if u["id"] in userlist:
        print (u["id"],u["name"],u["email"])

    """
    for u in userlist:
        print ("--------------",u)
        ok,res=tf.find_first("id",u,res)
        if ok:
            print (u, res["name"],res["email"])
    """

def example9(id):
    from stellar_sdk import server

#    server = Server(horizon_url="https://horizon-testnet.stellar.org")

    # get a list of transactions that occurred in ledger 1400
#    transactions = server.transactions().for_ledger(1400).call()
#    print(transactions)

    # get a list of transactions submitted by a particular account
    transactions = server.transactions().for_account(account_id=id).call()
    print(transactions)

def example10(farmid):
    """ list nodes info from farm """
    i = 0
    csv="\t"
    b,found=tf.find_all("farm_id",farmid,nodes)
    if b:
#        print(80*"_")
        ok,farm=tf.find_first("id",farmid,farms)
        if not ok:
            print (c,farmid,' <------------problem!!!')
            #sys.exit(0)
        else:
#            print ("Farm:",farm['name'])
            fn=farm['name']
            fid=farm['id']


#        print (" NodeID           V1      CRU   MRU    HRU    SRU")
        print (".",csv,"FarmID",csv,"NodeID",csv," V1-ID",csv,"name",csv,"ZOS",csv, \
            "T-CRU",csv,"T-MRU",csv,"T-HRU",csv,"T-SRU",csv, \
            "U-CRU",csv,"U-MRU",csv,"U-HRU",csv,"U-SRU",csv, \
            "R-CRU",csv,"R-MRU",csv,"R-HRU",csv,"R-SRU",)
        for n in found:
            i += 1
            ts_pro = n["updated"]+offline_timeout
            c = s_white
            if ts_now > ts_pro:
                c = s_red
                #continue
            # nn = n['node_id'][:4]+".."+n['node_id'][-4:]
            nn = n['node_id']

#            print (c,nn,n["node_id_v1"], \
#                str(n["total_resources"]["cru"]).rjust(4), \
#                str(n["total_resources"]["mru"]).rjust(4), \
#                str(n["total_resources"]["hru"]).rjust(8), \
#                str(n["total_resources"]["sru"]).rjust(7) \
#                )
            line = c+csv+str(fid)+csv+nn+csv+n["node_id_v1"]+csv+n["hostname"]+csv+n["os_version"]+csv


            for re in ["total_resources", "used_resources", "reserved_resources"]:
                line+=str(n[re]["cru"])+csv
                line+=str(n[re]["mru"])+csv
                line+=str(n[re]["hru"])+csv
                line+=str(n[re]["sru"])+csv

            line+=fn+csv
            int = ""
            ipv6 = ""

            if n["ifaces"] != None:
                for ii in n["ifaces"]:
                    mac=False
                    int += ii["name"]
#                    try:
                    if ii['addrs'] != None:
                        for ip in ii['addrs']:
                            ip = ip.split('/')[0]
                            if ip == "::1": continue
                            if ipaddress.ip_address(ip).version == 6:
                                if not mac:
                                    int += " ("+tf.ipv62mac(ip)+")"
                                    mac=True
                                if ip[0] not in ['f',":"]:
                                    ipv6 += ip + " ("+ii["name"]+")    "

#                    except:
#                        print ("!!!!!!!!-",ii["name"],ip)
#                        iiiint = "no int"
                        #traceback.print_exc
                    int += csv
            int = ipv6+csv+int
            line += int
            #print (int)
            print (line)





# ---------------------------------------------

telegram_3sdk_group = {"token":"804820058:AAEnxln3mjOWGA76131ucloIKswlSdHMLro","chat_id":-467483520}
telegram_herby = {"token":"804820058:AAEnxln3mjOWGA76131ucloIKswlSdHMLro","chat_id":249140376}

# print sumary for all or only GEC nodes



#set time to put node offline : default 10 min
offline_timeout=60*10

farms = tf.get_from_tf(farms_url)
nodes = tf.get_from_tf(nodes_url)

res = tf.get_from_tf(res_url)
gw = tf.get_from_tf(gw_url)
users = tf.get_from_tf(users_url)

#example1()
#example2(True)

#example3()
#example8("k",users)
#sys.exit()

#example4(9156)
#example5("MFxftFaF78sVlBwgZi+NfYKZtSi9dnurzwIOhKoyy2k=",res)
#example5("5738ikSBtYquMEV0JobrVre4yyESUl",res)
#example5("ustria",nodes)
#example5("TFT",farms)
#example6(telegram_3sdk_group,173611)



tf.send_telegram(telegram_3sdk_group,example2(False))
sys.exit()
# example8([98,130,1,7],users)
#example9("GBKVJL52QU3OIKVPNCPP62B4MLJ5HRAOJ6X3S6KUJ6PVBIDVRKELZQ2B")

#example5("GAXHKWABWWR7WCCPBIFNX4Q4QDFJ7K4NLGI7ZI76IB77VIQ5C2ANRK7K",farms)

#example10(1)
example10(82872)
#sys.exit()
example10(12775)
example10(84041)
example10(118280)
example10(118313)
example10(173632)

example10(118276)
example10(118300)
example10(118315)
example10(173609)
example10(173611)

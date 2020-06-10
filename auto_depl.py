#!/usr/bin/python3
# ---------------------------
# (C) 2020 by Herby
#
# V 1.0

from Jumpscale import j
import time
import sys
import requests
import ipaddress


def get_my_reservations(tid):
    reservations = j.sal.zosv2.reservation_list(tid=130,next_action="DEPLOY")
    #do some checks
    return reservations

def check_public_ipv6(node):
    """
    check for public on any interface IPv6
    """

    ok = False
    for ii in node.ifaces:
#        try:
        for ip in ii.addrs:
            ip = ip.split('/')[0]
            if ipaddress.ip_address(ip).version == 6:
                if ip[0] not in ['f',":"]:
                    ok = True

#    except:
#        print(ok)

    return ok



def get_free_ip(reservations,node,networkname):
    """
    find netork reservation
    and free IP on node for a specific network
    """
    ips=[]
    iprange=''
    for reservation in sorted(reservations, key=lambda r: r.id, reverse=True):
        if reservation.next_action != "DEPLOY":
            continue
        rnetworks = reservation.data_reservation.networks
        for network in rnetworks:
            if  network.name == networkname:
                for netres in network.network_resources:
                    if netres.node_id == node:
                        iprange = netres.iprange

        rcontainer = reservation.data_reservation.containers
        for container in rcontainer:
            if container.node_id == node:
                for netcon in container.network_connection:
                    if netcon.network_id == networkname:
                        ips.append(netcon.ipaddress)

        rkubernetes = reservation.data_reservation.kubernetes
        for kubernetes in rkubernetes:
            if kubernetes.node_id == node:
                ips.append(kubernetes.ipaddress)



    # asuming /24 !!
    if iprange == '':
        print("error: no network found for:",networkname)
        sys.exit(1)
    nodenet = iprange[0:-4]
    #search first free IP
    i = 1
    free_ip = ''
    while i<254:
        i+=1
        free_ip = nodenet+str(i)
        if free_ip not in ips:
            break
    # todo: check if free_ip is a valid IP
    return free_ip

def check_network_res(res_id):
    '''
    check if networkres is Ok
    via results_k8s
    '''

    results = j.sal.zosv2.reservation_result(res_id)
    print ("len:result:",len(results))
    res_nodes = []
    for r in results:
        res_nodes.append(r.node_id)

    nn = res.data_reservation.networks
    for n in nn:
        nr = n.network_resources
        print ("len:network_res:",len(nr))
        for r in nr:
            if r.node_id not in res_nodes:
                print (r.node_id, "missing")

def create_network():
    '''
    create a overlay network
    with all nodes from farms + GW inside
    !Attetione!
    can be a problem when more than 254 nodes --> IP Address logic
    '''

    # Load the zero-os sal and create empty reservation method
    zos = j.sal.zosv2
    r = zos.reservation_create()

    # change this
    expiration = int(j.data.time.HRDateToEpoch('2021/01/31'))

    overlay_network_ip_range = overlay_network_pre+"0.0/16"
    iprange = "automatic"

    # Farm ID of the farms involved
    GE_Salzburg1 =    12775
    GE_CapeTown1 =   118280
    GE_Vienna2 =      82872
    GE_Vienna1 =      84041
    GE_Rochester1 =  118276
    GE_Toronto1 =    118300
    GE_Frankfurt1 =  118313
    GE_StGallen1 =   118315
    GE_Daniel =      173609
    GE_Jakob =       173611
    GE_Vienna1 =     173632

    nodes_GE_Salzburg1     = zos.nodes_finder.nodes_search(farm_id=GE_Salzburg1)
    nodes_GE_CapeTown1     = zos.nodes_finder.nodes_search(farm_id=GE_CapeTown1)
    nodes_GE_Vienna2 	   = zos.nodes_finder.nodes_search(farm_id=GE_Vienna2)
    nodes_GE_Vienna1       = zos.nodes_finder.nodes_search(farm_id=GE_Vienna1)
    nodes_GE_Rochester1    = zos.nodes_finder.nodes_search(farm_id=GE_Rochester1)
    nodes_GE_Toronto1      = zos.nodes_finder.nodes_search(farm_id=GE_Toronto1)
    nodes_GE_Frankfurt1    = zos.nodes_finder.nodes_search(farm_id=GE_Frankfurt1)
    nodes_GE_StGallen1     = zos.nodes_finder.nodes_search(farm_id=GE_StGallen1)
    nodes_GE_Daniel        = zos.nodes_finder.nodes_search(farm_id=GE_Daniel)
    nodes_GE_Jakob         = zos.nodes_finder.nodes_search(farm_id=GE_Jakob)
    nodes_GE_Vienna1       = zos.nodes_finder.nodes_search(farm_id=GE_Vienna1)

    # Fixed IPv4 gateway node
    ipv4_gateway='CBDY1Fu4CuxGpdU3zLL9QT5DGaRkxjpuJmzV6V5CBWg4'
    gwnode = j.clients.explorer.explorer.nodes.get(ipv4_gateway)


    # Create network data structure
    network = zos.network.create(r, ip_range=overlay_network_ip_range, network_name=overlay_network_name)


#    nodes_all = nodes_GE_StGallen1  + nodes_GE_Frankfurt1 + nodes_GE_Toronto1 +nodes_GE_Rochester1
    nodes_all = nodes_GE_Salzburg1  + nodes_GE_Vienna2
    nodes_all.append(gwnode)

    # We only need one WG interface, once set this is set to True
    #wg_already_set = False

    # This adds all the nodes that are up and accepts 'FreeTFT' as a currency.
    #nipl = dict()  # node ip list :-)
    ii = 0
    for i, node in enumerate(nodes_all):
        if (zos.nodes_finder.filter_is_up(node) and zos.nodes_finder.filter_is_free_to_use(node) and check_public_ipv6(node)):
            ii += 1
            iprange = overlay_network_pre+f"{i+10}.0/24"
            ippre = overlay_network_pre+f"{i+10}."
            zos.network.add_node(network, node.node_id , iprange)
            #nipl[node.node_id]=ippre
            print("Node: ", i,node.farm_id, node.node_id,  " (",node.total_resources.cru, ") :", iprange)
        else:
            print("--> bad Node: ", i,node.farm_id, node.node_id,  " (",node.total_resources.cru, ") :", iprange, \
                zos.nodes_finder.filter_is_up(node),zos.nodes_finder.filter_is_free_to_use(node),check_public_ipv6(node))

#    if (zos.nodes_finder.filter_public_ip4(node) and wg_already_set == False):
    wg_config = zos.network.add_access(network, gwnode.node_id, overlay_network_pre+'254.0/24', ipv4=True)
    print("Node number: ", i, gwnode.node_id, ":", iprange,"  WG")
    #wg_already_set = True


    #print (nipl)
    print (80*"-")
    print ("usable nodes:",ii)

    # print the wireguard config - store in a secure place.
    print("WG Interface configured:")
    print (80*"-")
    print(wg_config)
    print (80*"-")
    #sys.exit(0)




    # register the reservation
    registered_reservation = zos.reservation_register(r, expiration, currencies=currency)

    print(registered_reservation)
    time.sleep(5)
    # inspect the result of the reservation provisioning
    result = zos.reservation_result(registered_reservation.reservation_id)
    print(result)

    time.sleep(5)
    check_network_res(registered_reservation)
    #todo: check if all nodes are in the result!
    sys.exit(0)


def create_minio(nodeset):


    password = "xxsupersecret"  # zdb secret_set
    #todo: randomize it!!

    # customize this !!!
    zdb_size = 10
    expiration = int(j.data.time.HRDateToEpoch('2020/06/10'))
    #expiration = int(j.data.time.HRDateToEpoch('2021/01/31'))


    wallet = j.clients.stellar.get(wallet_name)

    flist_url = "https://hub.grid.tf/tf-official-apps/minio-2020-01-25T02-50-51Z.flist"
    #flist_url = "https://hub.grid.tf/tf-official-apps/minio:latest.flist"

    zos = j.sal.zosv2
    reservation_zdbs = zos.reservation_create()
    reservation_storage = zos.reservation_create()

    #todo: select the best CPU node

    if nodeset == "vie2":
        # vie2 ########################################
        """ CPU nodes
        BvJzAiQTqTJoBZ1F5WzYoPpWUBoyRWp7agXSWnY7SBre
        CpssVPA4oh455qDxakYhiazgG6t2FT6gAGvmPJMKJL2d
        HkfruwpT1yjx3TTiKn5PVBGFDmnTEqrzz6S36e4rFePb
        9LmpYPBhnrL9VrboNmycJoGfGDjuaMNGsGQKeqrUMSii
        3FPB4fPoxw8WMHsqdLHamfXAdUrcRwdZY7hxsFQt3odL
        CrgLXq3w2Pavr7XrVA7HweH6LJvLWnKPwUbttcNNgJX7
        9TeVx6vtivk65GGf7QSAfAuEPy5GBDJe3fByNmxt73eT
        Dv127zmU6aVkS8LFUMgvsptgReokzGj9pNwtz1ZLgcWf
        HXRB7qxBwMp1giM3fzRDRGYemSfTDiLUhteqtAvmWiBh
        GiSqnwbuvQagEiqMoexkq582asC8MattsjbFFuMdsaCz
        6mVGwQ41R9f7VJpNoJ6QLs4V15dsfMNXfEmQYhVEwCz6
        """
        minio_master_node_id = 'BvJzAiQTqTJoBZ1F5WzYoPpWUBoyRWp7agXSWnY7SBre'
        # vie2 apollo ########################################
        zdb_node_id=['CLbt5He2JibpLb4VQtBEeYz3r7j1YYopeNSGAtjZKPPQ',
            'CayXiccrTd1uudPtBi1y6YusEXFFTENX3TShPJ85FnLJ',
            'DKxHM2qdSMw1c4s5bUdURWkmnvR9LiHP4cwTmCNZtpDK',
            '3yjVSkNM5vvpiQ8ey7xJHucHNrNvzkM5rWWASEYNsNQn',
            '4N6Rsb8QAMJXgcfWESDh1ccUkvjGWFrV4az65MZoLktb']


    if nodeset == "sbg1":
        # salzbug1 cpu nodes
        """
        BSusuRh6qFzheQFwNPe1S5FA5pdSZVJwVLhpNS6GN4XD
        FCxp4JG2kr76dCnc2FzniApdwBak52uaSfbuigknS5Jx
        FhfqdPSbEncHPWF74eDyDKjXTUfQjxwon9Hih9pG3Kjs
        7fHSAHEvUGtUcYSqLtpGq8ANssPikTyyHC52FddDYF4Y
        FjwyHVvfATkVb4Puh4x6jCMS79TVVgSYagAuZTxWrsbj
        9211BFV7MFwktD2b8jHE9Ub3fHRtaYQyBBfwT9kEKA7q
        FUq4Sz7CdafZYV2qJmTe3Rs4U4fxtJFcnV6mPNgGbmRg
        5Pb5NMBQWLTWhXK2cCM8nS6JZrnP2HaTP452TfMMYT9p
        DUF2knurdMuX2eJVp9o7tXq4eNBy2fbxBoWhrMXWPEtF
        8zdqjFD7GLsSSfsTgFYcGusw91gQ3tdx7jbUhJep2a5X
        6chi1iSczxfF4U2iyCcJwkwWnwzcDgQHzCRExK9r4V1j
        """
        minio_master_node_id = '6chi1iSczxfF4U2iyCcJwkwWnwzcDgQHzCRExK9r4V1j'
        # sbg1 apollo ########################################
        zdb_node_id=['HugtVL51BFNLbZbbxnWu2GEe8hV97YVPac19zy5wwNpT',
            '9KAbX21NGbZYupBJ6EeeWx3ZTKDx7ADevr8qtmEa5WkC',
            '9kcLeTuseybGHGWw2YXvdu4kk2jZzyZCaCHV9t6Axqqx',
            '3h4TKp11bNWjb2UemgrVwayuPnYcs2M1bccXvi3jPR2Y',
            '5Pb5NMBQWLTWhXK2cCM8nS6JZrnP2HaTP452TfMMYT9p']
            #'FLeByELHK22evRYqJokHsCMCF9wQpLtuyehUp1LgR5eM']

    if nodeset == "stg1":
        # St.Gallen CPU nodes
        """
        HnfviKvEtLXRh89uNC6MtEyg6PTbje3tNvUVBLAhWUmh    #dead
        5W8VCwtMnHineriACfF4y6gzDcoN9QwqrgkQ4k3V67X2    #dead
        7Gr3dVseRuQQgWEhp2nxXEzYRQx7Qt2t9k7qLUzY8r6M
        A3aoanVoFsngY7DFXKrCgnEH4XBgYpHoMrGMMz4FaqFx
        7ZEQQrh59ExcSwBj6F137qdW8cwGcLfnNg3ftu5L3D3J
        7duAWxuR1JAp3HEEWHKU8rBXwJoLCmwBpwvYkHJU75pz
        D5tphUSss9TJXe8ohzxXzP78t5nyX92fhYLBUPyZXJD1
        4p7txkT5HUUsknbBbtNtGLhChCXo6UmQWa5HdphCeNJu
        7D1E7rxukVi7cDFsMZ3UoKi3tHjQT9NFFs1hBiGvP1ff
        4Bvocr4hRVikfh7ijs32Vx9zLytVZYfNAxyXkge84wFp    #dead
        8h8bzadEZjn18eP1T6Pep5dcMuZqx6ArH5eqAJofjfYk
        """

        minio_master_node_id ='8h8bzadEZjn18eP1T6Pep5dcMuZqx6ArH5eqAJofjfYk'
        # stg1 apollo ########################################
        zdb_node_id=['BjiztEd9N4utH3M559653VxLvVncBhRCac2t3w7Y9fSE',
            '51EKwgRL6n3pLXBcTUsbzvq5VaAV2DA2LrVzFxrEKqH9',
            'y9b8MnqJDoK5SNNtzsysWyjHPUPXfPyDVxkGaF3K3px',
            '89mNigU1u94nATtvho3Ut7n9HT7zx6nuVqeXUFnmQwrA',
            'GdhTt47LD7Xn2RiVcGWW4fQ67YyiZEcgPgzeJcowge6s']


    if nodeset == "sbg1_no_apllo":
        # only on salzbug1 cpu nodes
        minio_master_node_id = 'BSusuRh6qFzheQFwNPe1S5FA5pdSZVJwVLhpNS6GN4XD'
        zdb_node_id=['HugtVL51BFNLbZbbxnWu2GEe8hV97YVPac19zy5wwNpT',
            'FCxp4JG2kr76dCnc2FzniApdwBak52uaSfbuigknS5Jx',
            'FhfqdPSbEncHPWF74eDyDKjXTUfQjxwon9Hih9pG3Kjs',
            '7fHSAHEvUGtUcYSqLtpGq8ANssPikTyyHC52FddDYF4Y',
            'FjwyHVvfATkVb4Puh4x6jCMS79TVVgSYagAuZTxWrsbj']


    if nodeset == "vie2sbg1":
        # mix vie2 + salzburg1 ########################################
        minio_master_node_id = 'FhfqdPSbEncHPWF74eDyDKjXTUfQjxwon9Hih9pG3Kjs'   #sbg1
        zdb_node_id=['HugtVL51BFNLbZbbxnWu2GEe8hV97YVPac19zy5wwNpT',    ##sbg1
            '9KAbX21NGbZYupBJ6EeeWx3ZTKDx7ADevr8qtmEa5WkC',     #sbg1
            'CLbt5He2JibpLb4VQtBEeYz3r7j1YYopeNSGAtjZKPPQ',     #vie2
            'CayXiccrTd1uudPtBi1y6YusEXFFTENX3TShPJ85FnLJ',     #vie2
            'DKxHM2qdSMw1c4s5bUdURWkmnvR9LiHP4cwTmCNZtpDK']     #vie2

    minio_master_node_ip = get_free_ip(myres,minio_master_node_id,overlay_network_name)

    print("minio_master_node_ip:",minio_master_node_ip)

    # Create volume for metadata storage
    volume = zos.volume.create(reservation_storage,minio_master_node_id,size=100,type='SSD')

    registered_reservation_volume = zos.reservation_register(reservation_storage, expiration, currencies=currency)

    # inspect the result of the reservation provisioning
    results_volume = zos.reservation_result(registered_reservation_volume.reservation_id)

    # make payment for the volume
    payment_id_volume=zos.billing.payout_farmers(wallet, registered_reservation_volume)


    for i, node_id in enumerate(zdb_node_id):
        zos.zdb.create(
            reservation=reservation_zdbs,
                node_id=node_id,
                size=zdb_size,
                mode='seq',
                password=password,
                disk_type="HDD",
                public=False)


    # register the reservation
    registered_reservation_zdbs = zos.reservation_register(reservation_zdbs, expiration, currencies=currency)

    # make payment for the zbds
    payment_id_zdb=zos.billing.payout_farmers(wallet, registered_reservation_zdbs)

    total_workloads = len(reservation_zdbs.data_reservation.zdbs) + len(reservation_zdbs.data_reservation.volumes)
    results_zdbs = zos.reservation_result(registered_reservation_zdbs.reservation_id)
    s=0
    while len(results_zdbs) < total_workloads:
        time.sleep(5)  # wait for worklaods to be deployed
        s += 5
        results_zdbs = zos.reservation_result(registered_reservation_zdbs.reservation_id)
        print ("\r","wait to finish zdbs... ",s, end = '')
    print("... zdbs created")
    # ----------------------------------------------------------------------------------
    # Read the IP address of the 0-db namespaces after they are deployed
    # we will need these IPs when creating the minio container
    # ----------------------------------------------------------------------------------
    namespace_config = []
    for result in results_zdbs:
        data = result.data_json
        cfg = f"{data['Namespace']}:{password}@[{data['IP']}]:{data['Port']}"
        namespace_config.append(cfg)

    # All IP's for the zdb's are now known and stored in the namespace_config structure.
    print(namespace_config)

    # ----------------------------------------------------------------------------------
    # With the low level disk managers done and the IP addresses discovered we can now build
    # the reservation for the min.io S3 interface.
    # ----------------------------------------------------------------------------------
    # overlay_network_name="Artheon-Production"
    reservation_master_minio = zos.reservation_create()

    minio_secret_encrypted = j.sal.zosv2.container.encrypt_secret(minio_master_node_id, "m987654321")

    shards_encrypted = j.sal.zosv2.container.encrypt_secret(minio_master_node_id, ",".join(namespace_config))
    secret_env = {"SHARDS": shards_encrypted, "SECRET_KEY": minio_secret_encrypted}


    minio_master_container=zos.container.create(
        reservation=reservation_master_minio,
        node_id=minio_master_node_id,
        network_name=overlay_network_name,
        ip_address=minio_master_node_ip,
        flist=flist_url,
        interactive=False,
        entrypoint='/bin/entrypoint',
        cpu=4,
        memory=4096,
        env={
            "DATA":"3",
            "PARITY":"2",
            "ACCESS_KEY":"minioap3",
            },
        secret_env=secret_env,
    )

    # ----------------------------------------------------------------------------------
    # Attach persistent storage to container - for storing metadata
    # ----------------------------------------------------------------------------------
    zos.volume.attach_existing(
        container=minio_master_container,
        volume_id=f'{registered_reservation_volume.reservation_id}-{volume.workload_id}',
        mount_point='/data')
    registered_reservation_minio_master = zos.reservation_register(reservation_master_minio, expiration, currencies=currency)
    results_master_minio = zos.reservation_result(registered_reservation_minio_master.reservation_id)

    # make payment for the minio_master
    payment_id_master_minio=zos.billing.payout_farmers(wallet, registered_reservation_minio_master)
    print ("Minio ID:",registered_reservation_minio_master.reservation_id)


def create_container(interact):

    HUB_URL = "https://hub.grid.tf/tf-bootable"
    wallet = j.clients.stellar.get(wallet_name)
    expiration = int(j.data.time.HRDateToEpoch('2020/06/10'))

    container_flist = f"{HUB_URL}/ubuntu:18.04-r1.flist"

    #container_flist = "https://hub.grid.tf/teibler02.3bot/hteibler-ovc-tools-2.5.6.flist"
    #container_flist = "https://hub.grid.tf/teibler02.3bot/hteibler-zabbix-1.0.8.flist"
    storage_url = "zdb://hub.grid.tf:9900"


    node_id="89mNigU1u94nATtvho3Ut7n9HT7zx6nuVqeXUFnmQwrA"
    ip_address = get_free_ip(myres,node_id,overlay_network_name)

    node = j.clients.explorer.explorer.nodes.get(node_id)
    farm = j.clients.explorer.explorer.farms.get(node.farm_id)

    print ("--------  create container ---------")
    print ("IP:",ip_address)
    print ("node:",node_id)
    print ("Farm ID:",node.farm_id)
    print ("Farm Name:",farm.name)

    if interact == "YES":
        interactive = True
    else:
        interactive = False

    cpu = 1
    memory = 1024
    disk_size = 1*1024

    var_dict = {"pub_key": PUBKEY}
    entry_point = "/bin/bash /start.sh"
    #entry_point = "/sbin/tini /docker-entrypoint.sh"
    #entry_point = "/bin/bash"

    # reservation structure initialisation
    zos = j.sal.zosv2

    reservation_container = j.sal.zosv2.reservation_create()

    container=zos.container.create(
        reservation=reservation_container,
        node_id=node_id,
        network_name=overlay_network_name,
        ip_address=ip_address,
        flist=container_flist,
        storage_url=storage_url,
        disk_size=disk_size,
        env=var_dict,
        public_ipv6=True,
        interactive=interactive,
        entrypoint=entry_point,
        cpu=cpu,
        memory=memory,)

    registered_reservation = zos.reservation_register(reservation_container, expiration, currencies=currency)
    #results_container = zos.reservation_result(registered_reservation.reservation_id)

    payment_container=zos.billing.payout_farmers(wallet, registered_reservation)

    #print (registered_reservation,results_container,payment_container)
    print ("Reservation:",registered_reservation.reservation_id)
    time.sleep(5)
    result = zos.reservation_result(registered_reservation.reservation_id)
    s=5
    while (len(result) == 0) and (s < 120):
        time.sleep(5)  # wait for worklaods to be deployed
        s += 1
        result = zos.reservation_result(registered_reservation.reservation_id)
        print ("\r","wait to finish container... ",s, end = '')

    r0 = result[0]
    print("\r","IPv6:",r0.data_json['ipv6'])
    print("state:",r0.state)
    print("MSG:",r0.message)
    print ("--------  create container ---------")

def create_k8s():
    wallet = j.clients.stellar.get(wallet_name)
    expiration = int(j.data.time.HRDateToEpoch('2020/12/30'))

    zos = j.sal.zosv2

    # custiomize this
    cluster_secret = 'qqqqqqqqqq'
    size = 2

    res_k8s = zos.reservation_create()

    node_master = '8TZdSPEUC8gACaNacQDFRiskiUeDxjmLm3mTUDoRaStg'
    node_workers=['37ZtYckRA47d8FW7GkUxtbCLLMFKa68KZp5UAGZmgfFW',
        'FS2bpZSpnHgs35hz3NYVLYfFmLjKffsrrRYjW8ntkoNh',
        'GzXndGfaG82B2J9nu85GGZ3XjufZDENvmVub1oaAc7RZ']

    ip_master = get_free_ip(myres,node_master,overlay_network_name)
    ip_worker = []
    for wnode in node_workers:
        ip_worker.append(get_free_ip(myres,wnode,overlay_network_name))

    master = zos.kubernetes.add_master(
        reservation=res_k8s,           # reservation structure
        node_id=node_master,          # node_id to make the capacity reservation on and deploy the flist
        network_name=overlay_network_name,     # network_name deployed on the node (node can have multiple private networks)
        cluster_secret=cluster_secret,   # cluster pasword
        ip_address=ip_master,       # IP address the network range defined by network_name on the node
        size=size,            # 1 (1 logical core, 2GB of memory) or 2 (2 logical cores and 4GB of memory)
        ssh_keys=PUBKEY)

    worker = []
    for i, node in enumerate(node_workers):
        print ("worker:",i,node,)
        worker.append(zos.kubernetes.add_worker(
            reservation=res_k8s,
            node_id=node,
            network_name=overlay_network_name,
            cluster_secret=cluster_secret,
            ip_address=ip_worker[i],
            size=size,
            master_ip=ip_master,
            ssh_keys=PUBKEY))

    print ("w:",worker)
    registered_reservation = zos.reservation_register(res_k8s, expiration, currencies=currency)
    results_k8s = zos.reservation_result(registered_reservation.reservation_id)
    print("res:",results_k8s,registered_reservation.reservation_id)
    payment_k8s=zos.billing.payout_farmers(wallet, registered_reservation)
    print ("pay:",payment_k8s)

def tcpproxy():
    zos.gateway.tcp_proxy(reservation=r,
                            node_id='CBDY1Fu4CuxGpdU3zLL9QT5DGaRkxjpuJmzV6V5CBWg4',
                            domain='s3vie1ap3.edGE_cloud.eu',
                            addr='2a04:7700:1003:1:e4e3:57ff:fec2:34f0',
                            port=9000,
                            port_tls=9001)


#----------------------------------------------------------------------------------------------------------------------------




j.clients.explorer.default_addr_set('explorer.grid.tf')

# customize this
PUBKEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDCCoY7+AchsnObo1Qct15MZWZA7KgqCaxi3DSZM34zak0dttNn7UasQtHa86dcyLJ1LWe94CaRLhM/Yi9VwvNC5QlpMizygEyvaD4pKPsQjLFm0Gi8F1SxENtxL3rOOzqqDDrnASrEKYR8ULSBSC/VjdTE5CVOTGdxMJGDsPsT2VngWikMes9n/o9kfnjN5t2SkukP6SxsxbB34RQLkdTXDvbH3JnlsjbCvtmyIq4l/SrjikjMRUyOorzPBenxzl1Jm+Fj4FYpjq277o07fqF4iOBRZ7brn1fjPxB+e8vkZ4JYC5Dodp55QxF7881VSae+G/wd9eKk8WJDOztF59jJ hteibler@miix720"
j.core.myenv.secret_set(secret="keines")
wallet_name='ht20'
currency='FreeTFT'

me=j.me
tid = me.id


#nr=j.clients.explorer.explorer.reservations.get(9847)
#check_network_res(9847)
#sys.exit(0)

#overlay_network_name="Net-20"
#overlay_network_pre="172.20." # only needed for network creation

# overlay_network_name="Net-19"

overlay_network_name="ht-test_5"
overlay_network_pre="10.216."


# you only need to create the network once
#create_network()
#sys.exit()

print ("--> start get res:",time.strftime("%Y.%m.%d-%H:%M:%S"))
myres = get_my_reservations(tid)
print ("--> end   get res:",time.strftime("%Y.%m.%d-%H:%M:%S"))

# you can deploy now on this network resources, one by one
#create_minio("vie2")
#create_minio("vie2sbg1")
#create_minio("sbg1_no_apllo")
#create_minio("sbg1")
create_container("no")
#create_k8s()
print ("--> finished:",time.strftime("%Y.%m.%d-%H:%M:%S"))

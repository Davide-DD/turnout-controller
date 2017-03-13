# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import udp


# INIZIO CLASSE
class Turnout(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # DEFINIZIONE INIZIALE DELLA CLASSE!!!!!!!!!!!!!
    def __init__(self, *args, **kwargs):
        super(Turnout, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.MONITORED_PORTS = (1,)
        self.DICTIONARY = {"QoSCheck": (3, 4)}
        self.communications = ""  # sono tutte le cominicazioni registrate dal controller
        self.routes = ""

        # Datapath dello switch sottostante: necessario in quanto nelle modifiche delle funzioni non abbiamo piu' i messaggi dai quali attingere informazioni
        self.my_datapath = None

        # creo la mac address table (vedere sotto per dettagli). Si tratta di un dizionario che poi diventera' un dizionario di dizionari!
        # Cioe' per esempio la mac table finale sara': mac_to_port = {1: {"00:00:00:02": 2, "00:00:00:01": 1}, 2: {"00:00:00:02": 1, "00:00:00:01":2}}

        # a seguire un decoratore che mi dice come gestire la fase openflow della richesta delle funzioni dello switch.
        # Specificamente, dopo aver ricevuto la reply dallo switch, viene aggiunto una table-miss flow, cioe' il comportamento
        # di default per i pacchetti che arrivano allo switch e non hanno una flow (non sanno dove essere rediretti dallo switch).


    # ---------------------METODI UTILI-----------------------------

    # metodo per filtrare mac address in ingresso (=passano dal controller senza conferma dell'utente)
    def filtered_ip(self, dst, eth):
    	# escludo i seguenti mac address dal filtraggio (passano normalmente):
    	#  richieste ARP, Link Layer Discovery Protocol, Multicast (ipv6 e ipv), broadcast address
        return eth.ethertype != 0x0806 and self.lldp_filter(dst) and self.ipv4_multicast_filter(dst) and self.ipv6_multicast_filter(dst) and dst != "ff:ff:ff:ff:ff:ff"

    def lldp_filter(self, addr):
        return addr != "01:80:c2:00:00:0e" and addr != "01:80:c2:00:00:03" and addr != "01:80:c2:00:00:00"

    def ipv6_multicast_filter(self, addr):
        # escludo mac da 33-33-00-00-00-00 a 33-33-FF-FF-FF-FF (vedere http://www.iana.org/assignments/ethernet-numbers/ethernet-numbers.xhtml)
        return addr[:5] != "33:33"

    def ipv4_multicast_filter(self, addr):
        # escludo mac da 01-00-5E-00-00-00 a 01-00-5E-7F-FF-FF (vedere https://technet.microsoft.com/en-us/library/cc957928.aspx)
        # print "valuto %s" % addr
        if addr[:8] != "01:00:5e":
            # print "TRUE"
            return True
        else:
            val = addr[9] == '8' or addr[9] == '9' or addr[9] == 'a' or addr[9] == 'b' or addr[9] == 'c' or addr[9] == 'd' or addr[9] == 'e' or addr[9] == 'f'
            # print "Sono nel secondo ramo: %s" % val
            return val


    def getProtocol(self, pkt):
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        tp = pkt.get_protocol(tcp.tcp)
        port = 0
        if tp:
            port = tp.dst_port
        ud = pkt.get_protocol(udp.udp)
        if ud:
            port = ud.dst_port
        # print "PORTA: %s" % port
        if pkt_ipv4:
            protocol = pkt_ipv4.proto
            if protocol == 1:
                return "ICMP"
            if protocol == 6:
                if port == 80:
                    return "HTTP"
                if port == 443:
                    return "HTTPS"
                return "TCP"
            if protocol == 17:
                if port == 53:
                    return "DNS"
                if port == 67:
                    return "DHCP"
                return "UDP"
        return "Unknown. If you confirm, you will add a general traffic rule (= every type of traffic) between src and dst"


    def getMatch(self, pkt, parser, in_port, dst):
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        tp = pkt.get_protocol(tcp.tcp)
        port = 0
        if tp:
            port = tp.dst_port
        ud = pkt.get_protocol(udp.udp)
        if ud:
            port = ud.dst_port
        # print "PORTA: %s" % port
        if pkt_ipv4:
            protocol = pkt_ipv4.proto
            if protocol == 1:
                return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=0x0800, ip_proto=1)
            if protocol == 6:
                if port == 80:
                    return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=0x0800, ip_proto=6, tcp_dst=80)
                if port == 443:
                    return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=0x0800, ip_proto=6, tcp_dst=443)
                return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=0x0800, ip_proto=6)
            if protocol == 17:
                if port == 53:
                    parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=0x0800, ip_proto=17, udp_dst=53)
                if port == 67:
                    parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=0x0800, ip_proto=17, udp_dst=67)
                return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_type=0x0800, ip_proto=17)
        return parser.OFPMatch(in_port=in_port, eth_dst=dst)


    def getMatchString(self, protocol, parser, in_port, src, dst):
        if protocol == "ICMP":
            return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=0x0800, ip_proto=1)
        if protocol == "HTTP":
            return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=0x0800, ip_proto=6, tcp_dst=80)
        if protocol == "HTTPS":
            return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=0x0800, ip_proto=6, tcp_dst=443)
        if protocol == "TCP":
            return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=0x0800, ip_proto=6)
        if protocol == "DNS":
            return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=0x0800, ip_proto=17, udp_dst=53)
        if protocol == "DHCP":
            return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=0x0800, ip_proto=17, udp_dst=67)
        return parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src, eth_type=0x0800, ip_proto=17)


    def accept(self, msg):

        datapath = servedMessage.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = servedMessage.match['in_port']
        dpid = datapath.id
        pkt = packet.Packet(servedMessage.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        src = eth.src
        dst = eth.dst

        protocol = self.getProtocol(pkt)

        key = "%s %s %s" % (src, dst, protocol)

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        # a seconda del pacchetto in ingresso e del suo tipo di traffico (ICMP, DNS.. ecc) installo una flow appropriata

        match = self.getMatch(pkt, parser, in_port, dst)

        # print(match)

        actions = [parser.OFPActionOutput(out_port)]

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                         actions)]

        if servedMessage.buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=servedMessage.buffer_id,
                                priority=1, match=match,
                                instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=1,
                                match=match, instructions=inst)

        datapath.send_msg(mod)


    def isModified(self, serialized_form):
        key = serialized_form[:serialized_form.find(" function=")]
        return self.routes.find(key) >= 0


    def modifyFunctions(self, mode, src, dst, proto, functions):

        dpid = self.my_datapath.id
        ofproto = self.my_datapath.ofproto
        parser = self.my_datapath.ofproto_parser
        in_ports = []
        out_ports = []

        # Per ogni funzione, bisogna fare due cose:
        # 1) Se un messaggio arriva dalla monitoring port (gia' verificato se siamo qui), dobbiamo passarlo alla porta dove e' connesso il computer di elaborazione
        # 2) Inoltre, il traffico andra' dalla porta da cui e' appena uscito alla porta di uscita del computer di elaborazione, quindi dobbiamo
        # mettere una regola che ridireziona il traffico dalla porta 2 alla porta della successiva funzione e cosi via'
        # Se finiscono le funzioni, l'ultima porta di uscita deve mandare il traffico alla porta dove c'e' S4, se non lo sa, FLOOD

        in_ports.append(self.mac_to_port[dpid][src])

        for fun in functions:
            out_ports.append(self.DICTIONARY[fun][0])
            in_ports.append(self.DICTIONARY[fun][1])

        if dst in self.mac_to_port[dpid]:
            out_ports.append(self.mac_to_port[dpid][dst])
        else:
            out_ports.append(ofproto.OFPP_FLOOD)

        for index in range(len(in_ports)):

            match = self.getMatchString(proto, parser, in_ports[index], src, dst)

            # print(match)

            if mode == 0:

                actions = [parser.OFPActionOutput(out_ports[index])]

                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                     actions)]
                mod = parser.OFPFlowMod(datapath=self.my_datapath, priority=1,
                                        match=match, instructions=inst)
            if mode == 1:
                mod = parser.OFPFlowMod(datapath=self.my_datapath, command=ofproto.OFPFC_DELETE, match=match,
                                                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY)

            self.my_datapath.send_msg(mod)



    #----------------------------GESTIONE DEGLI SWITCH-------------------------------------------
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        # Sfruttiamo l'evento di switch_handler per trovare il datapath dello switch sottostante
        self.my_datapath = ev.msg.datapath

        datapath = self.my_datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Delete all existing rules on the switch
        mod = parser.OFPFlowMod(datapath=datapath, command=ofproto.OFPFC_DELETE, out_port=ofproto.OFPP_ANY,
                                out_group=ofproto.OFPG_ANY)
        datapath.send_msg(mod)

        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=0, match=match, instructions=inst)
        datapath.send_msg(mod)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # con questo metodo raccolgo i packet in in ingresso! poi l'utente li accettera' o meno! Li metto in self.messages

        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        # sintassi di msg:
        # OFPPacketIn(buffer_id=256,cookie=0,data='\x01\x80\xc2\x00\x00\x0e\x8e\xf5\xa4\xcd\xa4j\x88\xcc\x02\x16\x07
        # dpid:0000000000000001\x04\x05\x02\x00\x00\x00\x02\x06\x02\x00x\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        # match=OFPMatch(oxm_fields={'in_port': 2}),reason=0,table_id=0,total_len=60))
        in_port = msg.match['in_port']  # su quale porta dello switch?
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        dpid = datapath.id  # quale switch? torna l'id (es: 1, 2 ecc)
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        src = eth.src  # indirizzo eth src (=mac address)
        dst = eth.dst  # indirizzo eth dst (=mac address)

	#print "DEBUG: Packet in src %s dst %s" % (src, dst)

        # Sotto aggiungiamo le informazioni sullo switch dpid
        # Ad ogni indirizzo MAC associa la porta dello switch
        # se il dpid dello switch non esiste nella mac address table, lo aggiungo con ovviamente la lista di mac e porte settata a {} (vuota).
        # Se lo switch c'era gia', il metodo non fa nulla!
        self.mac_to_port.setdefault(dpid, {})

        # learn a mac address to avoid FLOOD next time.
        # in poche parole associo l'indirizzo mac source con la porta in ingresso.
        # Cioe' associo il dispositivo fisico (mac address) in ingresso con la porta dello switch su cui ascolta!
        # E' come se registrassi chi ha fatto la richiesta! Cioe' associo il mac address alla porta su cui ascolta questo dispositivo!
        # Percio' per esempio un pacchetto di ritorno non dovra' fare flood perche' ora si sa a quale porta e' associato il dispositivo (mac addresss) a cui devo inviare!
        # La tabella sara' fatta come segue (come dicevamo sopra):
        # mac_to_port = {1: {"00:00:00:02": 2, "00:00:00:01": 1}, 2: {"00:00:00:02": 1, "00:00:00:01":2}}

        self.mac_to_port[dpid][src] = in_port

        #print "in_port %s" % in_port

        # RITROVAMENTO PROTOCOLLO
        protocol = self.getProtocol(pkt)

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        # altrimenti per forza la porta di uscita sara' un flood: pacchetto inviato a tutte le porte di uscita.
        # In tal modo spero di raggiungere il mac address della destinazione
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = []


        actions = [parser.OFPActionOutput(out_port)]

        key = "%s %s %s" % (src, dst, protocol)

        if in_port not in self.MONITORED_PORTS:
            if self.filtered_ip(dst, eth):
                self.accept(msg)
            else:
                data = None

                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data

                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                          in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)
        else:
            if self.communications.find(key) < 0 and self.filtered_ip(dst, eth):

                # scrivo in output la sorgente e la destinazione separati da uno spazio
                self.communications += str(src)
                self.communications += ' '
                self.communications += str(dst)
                self.communications += ' '
                self.communications += str(protocol)
                self.communications += '\n'

            if not self.filtered_ip(dst, eth):
                data = None

                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data

                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                          in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)


    #--------------------------------FUNZIONI PRINCIPALI--------------------------------------
    def list_communications(self):
        # prima rest api eseguita: notifica all'utente di una connessione nuova (nuovo packet in da un certo host ad un altro host)

        actual = self.communications[:self.communications.find('\n')]
        self.communications = self.communications[self.communications.find('\n') + 1:]  # elimino da self.communications il valore actual e lo faccio prendendo tutto cio' che c'e' dopo il primo \n 			(= svuoto self.communications)

        return actual


    def list_routes(self):
        # prima rest api eseguita: notifica all'utente di una connessione nuova (nuovo packet in da un certo host ad un altro host)

        return self.routes


    def set_route(self, serialized_form):
        # prima rest api eseguita: notifica all'utente di una connessione nuova (nuovo packet in da un certo host ad un altro host)

        # PARAMETRI DELLA RICHIESTA RICEVUTA
        # trovo la sorgente, la destinazione, il protocollo del traffico ricevuto e le funzioni da associare ad esso

        original_serialized_form = serialized_form

        requestedFunctions = []

        src = serialized_form[:serialized_form.find(" ")]

        serialized_form = serialized_form[(serialized_form.find(" ") + 1):]
        dst = serialized_form[:serialized_form.find(" ")]

        serialized_form = serialized_form[(serialized_form.find(" ") + 1):]
        proto = serialized_form[:serialized_form.find(" ")]

        if serialized_form[serialized_form.find(proto) + len(proto)] != '\n':
            serialized_form = serialized_form[(serialized_form.find(" ") + 1):]
            while serialized_form.find("&") >= 0:
                requestedFunctions.append(serialized_form[serialized_form.find("function=") + 9: serialized_form.find("&")])
                serialized_form = serialized_form[serialized_form.find("&") + 1:]
            if serialized_form:
                requestedFunctions.append(serialized_form[serialized_form.find("function=") + 9:])

        # Preparo una variabile key per agevolare le funzioni successive
        key = src + " " + dst + " " + proto + " "


        # Codice per testare la provenienza della richiesta
        # Difatti, se la richiesta arriva da self.routes.js, significa che c'e' gia' una rotta associata allo stesso traffico settato in precedenza
        # Bisogna controllare 3 situazioni
        # Funzione precedentemente settata ora e' stata disabilitata -> bisogna disattivare la funzione
        # Funzione precedentemente settata continua ad essere settata -> non bisogna fare niente, visto che rimane uguale
        # Funzione precedentemente non settata ora e' stata abilitata -> bisogna attivare la funzione
        # Quindi, quando arriva il serialized_form bisogna:
        # Tirare fuori le funzioni abilitate nel form
        # Confrontarle con quelle gia' abilitate
        # Disabilitare le funzioni che sono in self.routes ma non nel form
        # Abilitare le funzioni che sono nel form ma non in self.routes


        if self.isModified(original_serialized_form):

            activatedFunctions = []
            routeFunctions = self.routes[self.routes.find(key) + len(key):self.routes.find("\n", self.routes.find(key))]
            while routeFunctions.find(",") >= 0:
                activatedFunctions.append(routeFunctions[:routeFunctions.find(",")])
                routeFunctions = routeFunctions[routeFunctions.find(",") + 2:]
            if routeFunctions:
                activatedFunctions.append(routeFunctions)

            differences = False

            for fun in activatedFunctions:
                if fun not in requestedFunctions:
                    differences = True
                    break

            if not differences:
                for fun in requestedFunctions:
                    if fun not in activatedFunctions:
                        differences = True
                        break

            if differences:

                self.modifyFunctions(1, src, dst, proto, activatedFunctions)
                self.modifyFunctions(0, src, dst, proto, requestedFunctions)

                # Nel caso sia stata modificata realmente una route esistente, la stringa che identifica la vecchia route in self.routes non e' piu' valida, quindi viene tolta...
                firstroutes = self.routes[:self.routes.find(src + " " + dst + " " + proto)]
                lastroutes = self.routes[self.routes.find("\n", self.routes.find(src + " " + dst + " " + proto)):]
                self.routes = firstroutes + lastroutes

                #... e sostituita con la nuova in coda a self.routes
                self.routes += src + " " + dst + " " + proto + " "
                for fun in requestedFunctions:
                    self.routes += fun + ", "
                if len(requestedFunctions) > 0:
                    self.routes = self.routes[:-2] + "\n"
                else:
                    self.routes = self.routes[:-1] + " " + '\n'
        else:

            self.modifyFunctions(0, src, dst, proto, requestedFunctions)

            # Mentre se non c'era una route precedente, mi limito ad aggiungere la nuova route in coda a self.routes
            self.routes += src + " " + dst + " " + proto + " "
            for fun in requestedFunctions:
                self.routes += fun + ", "
            if len(requestedFunctions) > 0:
                self.routes = self.routes[:-2] + "\n"
            else:
                self.routes = self.routes[:-1] + " " + "\n"


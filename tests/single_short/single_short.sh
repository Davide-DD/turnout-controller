bin/bash
if test `whoami` != root; then 
	echo "Permesso negato. Avviare lo script come root!"
	exit 1
fi

if test "$1" == 'c'; then
	echo "Pulizia iniziata: "
	mn -c
	echo -n "Eliminazione dei namespace: "
	for i in $(seq 1 2)
	do
		ip netns del h"$i"
	done
	echo "fatto!"
	exit 2
fi

ip netns add h1
ip netns add h2
echo "Host disponibili: " 
ip netns list
echo "Creazione switch s1.." 
ovs-vsctl add-br s1 
echo "Creazione collegamento tra switch e h1" 
ip link add h1-eth0 type veth peer name s1-eth1
ip link set h1-eth0 netns h1
ovs-vsctl add-port s1 s1-eth1
echo "Creazione collegamento tra switch e h2" 
ip link add h2-eth0 type veth peer name s1-eth2
ip link set h2-eth0 netns h2
ovs-vsctl add-port s1 s1-eth2
echo "Creazione corto circuito (s1-eth3 e s1-eth4)" 
ip link add s1-eth3 type veth peer name s1-eth4
ovs-vsctl add-port s1 s1-eth4
ovs-vsctl add-port s1 s1-eth3


for i in $(seq 1 2)
do
   echo "Aggiunta indirizzo a h$i.."
   ip netns exec h"$i" ifconfig h"$i"-eth0 10.0.0."$i"
done

echo "Configurazione interfacce.."
for i in $(seq 1 4)
do
   ifconfig s1-eth"$i" up
   ifconfig s1-eth"$i" 0
done
ifconfig s1 up

echo "Aggiunta controller" 
ovs-vsctl set-controller s1 tcp:127.0.0.1:6633
echo "Situazione openvswith:" 
ovs-vsctl show
#echo "Configurazione stp.."
#ovs-vsctl set Bridge s1 rstp_enable=true
echo "Stoppo i flood dall'interfaccia cortocircuitata.."
ovs-ofctl mod-port s1 3 no-flood
ovs-ofctl mod-port s1 4 no-flood
echo "TUTTO FATTO!"




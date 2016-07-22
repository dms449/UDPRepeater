from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

class receiver(DatagramProtocol):
    def datagramReceived(self, datagram, addr):
        print(datagram.decode())

UDP_IP1 = 'localhost'
UDP_IP2 = 'localhost'

# UDP_PORT1 = 5005
UDP_PORT2 = 5007

# reactor.listenUDP(5005,receiver())
reactor.listenUDP(UDP_PORT2,receiver())
reactor.run()
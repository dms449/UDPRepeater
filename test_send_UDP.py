import socket
import time

UDP_IP1 = 'localhost'
UDP_IP2 = 'localhost'

UDP_PORT1 = 5005
UDP_PORT2 = 5006

sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP


for i in range(100):
    message1 = 'Sock1, Test Message: {}'.format(i)
    sock1.sendto(message1.encode(),(UDP_IP1,UDP_PORT1))
    print('sent message {}, to socket 1'.format(i))
    time.sleep(0.5)

    message2 = 'Sock2, Test Message: {}'.format(i)
    sock2.sendto(message2.encode(),(UDP_IP2,UDP_PORT2))
    print('sent message {}, to socket 1'.format(i))
    time.sleep(0.5)
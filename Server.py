import threading
import socket
import sys
import struct
import random

lock = threading.Lock()
def checkchecksum(checksum,data):
    tempdata=0
    newchcksum = 0
    i=0
    n = len(data) % 2
    for i in range(0, len(data) - n, 2):
        tempdata += ord(data[i]) + (ord(data[i + 1]) << 8)
    if n:
        tempdata += ord(data[i + 1])
    while tempdata >> 16:
        # sumcarry = sumcarry + tempdata
        newchcksum = (tempdata & 0xffff) + (tempdata >> 16)
        break
    result = newchcksum & checksum
    if result==0:
        return True
    else:
        return False

def makeacks(seqnum):
    sequence = struct.pack('=I', seqnum)
    paddingzeros=struct.pack('=H',0)
    ackindicator=struct.pack('=H',43690)
    ackpacket = sequence+paddingzeros+ackindicator
    return ackpacket

def main():
    port = int(sys.argv[1])
    filename = sys.argv[2]
    prob= float(sys.argv[3])
    buffer = {}
    file =open(filename,'a')
    file.flush()
    serversockt = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
    serversockt.bind(('', socket.htons(port)))
    while True:
        receivepacket, clientaddr=serversockt.recvfrom(4096)
        headerpacket=receivepacket[0:8]
        datapacket=receivepacket[8:]
        seqnum=struct.unpack("=I",headerpacket[0:4])
        seqnum=int(seqnum[0])
        checksum =struct.unpack("=H",headerpacket[4:6])
        checksum=int(checksum[0])
        dataidentifier =struct.unpack("=H",headerpacket[6:8])
        dataidentifier=int(dataidentifier[0])
        data = datapacket.decode("ISO-8859-1","ignore")
        randomprob=random.uniform(0,1)
        if randomprob > prob:
            checksumflag = checkchecksum(checksum,data)
            if dataidentifier== 21845 and checksumflag==True:
                if data !="00000end111111":
                    ackpacket=makeacks(seqnum)
                    buffer[seqnum]=data
                    file.write(buffer[seqnum])
                    serversockt.sendto(ackpacket, clientaddr)
                else:
                    break
        else:
            print("PACKET LOST SEQNUM %d" %seqnum)
    file.close()
    print("File received successfully")
    #serversockt.close()

main()

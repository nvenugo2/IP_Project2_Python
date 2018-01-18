import os
import threading
import socket
import sys
import struct
import time
lock = threading.Lock()

class clientreceiver(threading.Thread):
    def __init__(self, hostname, port, clientsocket, packet, seqnum):
        threading.Thread.__init__(self)
        self.port = port
        self.hostname = hostname
        self.clientsocket = clientsocket
        self.packet = packet
        self.sequencenum = seqnum
        self.start()

    def retransmit(self):
        self.clientsocket.sendto(self.packet, (self.hostname, socket.htons(self.port)))
        self.run()

    def run(self):
        try:
            self.clientsocket.settimeout(0.2)
            ackrxd, serveraddr = self.clientsocket.recvfrom(4096)
            sequenceno = struct.unpack("=I", ackrxd[0:4])
            sequenceno=int(sequenceno[0])
            paddingbits = struct.unpack("=H", ackrxd[4:6])
            paddingbits=int(paddingbits[0])
            ackidentifier = struct.unpack("=H", ackrxd[6:])
            ackidentifier=int(ackidentifier[0])
            if paddingbits==0 and ackidentifier==43690:
                if self.sequencenum == sequenceno:
                    #print("ACK received for Packet with SEQ{}".format(self.sequencenum))
                    if (sequenceno == 4294967295):
                        sequenceno = 0
                else:
                    self.retransmit()
            else:
                #print("The packet received is not an ACK Packet")
                self.retransmit()

        except socket.timeout:
            self.retransmit()


class clientsender(threading.Thread):
    def __init__(self, hostname, port, filename, MSS, clientsocket):
        threading.Thread.__init__(self)
        self.port = port
        self.hostname = hostname
        self.clientsocket = clientsocket
        self.filename = filename
        self.MSS = MSS
        self.start()

    def dochecksum(self, filesend):
        sumcarrynew = 0
        tempdata=0
        i=0
        n = len(filesend) % 2
        for i in range(0, len(filesend)-n, 2):
            tempdata += ord(filesend[i]) + (ord(filesend[i + 1]) << 8)
        if n:
            tempdata+=ord(filesend[i+1])
        while tempdata >> 16:
            #sumcarry = sumcarry + tempdata
            sumcarrynew = (tempdata & 0xffff) + (tempdata >> 16)
            break
        return ~sumcarrynew & 0xffff

    def makepacket(self, filesend, seqnum):
        checksum = 0
        indicator = 0
        data = filesend.encode('ISO-8859-1','ignore')
        filesend = data.decode('ISO-8859-1','ignore')
        # encoding and packing since python 3.X accepts only byte like objects in sendto()
        # = is for native standardized byte ordering
        # I = unsigned int(32 bit) H= unsigned short (16 bits)
        sequence = struct.pack('=I', seqnum)
        checksum = struct.pack('=H', self.dochecksum(filesend))
        indicator = struct.pack('=H', 21845)
        packet = sequence + checksum + indicator + filesend.encode('ISO-8859-1', 'ignore')
        return packet

    def rdt_send(self):
        file = open(self.filename, 'r')
        filebyte = True
        addbytes = ""
        sequencenum = 0
        count = 0
        while filebyte:
            filebyte = file.read(1)
            addbytes += filebyte
            if len(addbytes) == self.MSS or (not filebyte):
                lock.acquire()
                while(len(addbytes)<self.MSS):
                    addbytes+=" "
                packet = self.makepacket(addbytes, sequencenum)
                self.clientsocket.sendto(packet, (self.hostname, socket.htons(self.port)))
                ackrxvr = clientreceiver(self.hostname, self.port, self.clientsocket, packet, sequencenum)
                ackrxvr.join()
                lock.release()
                if (sequencenum == 4294967295):
                    sequencenum = 0
                else:
                    sequencenum += 1
                addbytes = ""
        addbytes = "00000end111111"
        lock.acquire()
        packet = self.makepacket(addbytes, sequencenum)
        self.clientsocket.sendto(packet, (self.hostname, socket.htons(self.port)))
        lock.release()
        

    def run(self):
        starttime = time.time()
        self.rdt_send()
        endtime = time.time()
        totaltime = endtime - starttime
        print("Total time for host %s is %.4f sec" % (self.hostname, totaltime))
        time.sleep(10)


def main():
    hostrx = sys.argv[1:-3]
    port = int(sys.argv[-3])
    filename = sys.argv[-2]
    MSS = int(sys.argv[-1])
    clientsockt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientsockt.bind(('', port))
    for i in range(0, len(hostrx)):
        filesender = clientsender(hostrx[i], port, filename, MSS, clientsockt)

if __name__=='__main__':
    main()

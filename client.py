import socket
import sys
import pickle
import time
import threading
import struct

history={} #new dictionary for the packet history based on its seqNum
curNum = 1; #current seq Number

address = ('127.0.0.1',8080)
filename = 'download.jpg'
data = ''
packet = True
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
feedTime = 0.0
timer = None

#server data
seqNum = None
tsend = None
RTT = None
done = False

trecv = 0
#XrecvCount = 0 #packets per RTT
Xrecv = 0
p = 0

elapsed = 0.0
t1 = None

def collect(seqNum,s):
    global data,curNum,history
    if seqNum==curNum: #if its the same number then
        data += s #add the data
        curNum += 1 #and increase the sequence number
    else: history[seqNum]=s #added information to dictionary
    while curNum in history: #if there is something in the history with the next number then
        data+=history[curNum] #access the data inside the history

#def calcXrecv():
    

def receive():
    global RTT, seqNum, tsend, trecv, XrecvCount, Xrecv, elapsed, t1, packet, address, data, sock, done, timer
    while True and not done:
        if RTT and RTT != 0:
            while elapsed < 1.0:
                packet = sock.recv(1024)
                trecv = time.time()
                if not packet or packet == '':
                    #print 'break'
                    done = True
                    break
                #print packet              
                seqNum = int(struct.unpack('f',packet[0:4])[0])
                tsend = struct.unpack('f',packet[4:8])[0]
                RTT = struct.unpack('f',packet[8:12])[0]
                s = packet[12:]
                #collect(seqNum,s)
                data +=s
                if not t1:
                    t1 = time.time()
                Xrecv += 1
                elapsed += (time.time() - t1)
                t1 = time.time()
            print Xrecv
            elapsed = 0.0
            t1 = None
            Xrecv = 0
        else:
            packet = sock.recv(1024)
            #print packet
            trecv = time.time()
            seqNum = int(struct.unpack('f',packet[0:4])[0])
            tsend = struct.unpack('f',packet[4:8])[0]
            RTT = struct.unpack('f',packet[8:12])[0]
            s = packet[12:]
            feedTime = RTT
            #collect(seqNum,s)
            data += s
            t1 = None    
            timer = threading.Timer(RTT, send)
            timer.start()
        if not packet or packet == '':
            done = True
            break

def send():
    #print "send"
    global timer
    if timer:
        timer.cancel()
    global Xrecv, trecv, RTT, done
    sock.sendto(struct.pack('f',trecv)+struct.pack('f',time.time()-trecv)+struct.pack('f',Xrecv)+struct.pack('f',p),address)
    timer = threading.Timer(RTT, send)
    if not done:
        timer.start()

cmd = raw_input('Type \"start\" to begin downloading\n')
if cmd == 'start':
    sock.sendto(str(time.time()),address)
    
f = open(filename,'wb')

while 1:
    receive()
    if done:
        break

print 'Downloading File:'
f.write(data)
print 'Download finished'
f.close()

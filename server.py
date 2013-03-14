import socket
import sys
import thread
import time
import os
import struct
import array
import pickle
import math
import threading

address = ('127.0.0.1',8080)
wait = 1 #sends every 1 second
rate = 1 #1 packet/second
blocksize = 1000
filename = 'Red_Skull_HIGH.jpg' 
recvLimit = None
tMBI = 64
Xrecvset = [2 ** 32, None]
tld = 0 #time last doubled
initRate = 0
done = False

#Server info
seqNum = 0 #sequence number
timeStamp = None #timestamp
RTT = 0 #Round trip time
Rsample = None #R sample
nft = 2.0 #No feedback timer
timer = None

#client info
tRecv = None
tDelay = None
Xrecv = None
p = None

formula = True

def updateData():
    global seqNum, timeStamp, RTT, tRecv, tDelay, Xrecv, p
    updateRTT()
    #updateNFT()
    updateRate()
    seqNum += 1
    
def updateRTT():
    global RTT, Rsample, tRecv, tDelay, rate, tld, initRate
    if tRecv and tDelay:
        #print time.time()
        Rsample = time.time() - tRecv - tDelay
        if RTT == 0:
            RTT = Rsample
            tld = time.time()
            initRate = min(4 * 1000, max(2 * 1000, 4380)) / RTT
            rate = int(math.floor(initRate / 1000))
        else:
            RTT = .9 * RTT + (1-.9) * Rsample
    else:
        RTT = 1.0
            
def updateNFT():
    global nft, RTT, rate
    nft = max(4 * RTT, 2 * 1000/(rate*1000))
    
def updateRate():
    global recvLimit, tMBI, Xrecv, Xrecvset, p, rate, tld, initRate, RTT
    if not Xrecvset[1] and Xrecv:
        Xrecvset[1] = Xrecv * 1000
    elif Xrecv:
        Xrecvset[0] = Xrecvset[1]
        Xrecvset[1] = Xrecv * 1000
    recvLimit = 2 * max(Xrecvset[0], Xrecvset[1])
    if p > 0:
        XBps = updateBPS()
        X = max(min(XBps, recvLimit), (1000/tMBI))
        rate = int(math.floor(X / 1000))
    elif time.time() - tld >= RTT:
        X = max(min(2*rate*1000, recvLimit), initRate)
        rate = int(math.floor(X / 1000))
        tld = time.time()
        
def updateBPS():
    global RTT, p
    if p != 0:
        XBps = 1000 / (RTT * (math.sqrt(2 * p / 3) + 12 * math.sqrt(3 * p / 8) * p * (1 + 32 * p ** 2)))
        return XBps
        
def nftExpire():
    global timer
    xrecv = max(Xrecvset[0], Xrecvset[1])
    XBps = updateBPS()
    if RTT == 0:
        rate = max(int(math.floor(rate/2)), 1000/tMBI)
    elif p == 0:
        rate = max(int(math.floor(rate/2)), 1000/tMBI)    
    elif XBps > (2*xrecv):
        updateLimits(xrecv)
    else:
        updateLimits(XBps/2)
    timer = threading.Timer(max(4*RTT,2*1/rate), nftExpire)
    
def updateLimits(timerLimit):
    global Xrecvset
    if timerLimit < (1000/tMBI):
        timerLimit = 1000/tMBI
    Xrecvset[0] = timerLimit
    Xrecvset[1] = None
    updateRate()

def send(client,address):
    global done, rate, RTT, seqNum
    start=0
    f = open(filename, 'rb').read()
    while True:
        if not formula:
            rate = 25
            seqNum = 1
            RTT = 1.0
        for i in range(0,rate):
            print str(seqNum)+","+str(rate)
            if filesize - start < blocksize: 
                end = filesize-start
            else: 
                end = blocksize
            if formula:
                updateData()
            server.sendto(struct.pack('i',seqNum)+struct.pack('f',time.time())+struct.pack('f',RTT)+f[start:start+end],address)
            start+=blocksize
        os.system('clear')
        print 'Uploaded: '+str((100*start)//filesize) +'%'
        if end < blocksize: 
            break
        time.sleep(wait)
    server.sendto('',address)
    print str(address)+' has received all the data'
    done = True
    
def receive():
    global server, tRecv, tDelay, Xrecv, p, timer, nft
    while 1:
        client = server.recv(1024)
        if timer:
            timer.cancel()
            timer = threading.Timer(nft, nftExpire)
        else:
            updateNFT()
            timer = threading.Timer(nft, nftExpire)
        tRecv = struct.unpack('f',client[0:4])[0]
        tDelay = struct.unpack('f',client[4:8])[0]
        Xrecv = int(struct.unpack('f',client[8:12])[0])
        p = int(struct.unpack('f',client[12:16])[0])
        if done:
            break
    
filesize = os.path.getsize(filename);
server = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
server.bind(address)

while True:
    global formula
    print "Would you like to apply the dumb formula from the pdf? yes/no"
    formula = raw_input() == "yes"
    print 'Waiting for clients'
    
    (client,address) = server.recvfrom(1024)
    if client:        
        print 'Client has requested download'
    
    thread.start_new_thread(send,(client,address))
    thread.start_new_thread(receive,())
    
    str = raw_input('Type \"exit\" to quit\n')
    if str == 'exit':
        break
server.close()
input()


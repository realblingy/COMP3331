import sys
from socket import *
import threading
from ptp import createSegement, senderLogFileEntry
from threadingManagers import SenderManager

if len(sys.argv) != 9:
    print("""Usage python sender.py <receiver_host_ip> <receiver_port> <FileToSend.txt> <MWS> <MSS> <timeout> <pdrop> <seed>""")
    sys.exit();

serverIP = '127.0.0.1'
serverPort = 12000
receiverIP = sys.argv[1]
receiverPort = int(sys.argv[2])
fileToSend = sys.argv[3]
MWS = int(sys.argv[4])
MSS = int(sys.argv[5])
timer = int(sys.argv[6])
pdrop = float(sys.argv[7])
seedNumber = int(sys.argv[8])


clientAddress = (receiverIP, receiverPort)

# This will control the sending of messages
sManager = SenderManager(fileToSend, MSS, MWS, seedNumber, pdrop)
sManager.initializeSocket(serverIP, serverPort, timer)

# Sends SYN segment
synSegment = createSegement(
    sManager.sequenceNumber,
    syn=1
)

sManager.sendSegment(synSegment, clientAddress, 0, 'S')

# Receives SYN-ACK segement
SynAcksegment = sManager.receiveSegment('SA')

# Sends ACK segment send an acknowledgement
if SynAcksegment['syn'] == 1 and SynAcksegment['ack'] == 1:

    sManager.incrementSequenceNumber(1)
    sManager.setAcknowledgementNumber(
        int(SynAcksegment['sequenceNumber']) + 1
    )

    ackSegment = createSegement(
        sManager.sequenceNumber,
        sManager.acknowledgementNumber,
        ack = 1
    )

    sManager.sendSegment(
        ackSegment,
        clientAddress,
        0,
        'A'
    )

    def sendingPLModule():
        while (sManager.receivedAcks < len(sManager.segmentsToSend)):
            sManager.sendPLSegment(clientAddress)

    def receivingPLModule():
        while (sManager.receivedAcks < len(sManager.segmentsToSend)):
            sManager.receivePLSegment()

    sendingThread = threading.Thread(target=sendingPLModule)
    receivingThread = threading.Thread(target=receivingPLModule)

    sendingThread.start()
    receivingThread.start()

    sendingThread.join()
    receivingThread.join()

    finSegment = createSegement(
        sManager.sequenceNumber,
        sManager.acknowledgementNumber,
        fin=1
    )

    # Sends fin segment
    sManager.sendSegment(finSegment, (receiverIP, receiverPort), 0, 'F')

    segment = sManager.receiveSegment('A')

    ackSegment = createSegement(
        sManager.sequenceNumber,
        sManager.acknowledgementNumber,
        ack = 1
    )

    # Checks if fin-ack segment was received
    if segment["fin"] == 1 and segment["ack"] == 1:

        sManager.sendSegment(ackSegment, (receiverIP, receiverPort), 0, 'A')

    sManager.closeSocket()
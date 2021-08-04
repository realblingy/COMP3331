import sys
from socket import *
from ptp import createSegement
import json
import random
import time

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

sequenceNumber = 1000
acknowledgementNumber = None
segmentsToSend = []
segmentsToSendIndex = 0

random.seed(seedNumber)

# Creates segments to be sent
with open(fileToSend, "r") as f:
    payload = f.read(MSS)
    while payload != "":
        segmentsToSend.append(payload)
        payload = f.read(MSS)
    f.close()


senderSocket = socket(AF_INET, SOCK_DGRAM)
senderSocket.bind((serverIP, serverPort))
senderSocket.settimeout(timer / 1000)

synSegment = createSegement(
    sequenceNumber,
    syn=1
)

senderSocket.sendto(synSegment, (receiverIP, receiverPort))

# Receives SYN-ACK segement
message, senderAddress = senderSocket.recvfrom(2048)
segment = json.loads(message.decode('utf-8'))

# Sends ACK segment
if segment['syn'] == 1 and segment['ack'] == 1:
    sequenceNumber += 1
    acknowledgementNumber = int(segment['sequenceNumber']) + 1

    ackSegment = createSegement(
        sequenceNumber,
        acknowledgementNumber,
        ack = 1
    )

    senderSocket.sendto(ackSegment, (receiverIP, receiverPort))

    print("Initial sequence number: " + str(sequenceNumber))
    print()
    print("Initial acknowledgement number: " + str(acknowledgementNumber))

    # Determines whether a packet is lost
    packetLoss = False
    # Sequence number of loss packet
    packetLossSequence = None
    # Start pointer of window
    windowStart = 0
    # End pointer of window
    windowEnd = min(MWS, len(segmentsToSend))

    # Sends PTP segments with data
    while segmentsToSendIndex < len(segmentsToSend):
        segmentPayload = segmentsToSend[segmentsToSendIndex]
        PTPsegement = createSegement(
            sequenceNumber,
            acknowledgementNumber,
            payload=segmentPayload,
            length=len(segmentPayload)
        )

        # PL modules

        # If we do not drop the packet, we move the window
        if (random.random() > pdrop): 
            senderSocket.sendto(PTPsegement, (receiverIP, receiverPort))
            if packetLoss == False:
                windowStart += 1
                packetLossSequence = sequenceNumber
                windowEnd = min(windowEnd + 1, len(segmentsToSend))
        else:
            if packetLoss == False:
                packetLossSequence = sequenceNumber
                packetLoss = True

        sequenceNumber += len(segmentPayload)
        print(PTPsegement)
        print()

        try:
            message, senderAddress = senderSocket.recvfrom(2048)
            segmentsToSendIndex += 1
            sequenceNumber += len(payload)
        except:
            segmentsToSendIndex = windowStart
            packetLoss = False
            sequenceNumber = packetLossSequence

finSegment = createSegement(
    sequenceNumber,
    acknowledgementNumber,
    fin=1
)

# Sends fin segment
senderSocket.sendto(finSegment, (receiverIP, receiverPort))

message, senderAddress = senderSocket.recvfrom(2048)
segment = json.loads(message.decode('utf-8'))

ackSegment = createSegement(
    sequenceNumber,
    acknowledgementNumber,
    ack = 1
)

# Checks if fin-ack segment was received
if segment["fin"] == 1 and segment["ack"] == 1:
    senderSocket.sendto(ackSegment, (receiverIP, receiverPort))


print("Closing socket")  
senderSocket.close()
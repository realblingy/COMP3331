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

# print("Split file into segments")
# print(segmentsToSend)

senderSocket = socket(AF_INET, SOCK_DGRAM)
senderSocket.bind((serverIP, serverPort))

print('PTP client is ready to send')

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

    segmentsSent = 0
    oldestUnack = None

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
        if (random.random() > pdrop): 
            senderSocket.sendto(PTPsegement, (receiverIP, receiverPort))
            segmentsSent += 1
            sequenceNumber += len(segmentPayload)
            segmentsToSendIndex += 1
            receivedAcks = 0
        else:
            if oldestUnack is None:
                oldestUnack = segmentsToSendIndex
            elif segmentsToSendIndex < oldestUnack:  
                time.sleep(timer/1000)
                segmentsToSend = oldestUnack
                oldestUnack = None
                continue

        # If we reached the maximum window size, we wait for all ACKs
        if segmentsToSendIndex % (MWS) == 0:
            while receivedAcks < MWS:
                message, senderAddress = senderSocket.recvfrom(2048)

                ackSegment = json.loads(message.decode('utf-8'))
                print("Received segemnet")
                print(ackSegment)
                print()

                if ackSegment['ack'] == 1:
                    receivedAcks += 1;
            segmentsSent = 0
        elif segmentsToSendIndex == len(segmentsToSend):
            while receivedAcks < segmentsSent:
                message, senderAddress = senderSocket.recvfrom(2048)

                ackSegment = json.loads(message.decode('utf-8'))
                print("Received segemnet")
                print(ackSegment)
                print()

                if ackSegment['ack'] == 1:
                    receivedAcks += 1;

# Closing connection

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
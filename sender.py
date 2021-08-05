import sys
from socket import *
from ptp import createSegement, senderLogFileEntry
import json
import random
import time
from threadingManagers import SenderManager

startTime = time.time()

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

# Opens the log file
senderLogFile = open("Sender_log.txt", "w")
senderLogActions = ""

sequenceNumber = 1000
acknowledgementNumber = 0
segmentsToSend = []
segmentsToSendIndex = 0

sManager = SenderManager()

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

# Sends SYN segment
synSegment = createSegement(
    sequenceNumber,
    syn=1
)

senderSocket.sendto(synSegment, (receiverIP, receiverPort))

senderLogActions += senderLogFileEntry("snd", round(time.time() - startTime, 6), "S", sequenceNumber, 0, acknowledgementNumber)

# Receives SYN-ACK segement
message, senderAddress = senderSocket.recvfrom(2048)
segment = json.loads(message.decode('utf-8'))

# Sends ACK segment
if segment['syn'] == 1 and segment['ack'] == 1:

    sequenceNumber += 1
    acknowledgementNumber = int(segment['sequenceNumber']) + 1

    senderLogActions += senderLogFileEntry("rcv", round(time.time() - startTime, 6), "SA", segment['sequenceNumber'], 0, segment['acknowledgementNumber'])

    ackSegment = createSegement(
        sequenceNumber,
        acknowledgementNumber,
        ack = 1
    )

    senderSocket.sendto(ackSegment, (receiverIP, receiverPort))

    senderLogActions += senderLogFileEntry("snd", round(time.time() - startTime, 6), "A", sequenceNumber, 0, acknowledgementNumber)

    # print("Initial sequence number: " + str(sequenceNumber))
    # print()
    # print("Initial acknowledgement number: " + str(acknowledgementNumber))

    # Determines whether a packet is lost
    packetLoss = False
    # Sequence number of loss packet
    packetLossSequence = None
    # Start pointer of window
    windowStart = 0
    # End pointer of window
    windowEnd = min(MWS, len(segmentsToSend))


    # FOR LOG FILE
    dataTransferredBits = 0
    dataSegmentsSent = 0
    packetsDropped = 0
    retransmittedSegments = 0
    dupAcksReceived = 0

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
                senderLogActions += senderLogFileEntry("snd", round(time.time() - startTime, 6), "D", sequenceNumber, len(segmentPayload), acknowledgementNumber)
        else:
            if packetLoss == False:
                packetLossSequence = sequenceNumber
                packetLoss = True
                senderLogActions += senderLogFileEntry("drop", round(time.time() - startTime, 6), "D", sequenceNumber, len(segmentPayload), acknowledgementNumber)

        sequenceNumber += len(segmentPayload)
        # print(PTPsegement)
        # print()

        try:
            message, senderAddress = senderSocket.recvfrom(2048)
            ackSegment = json.loads(message.decode('utf-8'))
            senderLogActions += senderLogFileEntry("rcv", round(time.time() - startTime, 6), "A", ackSegment['sequenceNumber'], 0, ackSegment['acknowledgementNumber'])
            segmentsToSendIndex += 1
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
senderLogActions += senderLogFileEntry("snd", round(time.time() - startTime, 6), "F", sequenceNumber, 0, acknowledgementNumber)

message, senderAddress = senderSocket.recvfrom(2048)
segment = json.loads(message.decode('utf-8'))

ackSegment = createSegement(
    sequenceNumber,
    acknowledgementNumber,
    ack = 1
)

# Checks if fin-ack segment was received
if segment["fin"] == 1 and segment["ack"] == 1:

    senderLogActions += senderLogFileEntry("rcv", round(time.time() - startTime, 6), "FA", segment['sequenceNumber'], 0, segment['acknowledgementNumber'])
    senderSocket.sendto(ackSegment, (receiverIP, receiverPort))
    senderLogActions += senderLogFileEntry("snd", round(time.time() - startTime, 6), "A", sequenceNumber, 0, acknowledgementNumber)

senderLogFile.write(senderLogActions)

senderLogFile.close()

# print("Closing socket")  
senderSocket.close()
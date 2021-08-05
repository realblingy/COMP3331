import sys
from socket import *
from ptp import createSegement, senderLogFileEntry
# import json
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


clientAddress = (receiverIP, receiverPort)

# Opens the log file
# senderLogFile = open("Sender_log.txt", "w")
# senderLogActions = ""

# sequenceNumber = 1000
# acknowledgementNumber = 0
segmentsToSend = []
segmentsToSendIndex = 0

sManager = SenderManager()

random.seed(seedNumber)

# Creates segments to be sent
with open(fileToSend, "r") as f:
    payload = f.read(MSS)
    while payload != "":
        # sManager.addSegmentToSend(payload)
        segmentsToSend.append(payload)
        payload = f.read(MSS)
    f.close()


# senderSocket = socket(AF_INET, SOCK_DGRAM)
# senderSocket.bind((serverIP, serverPort))
# senderSocket.settimeout(timer / 1000)

sManager.initializeSocket(serverIP, serverPort, timer)

# Sends SYN segment
synSegment = createSegement(
    sManager.sequenceNumber,
    syn=1
)

# senderSocket.sendto(synSegment, (receiverIP, receiverPort))
sManager.sendSegment(synSegment, clientAddress)

sManager.addLogAction(
    senderLogFileEntry(
        "snd",
        round(time.time() - startTime, 6),
        "S",
        sManager.sequenceNumber,
        0,
        sManager.acknowledgementNumber
    )
)

# Receives SYN-ACK segement
# message, senderAddress = senderSocket.recvfrom(2048)
# segment = json.loads(message.decode('utf-8'))
SynAcksegment = sManager.receiveSegment()

# Sends ACK segment
if SynAcksegment['syn'] == 1 and SynAcksegment['ack'] == 1:

    # sequenceNumber += 1
    sManager.incrementSequenceNumber(1)
    sManager.setAcknowledgementNumber(
        int(SynAcksegment['sequenceNumber']) + 1
    )
    # acknowledgementNumber = int(SynAcksegment['sequenceNumber']) + 1

    sManager.addLogAction(
        senderLogFileEntry(
            "rcv",
            round(time.time() - startTime, 6),
            "SA",
            SynAcksegment['sequenceNumber'],
            0,
            SynAcksegment['acknowledgementNumber']
        )
    )

    ackSegment = createSegement(
        sManager.sequenceNumber,
        sManager.acknowledgementNumber,
        ack = 1
    )

    sManager.sendSegment(
        ackSegment,
        clientAddress
    )
    # senderSocket.sendto(ackSegment, (receiverIP, receiverPort))

    sManager.addLogAction(
        senderLogFileEntry(
            "snd",
            round(time.time() - startTime, 6),
            "A",
            sManager.sequenceNumber,
            0,
            sManager.acknowledgementNumber
        )
    )

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
            sManager.sequenceNumber,
            sManager.acknowledgementNumber,
            payload=segmentPayload,
            length=len(segmentPayload)
        )

        # PL modules

        # If we do not drop the packet, we move the window
        if (random.random() > pdrop): 
            sManager.sendSegment(PTPsegement, (receiverIP, receiverPort))
            if packetLoss == False:
                windowStart += 1
                packetLossSequence = sManager.sequenceNumber
                windowEnd = min(windowEnd + 1, len(segmentsToSend))
                sManager.addLogAction(
                    senderLogFileEntry(
                        "snd",
                        round(time.time() - startTime, 6),
                        "D",
                        sManager.sequenceNumber,
                        len(segmentPayload),
                        sManager.acknowledgementNumber
                    )
                )
        else:
            if packetLoss == False:
                packetLossSequence = sManager.sequenceNumber
                packetLoss = True
                sManager.addLogAction(
                    senderLogFileEntry(
                        "drop",
                        round(time.time() - startTime, 6),
                        "D",
                        sManager.sequenceNumber,
                        len(segmentPayload),
                        sManager.acknowledgementNumber
                    )
                )

        sManager.incrementSequenceNumber(len(segmentPayload))
        # print(PTPsegement)
        # print()

        try:
            # message, senderAddress = senderSocket.recvfrom(2048)
            ackSegment = sManager.receiveSegment()
            sManager.addLogAction(
                senderLogFileEntry(
                    "rcv",
                    round(time.time() - startTime, 6),
                    "A",
                    ackSegment['sequenceNumber'],
                    0,
                    ackSegment['acknowledgementNumber']
                )
            )
            segmentsToSendIndex += 1
        except:
            segmentsToSendIndex = windowStart
            packetLoss = False
            sManager.sequenceNumber = packetLossSequence

finSegment = createSegement(
    sManager.sequenceNumber,
    sManager.acknowledgementNumber,
    fin=1
)

# Sends fin segment
sManager.sendSegment(finSegment, (receiverIP, receiverPort))
sManager.addLogAction(
    senderLogFileEntry(
        "snd",
        round(time.time() - startTime, 6),
        "F",
        sManager.sequenceNumber,
        0,
        sManager.acknowledgementNumber
    )
)

segment = sManager.receiveSegment()

ackSegment = createSegement(
    sManager.sequenceNumber,
    sManager.acknowledgementNumber,
    ack = 1
)

# Checks if fin-ack segment was received
if segment["fin"] == 1 and segment["ack"] == 1:

    sManager.addLogAction(
        senderLogFileEntry(
            "rcv",
            round(time.time() - startTime, 6),
            "FA",
            segment['sequenceNumber'],
            0,
            segment['acknowledgementNumber']
        )
    )
    sManager.sendSegment(ackSegment, (receiverIP, receiverPort))
    sManager.addLogAction(
        senderLogFileEntry(
            "snd",
            round(time.time() - startTime, 6),
            "A",
            sManager.sequenceNumber,
            0,
            sManager.acknowledgementNumber
        )
    )

# senderLogFile.write(senderLogActions)

# senderLogFile.close()

# print("Closing socket")  
sManager.closeSocket()
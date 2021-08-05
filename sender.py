import sys
from socket import *
import threading
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

sManager = SenderManager(fileToSend, MSS, MWS, seedNumber, pdrop)

random.seed(seedNumber)

sManager.initializeSocket(serverIP, serverPort, timer)

# Sends SYN segment
synSegment = createSegement(
    sManager.sequenceNumber,
    syn=1
)

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
SynAcksegment = sManager.receiveSegment()

# Sends ACK segment
if SynAcksegment['syn'] == 1 and SynAcksegment['ack'] == 1:

    sManager.incrementSequenceNumber(1)
    sManager.setAcknowledgementNumber(
        int(SynAcksegment['sequenceNumber']) + 1
    )

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

    # FOR LOG FILE
    dataTransferredBits = 0
    dataSegmentsSent = 0
    packetsDropped = 0
    retransmittedSegments = 0
    dupAcksReceived = 0

    def sendingPLModule():
        # Sends PTP segments with data
        while (sManager.receivedAcks < len(sManager.segmentsToSend)):
            sManager.sendPLSegment(clientAddress)
            # print("here")
            # segmentPayload = sManager.getCurrentSegment()
            # PTPsegement = createSegement(
            #     sManager.sequenceNumber,
            #     sManager.acknowledgementNumber,
            #     payload=segmentPayload,
            #     length=len(segmentPayload)
            # )

            # # PL modules

            # # If we do not drop the packet, we move the window
            # if (random.random() > pdrop): 
            #     sManager.sendSegment(PTPsegement, (receiverIP, receiverPort))
            #     if sManager.packetLoss == False:
            #         sManager.windowStart += 1
            #         sManager.packetLossSequence = sManager.sequenceNumber
            #         sManager.windowEnd = min(sManager.windowEnd + 1, len(sManager.segmentsToSend))
            #         sManager.addLogAction(
            #             senderLogFileEntry(
            #                 "snd",
            #                 round(time.time() - startTime, 6),
            #                 "D",
            #                 sManager.sequenceNumber,
            #                 len(segmentPayload),
            #                 sManager.acknowledgementNumber
            #             )
            #         )
            # else:
            #     if sManager.packetLoss == False:
            #         sManager.packetLossSequence = sManager.sequenceNumber
            #         sManager.packetLoss = True
            #         sManager.addLogAction(
            #             senderLogFileEntry(
            #                 "drop",
            #                 round(time.time() - startTime, 6),
            #                 "D",
            #                 sManager.sequenceNumber,
            #                 len(segmentPayload),
            #                 sManager.acknowledgementNumber
            #             )
            #         )

            # sManager.incrementSequenceNumber(len(segmentPayload))


    def receivingPLModule():
        while (sManager.receivedAcks < len(sManager.segmentsToSend)):
            sManager.receivePLSegment()
        # try:
        #     # message, senderAddress = senderSocket.recvfrom(2048)
        #     ackSegment = sManager.receiveSegment()
        #     sManager.addLogAction(
        #         senderLogFileEntry(
        #             "rcv",
        #             round(time.time() - startTime, 6),
        #             "A",
        #             ackSegment['sequenceNumber'],
        #             0,
        #             ackSegment['acknowledgementNumber']
        #         )
        #     )
        #     sManager.segmentsToSendIndex += 1
        # except:
        #     sManager.segmentsToSendIndex = sManager.windowStart
        #     sManager.packetLoss = False
        #     sManager.sequenceNumber = sManager.packetLossSequence

    sendingThread = threading.Thread(target=sendingPLModule)
    receivingThread = threading.Thread(target=receivingPLModule)

    sendingThread.start()
    receivingThread.start()

    sendingThread.join()
    receivingThread.join()

        # print(PTPsegement)
        # print()

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
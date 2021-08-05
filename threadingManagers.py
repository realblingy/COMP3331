import json
import random
from ptp import createSegement, senderLogFileEntry
from socket import AF_INET, SOCK_DGRAM, socket
import threading
import time


class SenderManager():

    def __init__(self, fileToSend, MSS, MWS, seedNumber, pdrop):

        random.seed(seedNumber)

        self.lock = threading.Lock()
        self.sequenceNumber = 0
        self.acknowledgementNumber = 0
        self.pdrop = pdrop

        self.timeElapsed = time.time()

        self.sock = None
        self.clientAddress = None
        self.timer = None

        self.senderLogActions = ""
        self.senderLogFile = open("Sender_log.txt", "w")

        self.segmentsToSend = []
        self.segmentsToSendIndex = 0

        self.packetLoss = False
        self.packetLossSequence = False
        self.packetLossIndex = 0
        self.windowStart = 0
        self.lastReceivedAck = 0

        self.hasSentWindow = False

        self.lastReceivedAck = 0
        self.receivedDupAcks = 1
        self.receivedAcks = 0
        self.sentSegments = 0
        self.sentNonDroppedSegments = 0

        # For the log file
        self.totalDataTransferred = 0
        self.totalDataSegmentsSent = 0
        self.totalPacketsDropped = 0
        self.totalDuplicateAcks = 0
        self.totalDuplicateSegments = 0

        self.allSegments = 0


        with open(fileToSend, "r") as f:
            payload = f.read(MSS)
            while payload != "":
                self.totalDataSegmentsSent += 1
                # sManager.addSegmentToSend(payload)
                self.segmentsToSend.append(payload)
                self.totalDataTransferred += len(payload)
                payload = f.read(MSS)
                
            f.close() 

        self.windowEnd = min(MWS / MSS, len(self.segmentsToSend))

    def addLogAction(self, entry):
        self.senderLogActions += entry

    def initializeSocket(self, serverIP, serverPort, timer):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((serverIP, serverPort))
        self.sock.settimeout(timer / 1000)
        self.timer = timer

    def getCurrentSegment(self):
        return self.segmentsToSend[self.segmentsToSendIndex]

    def incrementSequenceNumber(self, increment):
        self.sequenceNumber += increment

    def setSequenceNumber(self, newSequenceNumber):
        self.sequenceNumber = newSequenceNumber

    def incrementAcknowledgementNumber(self, increment):
        self.acknowledgementNumber += increment

    def setAcknowledgementNumber(self, newAcknowledgementNumber):
        self.acknowledgementNumber = newAcknowledgementNumber

    def sendSegment(self, segment, clientAddress, length, flag):

        self.sock.sendto(segment, clientAddress)
        self.addLogAction(
            senderLogFileEntry(
                "snd",
                round(time.time() - self.timeElapsed, 6),
                flag,
                self.sequenceNumber,
                length,
                self.acknowledgementNumber,
            )
        )


    def sendPLSegment(self, clientAddress):
        self.lock.acquire()
        while self.segmentsToSendIndex < self.windowEnd:
            segmentPayload = self.getCurrentSegment()
            try:
                PTPsegement = createSegement(
                    self.sequenceNumber,
                    self.acknowledgementNumber,
                    payload=segmentPayload,
                    length=len(segmentPayload)
                )

                # Send packet
                if (random.random() > self.pdrop):
                    self.allSegments += 1
                    self.sendSegment(PTPsegement, clientAddress, len(segmentPayload), 'D')
                    self.sentNonDroppedSegments += 1

                    if self.packetLoss == False:
                        self.packetLossSequence = self.sequenceNumber
                    else:
                        self.totalDuplicateSegments += 1
                else:

                    self.totalPacketsDropped += 1
                    self.addLogAction(
                        senderLogFileEntry(
                            "drop",
                            round(time.time() - self.timeElapsed, 6),
                            "D",
                            self.sequenceNumber,
                            len(segmentPayload),
                            self.acknowledgementNumber,
                        )
                    )
                    if self.packetLoss == False:
                        self.packetLossSequence = self.sequenceNumber
                        self.packetLoss = True
                        self.packetLossIndex = self.segmentsToSendIndex
            finally:
                self.segmentsToSendIndex += 1
                self.sentSegments += 1
                self.incrementSequenceNumber(len(segmentPayload))
        self.lock.release()
        

    def receivePLSegment(self):
        self.lock.acquire()
        try:
            # Only receive segments if we attempt to send them
            # which can be dropped
            if self.receivedAcks < self.sentSegments:
                lastAck = self.lastReceivedAck
                ackSegment = self.receiveSegment('A')
                self.sentNonDroppedSegments -= 1

                if int(ackSegment['acknowledgementNumber']) > lastAck:
                    self.lastReceivedAck = int(ackSegment['acknowledgementNumber'])

                    self.receivedAcks += 1
                    self.windowStart += 1
                    self.windowEnd = min(self.windowEnd + 1, len(self.segmentsToSend))
                else:
                    self.totalDuplicateAcks += 1
                    self.receivedDupAcks += 1

                # Discard remaining ack segments and revert back to lost packet
                if self.receivedDupAcks == 3:
                    while (self.sentNonDroppedSegments > 0):
                        self.receiveSegment('A')
                        self.sentNonDroppedSegments -= 1
                        self.totalDuplicateAcks += 1
                    raise Exception

        except:
            self.sentNonDroppedSegments = 0
            self.receivedDupAcks = 1
            self.sentSegments = self.packetLossIndex
            self.receivedAcks = self.packetLossIndex
            self.segmentsToSendIndex = self.packetLossIndex
            self.packetLoss = False
            self.sequenceNumber = self.packetLossSequence
        finally:
            self.lock.release()

    def receiveSegment(self, flag):
        try:
            self.sock.settimeout(self.timer / 1000)
            message, clientAddress = self.sock.recvfrom(2048)
            segment = json.loads(message.decode('utf-8'))
            self.lastReceivedAck = int(segment['acknowledgementNumber'])
            self.addLogAction(
                senderLogFileEntry(
                    "rcv",
                    round(time.time() - self.timeElapsed, 6),
                    flag,
                    segment['sequenceNumber'],
                    int(segment['length']),
                    segment['acknowledgementNumber'],
                )
            )
            return segment
        except:
            raise Exception()

    def closeSocket(self):
        self.senderLogFile.write(self.senderLogActions)
        self.senderLogFile.write("\n=====================================================\n")
        self.senderLogFile.write(f"Total data transferred: {self.totalDataTransferred}\n")
        self.senderLogFile.write(f"Number of data segments sent: {self.totalDataSegmentsSent}\n")
        self.senderLogFile.write(f"Number of (all) Packets Dropped (by the PL module): {self.totalPacketsDropped}\n")
        self.senderLogFile.write(f"Number of retransmitted segments: {self.totalDuplicateSegments}\n")
        self.senderLogFile.write(f"Number of duplicate acknowledgements received: {self.totalDuplicateAcks}\n")
    

        self.senderLogFile.close()
        self.sock.close()

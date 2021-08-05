import json
from socket import AF_INET, SOCK_DGRAM, socket
import threading
import time


class SenderManager():

    def __init__(self, fileToSend, MSS, MWS):
        self.lock = threading.Lock()
        self.sequenceNumber = 1000
        self.acknowledgementNumber = 0

        self.sock = None
        self.clientAddress = None

        self.senderLogActions = ""
        self.senderLogFile = open("Sender_log.txt", "w")

        self.segmentsToSend = []
        self.segmentsToSendIndex = 0

        self.packetLoss = False
        self.packetLossSequence = False
        self.windowStart = 0

        with open(fileToSend, "r") as f:
            payload = f.read(MSS)
            while payload != "":
                # sManager.addSegmentToSend(payload)
                self.segmentsToSend.append(payload)
                payload = f.read(MSS)
            f.close() 

        self.windowEnd = min(MWS, len(self.segmentsToSend))
    # def increment(self):
    #     self.lock.acquire()
    #     try:
    #         print("Acquired a lock, segmentsToSendIdx value: ", self.segmentsToSendIndex)
    #         self.segmentsToSendIndex += 3
    #     finally:
    #         print("Released a lock, segmentsToSendIdx value: ", self.segmentsToSendIndex)
    #         self.lock.release()
    def addLogAction(self, entry):
        self.senderLogActions += entry

    def initializeSocket(self, serverIP, serverPort, timer):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((serverIP, serverPort))
        self.sock.settimeout(timer / 1000)

    def getCurrentSegment(self):
        return self.segmentsToSend[self.segmentsToSendIndex]

    # def addSegmentToSend(self, segment):
    #     self.segmentsToSend.append(segment)
    
    def incrementSequenceNumber(self, increment):
        self.sequenceNumber += increment

    def setSequenceNumber(self, newSequenceNumber):
        self.sequenceNumber = newSequenceNumber

    def incrementAcknowledgementNumber(self, increment):
        self.acknowledgementNumber += increment

    def setAcknowledgementNumber(self, newAcknowledgementNumber):
        self.acknowledgementNumber = newAcknowledgementNumber

    # def decrement(self):
    #     print("Decrementing")
    #     print("Waiting for lock")
    #     self.lock.acquire()
    #     try:
    #         print("Acquired a lock, segmentsToSendIdx value: ", self.segmentsToSendIndex)
    #         self.segmentsToSendIndex -= 1
    #     finally:
    #         print("Released a lock, segmentsToSendIdx value: ", self.segmentsToSendIndex)
    #         self.lock.release()

    def sendSegment(self, segment, clientAddress):
        self.sock.sendto(segment, clientAddress)

    def receiveSegment(self):
        try:
            message, clientAddress = self.sock.recvfrom(2048)
            segment = json.loads(message.decode('utf-8'))
            return segment
        except:
            raise Exception()

    def closeSocket(self):
        self.senderLogFile.write(self.senderLogActions)
        self.senderLogFile.close()
        self.sock.close()

def sendSegment(s):

    for i in range(5):
        s.increment()
    print("Done")

def cancelSegment(s):

    for i in range(5):
        s.decrement()
    print("Done")


if __name__ == '__main__':

    sManager = SenderManager()

    t1 = threading.Thread(target=sendSegment, args=(sManager,))
    t1.start()

    t2 = threading.Thread(target=cancelSegment, args=(sManager,))
    t2.start()

    t1.join()
    t2.join()

    print("Final IDX number: ", sManager.segmentsToSendIndex)

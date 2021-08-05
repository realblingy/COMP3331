import threading
import time


class SenderManager():

    def __init__(self):
        self.lock = threading.Lock()
        self.sequenceNumber = 1000
        self.acknowledgementNumber = 0
        self.segmentsToSend = 0
        self.segmentsToSendIndex = 0

    def increment(self):
        self.lock.acquire()
        try:
            print("Acquired a lock, segmentsToSendIdx value: ", self.segmentsToSendIndex)
            self.segmentsToSendIndex += 3
        finally:
            print("Released a lock, segmentsToSendIdx value: ", self.segmentsToSendIndex)
            self.lock.release()

    def decrement(self):
        print("Decrementing")
        print("Waiting for lock")
        self.lock.acquire()
        try:
            print("Acquired a lock, segmentsToSendIdx value: ", self.segmentsToSendIndex)
            self.segmentsToSendIndex -= 1
        finally:
            print("Released a lock, segmentsToSendIdx value: ", self.segmentsToSendIndex)
            self.lock.release()


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

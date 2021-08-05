from ptp import createSegement, senderLogFileEntry
import sys
from socket import *
import json
import time

if len(sys.argv) != 3:
    print("Usage python receiver.py <receiver_port> <FileReceived.txt>")
    sys.exit();


receiverPort = int(sys.argv[1])
fileReceived = open(sys.argv[2], "w")

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.bind(('localhost', receiverPort))

# print('PTP server is ready to receive')

sequenceNumber = 500
acknowledgementNumber = None
allowSending = False

# Awaits SYN segment
message, senderAddress = clientSocket.recvfrom(2048)

segment = json.loads(message.decode('utf-8'))
contents = ''

receiveLogActions = ""
receiverLogFile = open("Receiver_log.txt", "w")

startTime = time.time()

totalDataReceived = 0
totalDataSegmentsReceived = 0
totalDuplicateSegmentsReceived = 0
prevAck = 0
prevAckCounter = 0

# Sends SYN-ACK segment
if segment['syn'] == 1:
    acknowledgementNumber = int(segment['sequenceNumber']) + 1

    synAckSegement = createSegement(
        sequenceNumber,
        acknowledgementNumber,
        syn=1,
        ack=1
    )

    clientSocket.sendto(synAckSegement, senderAddress)

    receiveLogActions += senderLogFileEntry(
        "snd",
        round(time.time() - startTime, 6),
        "SA",
        sequenceNumber,
        0,
        acknowledgementNumber
    )

# Awaits ACK segment
message, senderAddress = clientSocket.recvfrom(2048)

segment = json.loads(message.decode('utf-8'))

receiveLogActions += senderLogFileEntry(
    "rcv",
    round(time.time() - startTime, 6),
    "A",
    sequenceNumber,
    0,
    acknowledgementNumber
)

# Connection established
if segment['ack'] == 1:
    allowSending = True
    sequenceNumber += 1
    prevAck = acknowledgementNumber
    
    # print("A connection has been established with " + str(senderAddress))
    # print()
    # print("Initial sequence number: " + str(sequenceNumber))
    # print()
    # print("Initial acknowledgement number: " + str(acknowledgementNumber))

# Receive segments
while 1:
    message, senderAddress = clientSocket.recvfrom(2048)
    # print(segment['sequenceNumber'])
    segment = json.loads(message.decode('utf-8'))

    # print("Received segment")
    # print(segment)
    # print("==================")

    # Sender sends finish segment which closes the socket
    if segment['fin'] == 1:


        finAckSegment = createSegement(
            sequenceNumber,
            acknowledgementNumber,
            fin=1,
            ack=1,
        )

        
        clientSocket.sendto(finAckSegment, senderAddress)

        receiveLogActions += senderLogFileEntry(
            "snd",
            round(time.time() - startTime, 6),
            "FA",
            sequenceNumber,
            0,
            acknowledgementNumber
        )

        message, senderAddress = clientSocket.recvfrom(2048)

        receiveLogActions += senderLogFileEntry(
            "rcv",
            round(time.time() - startTime, 6),
            "A",
            sequenceNumber,
            0,
            acknowledgementNumber
        )

        totalDataReceived = len(contents)

        receiveLogActions += "\n=====================================================\n"
        receiveLogActions += f"Amount of data received: {totalDataReceived}\n"
        receiveLogActions += f"Number of data segments received: {totalDataSegmentsReceived}\n"
        receiveLogActions += f"Number of duplicate segments received: {totalDuplicateSegmentsReceived}"

        fileReceived.write(contents)
        

        # print("Closing socket");
        receiverLogFile.write(receiveLogActions)
        receiverLogFile.close()
        fileReceived.close()
        clientSocket.close()
        break;

    receiveLogActions += senderLogFileEntry(
        "rcv",
        round(time.time() - startTime, 6),
        "D",
        sequenceNumber,
        segment['length'],
        acknowledgementNumber
    )

    # Checks if right packet is sent
    if segment['sequenceNumber'] == acknowledgementNumber:
        acknowledgementNumber += int(segment['length'])
        contents += segment['payload']
        totalDataSegmentsReceived += 1
    else:
        totalDuplicateSegmentsReceived += 1
        # print("Received segment")
        # print(segment)
        # print()
    
    ackSegment = createSegement(
        sequenceNumber,
        acknowledgementNumber,
        ack=1
    )

    # print("Acked Segment sent")
    # print(ackSegment)
    # print()

    clientSocket.sendto(ackSegment, senderAddress)

            





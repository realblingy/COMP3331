from ptp import createSegement
import sys
from socket import *
import json

if len(sys.argv) != 3:
    print("Usage python receiver.py <receiver_port> <FileReceived.txt>")
    sys.exit();

receiverPort = int(sys.argv[1])
fileReceived = open(sys.argv[2], "w")

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.bind(('localhost', receiverPort))

print('PTP server is ready to receive')

sequenceNumber = 500
acknowledgementNumber = None
allowSending = False

# Awaits SYN segment
message, senderAddress = clientSocket.recvfrom(2048)

segment = json.loads(message.decode('utf-8'))
contents = ''

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

# Awaits ACK segment
message, senderAddress = clientSocket.recvfrom(2048)

segment = json.loads(message.decode('utf-8'))

# Connection established
if segment['ack'] == 1:
    allowSending = True
    sequenceNumber += 1
    print("A connection has been established with " + str(senderAddress))
    print()
    print("Initial sequence number: " + str(sequenceNumber))
    print()
    print("Initial acknowledgement number: " + str(acknowledgementNumber))

# Receive segments
while 1:
    message, senderAddress = clientSocket.recvfrom(2048)
    segment = json.loads(message.decode('utf-8'))
    print("Received segment")
    print(segment)
    print()

    # Sender sends finish segment which closes the socket
    if segment['fin'] == 1:
        finAckSegment = createSegement(
            sequenceNumber,
            acknowledgementNumber,
            fin=1,
            ack=1,
        )


        clientSocket.sendto(finAckSegment, senderAddress)

        message, senderAddress = clientSocket.recvfrom(2048)
        fileReceived.write(contents)

        # print("Closing socket");
        fileReceived.close()
        clientSocket.close()
        break;


    # Checks if right packet is sent
    if segment['sequenceNumber'] == acknowledgementNumber:
        acknowledgementNumber += int(segment['length'])
        contents += segment['payload']
    
    ackSegment = createSegement(
        sequenceNumber,
        acknowledgementNumber,
        ack=1
    )

    clientSocket.sendto(ackSegment, senderAddress)

            





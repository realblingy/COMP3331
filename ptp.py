import json

def createSegement(
    sequenceNumber, 
    acknowledgementNumber = 0,
    syn = 0,
    fin = 0,
    ack = 0,
    payload = "",
    length = 0
):

    dict = {
        'sequenceNumber': sequenceNumber,
        'acknowledgementNumber': acknowledgementNumber,
        'syn': syn,
        'fin': fin,
        'ack': ack,
        'length': length,
        'payload': payload 
    }

    encoded_dict = json.dumps(dict, indent=2).encode('utf-8')

    return encoded_dict


def senderLogFileEntry(action, time, packetType, sequenceNumber, numberOfBytes, ackNumber):

    return f"{action.ljust(5)} {str(time).ljust(10)} {packetType.ljust(3)} {str(sequenceNumber).ljust(10)} {str(numberOfBytes).ljust(10)} {str(ackNumber).ljust(10)}\n"

# def receiverLogFileEntry()
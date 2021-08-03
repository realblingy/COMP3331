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


import sys
import string
import struct
import socket
import time
import random


def create_header():
    ID = random.randint(0, 65535) # Generate a random 16-bit number for the ID field
    QR = 0 # 1 bit
    OPCODE = 0 # 4 bits
    AA = 0 # 1 bit
    TC = 0 # 1 bit
    RD = 1 # 1 bit
    RA = 0 # 1 bit
    Z = 0 # 3 bits
    RCODE = 0 # 4 bits
    
    flags = (QR << 15) | (OPCODE << 11) | (AA << 10) | (TC << 9) | (RD << 8) | (RA << 7) | (Z << 4) | RCODE # 16 bits
    
    QDCOUNT = 1 # 16 bits
    ANCOUNT = 0 # 16 bits
    NSCOUNT = 0 # 16 bits
    ARCOUNT = 0 # 16 bits
    
    header = struct.pack(">HHHHHH", ID, flags, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT) # 12 bytes
    return header, ID, RD
    
def create_question(domaine_name, query_type):
    question = b''
    QNAME = []
    domaine_name_list = domaine_name.split(".")
    
    for label in domaine_name_list:
        question += struct.pack(">B", len(label))
        QNAME.append(len(label))
        for char in label:
            question += char.encode('ascii')
            QNAME.append(ord(char))
    question += struct.pack(">B", 0) # end of domain name
    
    QTYPE = 1 # 16 bits, A record by default
    QCLASS = 1 # 16 bits, IN class by default
    
    if query_type == "-mx":
        QTYPE = 15
    elif query_type == "-ns":
        QTYPE = 2
    
    question += struct.pack(">HH", QTYPE, QCLASS) # 4 bytes
    return question, QNAME, QTYPE, QCLASS
        
    
def query_server(timeout, max_retries, port, server, query):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    
    
    retry_count = 0
    while retry_count < max_retries:
        try:
            send_time = time.time() # time before sending the query
            sock.sendto(query, (server, port))
            response, _ = sock.recvfrom(1024)
            recv_time = time.time() # time after receiving the response
            if response: 
                return response, recv_time - send_time, retry_count
        except:
            retry_count += 1
        
    print(f"ERROR    Maximum number of retries {max_retries} exceeded")
    return None

def parse_header(query_ID, query_RD, response):
    
    ID, flags, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT = struct.unpack(">HHHHHH", response[:12])
    
    if ID != query_ID:
        print(f"Error    Unexpected response, the response ID {ID} does not match the query ID {query_ID}")
    
    QR = (flags >> 15) & 0b1
    OPCODE = (flags >> 11) & 0b1111
    AA = (flags >> 10) & 0b1
    TC = (flags >> 9) & 0b1
    RD = (flags >> 8) & 0b1
    RA = (flags >> 7) & 0b1
    Z = (flags >> 4) & 0b111
    RCODE = flags & 0b1111
    
    if QR != 1:
        print("Error    Unexpected response, the QR bit does not correspond to a response message")
    elif OPCODE != 0:
        print("Error    Unexpected response, the OPCODE does not correspond to a standard query")
    elif TC != 0:
        print("Error    Unexpected response, message is truncated")
    elif RD != query_rd:
        print(f"Error    Unexpected response, the RD flag {RD} does not match the query RD flag {query_RD}")
    elif Z != 0:
        print("Error    Unexpected response, the Z field is not zero")
    elif RCODE != 0:
        if RCODE == 1:
            print("Error    Unexpected response: the name server was unable to interpret the query")
        elif RCODE == 2:
            print("Error    Unexpected response: the name server was unable to process the query")
        elif RCODE == 3:
            print("Error    Unexpected response: the domain name does not exist")
        elif RCODE == 4:
            print("Error    Unexpected response: the name server does not support the requested query")
        elif RCODE == 5:
            print("Error    Unexpected response: the name server refused to process the query")
            
    return ID, QR, OPCODE, AA, TC, RD, RA, Z, RCODE, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT

def parse_question(query_QNAME, query_QTYPE, query_QCLASS, response):
    offset = 12 # start after the header (12 bytes)
    QNAME = []
    
    while response[offset] != 0:
        QNAME.append(response[offset])
        offset += 1
        
    offset += 1 # skip the 0 byte
    
    QTYPES = struct.unpack_from(">H", response, offset)[0]
    QCLASS = struct.unpack_from(">H", response, offset + 2)[0]
    
    offset += 4
    
    if query_QNAME != QNAME:
        print(f"Error    Unexpected response, the QNAME {QNAME} does not match the query QNAME {query_QNAME}")
    elif query_QTYPE != QTYPES:
        print(f"Error    Unexpected response, the QTYPE {QTYPES} does not match the query QTYPE {query_QTYPE}")
    elif query_QCLASS != QCLASS:
        print(f"Error    Unexpected response, the QCLASS {QCLASS} does not match the query QCLASS {query_QCLASS}")
    
    return QNAME, QTYPES, QCLASS, offset

def parse_answer(response, offset, COUNT):
    answers = []
    
    for i in range(COUNT):
        NAME = []
        if response[offset] & 0b11000000:
            pointer = struct.unpack_from(">H", response, offset)[0] & 0b0011111111111111 # remove the first 2 bits and get the 14 bits representing the offset
            while response[pointer] != 0:
                NAME.append(response[pointer])
                pointer += 1
            offset += 2
        else:
            while response[offset] != 0:
                NAME.append(response[offset])
                offset += 1
            offset += 1 # skip the 0 byte
        
        TYPE = struct.unpack_from(">H", response, offset)[0]
        CLASS = struct.unpack_from(">H", response, offset + 2)[0]
        TTL = struct.unpack_from(">I", response, offset + 4)[0]
        RDLENGTH = struct.unpack_from(">H", response, offset + 8)[0]
        RDATA = response[offset + 10: offset + 10 + RDLENGTH]
        PREFERENCE = None
        EXCHANGE = None
        
        record = (NAME, TYPE, CLASS, TTL, RDLENGTH, RDATA)
        
        if (TYPE == 1 and RDLENGTH != 4):
            print(f"ERROR   Unexpected response, the RDLENGTH {RDLENGTH} does not match the expected length for an A record")
        elif (TYPE == 15):
            PREFERENCE = struct.unpack_from(">H", response, offset + 10)[0]
            EXCHANGE = []
            exchange_offset  = offset + 12
            if response[exchange_offset] & 0b11000000:
                pointer = struct.unpack_from(">H", response, exchange_offset)[0] & 0b0011111111111111
                while response[pointer] != 0:
                    EXCHANGE.append(response[pointer])
                    pointer += 1
            else:
                while response[exchange_offset] != 0:
                    EXCHANGE.append(response[exchange_offset])
                    exchange_offset += 1
                exchange_offset += 1
                    
            record += (PREFERENCE, EXCHANGE)
        
        offset += 10 + RDLENGTH
        answers.append(record)
    
    return answers, offset

print_response(ID, QR, OPCODE, AA, TC, RD, RA, Z, RCODE, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT, QNAME, QTYPES, QCLASS, answers, authorities, additionals):
    
          
def parse_response(query_ID, query_RD, query_QNAME, query_QTYPE, query_QCLASS, response):
    ID, QR, OPCODE, AA, TC, RD, RA, Z, RCODE, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT = parse_header(query_ID, query_RD, response)
    
    QNAME, QTYPES, QCLASS, offset_question = parse_question(query_QNAME, query_QTYPE, query_QCLASS, response)
    
    answers, offset_answer = parse_answer(response, offset_question, ANCOUNT)
    
    authorities, offset_authorities parse_answer(response, offset_answer, NSCOUNT) # reuse the parse_answer function to parse the authorities
    
    additionals, offset_additionals = parse_answer(response, offset_authorities, ARCOUNT) # reuse the parse_answer function to parse the additionals
    
    print_response(ID, QR, OPCODE, AA, TC, RD, RA, Z, RCODE, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT, QNAME, QTYPES, QCLASS, answers, authorities, additionals)
    

def main():
    # program arguments
    timeout  = 5 # default value
    max_retries = 3 # default value
    port = 53 # default value
    query_type = "A" # default A, other values: MX, NS
    server = None # dns server
    name = None # domain name
    args = sys.argv[1:]
    
    i = 0
    while (i < len(args)):
        if args[i] == "-t":
            timeout = int(args[i+1])
            i += 2
        elif args[i] == "-r":
            max_retries = int(args[i+1])
            i += 2
        elif args[i] == "-p":
            port = int(args[i+1])
            i += 2
        elif args[i] == "-mx":
            query_type = "-mx"
            i += 1
        elif args[i] == "-ns":
            query_type = "-ns"
            i += 1
        elif args[i].startwith("@"):
            server = args[i][1:] # remove the @ symbol, keep the server IP address
            name = args[i+1] # domain name
            i += 2
            
            if (i < len(args)):
                print("ERROR    Incorrect input syntax: the server name must be the last specified arguments")
                exit(1)
        else:
            print(f"ERROR    Incorrect input syntax: program argument {args[i]} is not recognized")
            exit(1)
    
    if (server is None or name is None):
        print("ERROR    Incorrect input syntax: server name and domain name must be specified")
        exit(1)
    
    print(f"DnsClient sending request for {name}")
    print(f"Server: {server}")
    print(f"Request type: {query_type}")
    
    # create query
    header, ID, RD = create_header()
    question, QNAME, QTYPE, QCLASS = create_question(name, query_type)
    query = header + question
    
    # send query to server
    response, elapsed_time, retry_count = query_server(timeout, max_retries, port, server, query)
    
    print(f"Response received after {elapsed_time} seconds ({retry_count} retries)")
    
    
    # parse response
    parse_response(ID, RD, QNAME, QTYPE, QCLASS, response)

              
if __name__ == "__main__":
    main()
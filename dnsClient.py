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
    return header
    
def create_question(domaine_name, query_type):
    question = b''
    domaine_name_list = domaine_name.split(".")
    
    for label in domaine_name_list:
        question += struct.pack(">B", len(label))
        for char in label:
            question += char
    question += struct.pack(">B", 0) # end of domain name
    
    QTYPE = 1
    QCLASS = 1
    
    if query_type == "-mx":
        QTYPE = 15
    elif query_type == "-ns":
        QTYPE = 2
    
    question += struct.pack(">HH", QTYPE, QCLASS) # 4 bytes
    return question
        
    
def create_query(domaine_name, query_type):
    return create_header() + create_question(domaine_name, query_type)
    
def query_server(timeout, max_retries, port, server, query):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    
    retry_count = 0
    while retry_count < max_retries:
        try:
            sock.sendto(query, (server, port))
            response = sock.recvfrom(1024)
            if response:
                return response

        except socket.timeout:
            retry_count += 1
        
    print(f"ERROR    Maximum number of retries {max_retries} exceeded")
    return None
        
def parse_response():
    return 1
    

def main():
    # program arguments
    timeout  = 5 # default value
    max_retries = 3 # default value
    port = 53 # default value
    query_type = "" # -mx or -ns
    server = "" # dns server
    name = "" # domain name
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
            server = args[i][1:]
            name = args[i+1]
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
     
    query = create_query(name, query_type)
    response = query_server(timeout, max_retries, port, server, query)

              
if __name__ == "__main__":
    main()
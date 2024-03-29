import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
rttList = []
recPacks = 0
sentPacks = 0

def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = ord(string[count+1]) * 256 + ord(string[count])
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receive_one_ping(mySocket, ID, timeout, destAddr):
    while 1:
        what_ready = select.select([mySocket], [], [], timeout)
        if what_ready[0] == []:  # Timeout
            return "Request timed out."

        time_recieved = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # TODO: read the packet and parse the source IP address, you will need this part for traceroute
        header_pieces = struct.unpack('bbHHh',recPacket[20:28])

        # TODO: calculate and return the round trip time for this ping
        time_sent = struct.unpack('d',recPacket[28:(28 + struct.calcsize('d'))])[0]
        rtt = time_recieved - time_sent

        # TODO: handle different response type and error code, display error message to the user
        headerType = header_pieces[0]
        if headerType == 0:
            # part for extra credit
            global recPacks
            recPacks = recPacks + 1
            ec_helper(rtt)
            return rtt
        elif headerType == 8:
            print("Pass - echo request (type 8)")
            return
        elif headerType == 3:
            print("Error: port unreachable (type 3)")
            return
        else:
            print('Error: unrecognized type (type {:d})'.format(headerType))
            return


def send_one_ping(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0
    # Make a dummy header with a 0 checksum

    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(str(header + data))
    # Get the right checksum, and put in the header
    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network byte order
        myChecksum = socket.htons(myChecksum) & 0xffff
    else:
        myChecksum = socket.htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data
    # AF_INET address must be tuple, not str # Both LISTS and TUPLES consist of a number of objects
    mySocket.sendto(packet, (destAddr, 1))
    global sentPacks
    sentPacks = sentPacks + 1
    # which can be referenced by their position number within the object.


def do_one_ping(destAddr, timeout):
    icmp = socket.getprotobyname("icmp")
    # SOCK_RAW is a powerful socket type. For more details: http://sock- raw.org/papers/sock_raw
    mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    # Return the current process i
    myID = os.getpid() & 0xFFFF
    send_one_ping(mySocket, destAddr, myID)
    delay = receive_one_ping(mySocket, myID, timeout, destAddr)

    mySocket.close()
    return delay


def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost
    dest = socket.gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    # Send ping requests to a server separated by approximately one second
    while 1:
        delay = do_one_ping(dest, timeout)
        print(delay)
        time.sleep(1)  # one second
    return delay

# calculates stats for extra credit part
def ec_helper(rtt):
    global rttList
    global recPacks
    global sentPacks
    rttList.append(rtt)
    rttAvg = sum(rttList) / len(rttList)
    packLoss = ((sentPacks - recPacks) / sentPacks) * 100
    print('Minimum RTT: {:f}'.format(min(rttList)))
    print('Maximum RTT: {:f}'.format(max(rttList)))
    print('Average RTT: {:f}'.format(rttAvg))
    print('Packet Loss: {:f}%'.format(packLoss))
    print('---------------')

ping(sys.argv[1])
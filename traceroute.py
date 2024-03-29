import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 2
# The packet that we shall send to each router along the path is the ICMP echo # request packet, which is exactly what we had used in the ICMP ping exercise. # We shall use the same packet that we built in the Ping exercise


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


def build_packet():
    # In the sendOnePing() method of the ICMP Ping exercise ,firstly the header of our
    # packet to be sent was made, secondly the checksum was appended to the header and
    # then finally the complete packet was sent to the destination.
    # Make the header in a similar way to the ping exercise.
    # Append checksum to the header.
    # So the function ending should look like this
    ID = os.getpid() & 0xFFFF
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, 0, ID, 1)
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
    return packet


def get_route(hostname):
    icmp = socket.getprotobyname("icmp")
    timeLeft = TIMEOUT
    for ttl in range(1, MAX_HOPS):
        for tries in range(TRIES):

            # TODO: create ICMP socket, connect to destination IP, set timeout and time-to-live
            icmp_socket = socket.socket(socket.AF_INET,socket.SOCK_RAW,icmp)
            icmp_socket.settimeout(TIMEOUT)
            icmp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))

            try:
                # TODO: create ICMP ping packet, record the time delay of getting response, detect timeout
                icmp_socket.sendto(build_packet(),(hostname,0))

                recPacket,addr = icmp_socket.recvfrom(1024)
                time_received = time.time()

            except socket.timeout:
                continue
            else:
                # TODO: parse and handle different response type
                # Hint: use wireshark to get the byte location of the response type
                header_pieces = struct.unpack('bbHHh',recPacket[20:28])
                ipAddr = addr[0]
                try:
                    hostName = socket.gethostbyaddr(ipAddr)[0]
                except:
                    print("")
                if header_pieces[0] == 0:
                    time_sent = struct.unpack('d',recPacket[28:(28 + struct.calcsize('d'))])[0]
                    trip = time_received - time_sent
                    print("Trip time: {:f}".format(trip))
                    return trip
                elif header_pieces[0] == 11:
                    print("Error: TTL exceeded (type 11)")
                    print("IP addr: {:s}".format(ipAddr))
                    print("Hostname: {:s}".format(hostName))
                    print('---------------')
                elif header_pieces[0] == 3:
                    print("Error: destination unreachable (type 3)")
                    print("IP addr: {:s}".format(ipAddr))
                    print("Hostname: {:s}".format(hostName))
                    print('---------------')
                else:
                    print("Error: unexpected type (type {:d})".format(header_pieces[0]))
                    break

            finally:
                # TODO: close the socket
                icmp_socket.close()


get_route(sys.argv[1])
import socket
import struct
import numpy as np


class BPC:
    def __init__(self, IP, port=5000):
        self.IP = IP
        self.port = port
        self.message = b"XXXXXXXXLoop"

        self.sock = None
        self.server_address = None

        self.getUDPConnection()

    def getUDPConnection(self):
        """Create the UDP socket and configure the BPC server address."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(3)
            self.server_address = (self.IP, self.port)

        except Exception as err:
            print("Socket error: %s" % err)
            self.sock = None
            self.server_address = None

    def poll_BPC(self):
        """Poll the BPC and return the payload after the 8-byte header."""
        if self.sock is None or self.server_address is None:
            raise RuntimeError("UDP connection has not been initialized.")

        self.sock.sendto(self.message, self.server_address)
        data, addr = self.sock.recvfrom(2048)

        header = data[:8]
        payload = data[8:]

        return payload

    def getBPC_Parameter(self, index):
        """Unpack 60 big-endian floats and return the requested parameter."""
        w = np.asarray(struct.unpack(">60f", self.poll_BPC()))
        
        if isinstance(index,(list,tuple,np.ndarray)):
            return w[index]

        return w[index]

    def close(self):
        """Close the UDP socket."""
        if self.sock is not None:
            self.sock.close()
            self.sock = None


# Example:
#
# IP = "192.168.1.100"
# bpc = BPC(IP)
#
# try:
#     payload = bpc.poll_BPC()
#     value = bpc.getBPC_Parameter(payload, 0)
#     print(value)
# finally:
#     bpc.close()

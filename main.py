import sys

from modules .server import Server
from modules .client import Client


if __name__ == "__main__" :
    HOST = sys .argv [2] if len (sys .argv) == 3 else "localhost"
    if sys .argv [1] == 's':
        Server (local_host = HOST)
    elif sys .argv [1] == 'c' :
        Client (remote_host = HOST)
    else :
        print ("Provide CLA")


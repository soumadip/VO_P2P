import socket
import time
import gzip
from os import urandom
import numpy as np
import traceback

from modules .params import *

class Communications :
    def __init__ (self, cipher) :
        self .cipher = cipher
        self .PRE = PREFIX_LENGTH
        self .END = END_SEQUENCE
        self .running = None

    def start (self) :
        self .running = True

    def stop (self) :
        self .running = False

    def create_conn (self, host, port) :
        sock = socket .socket (socket .AF_INET, socket .SOCK_STREAM)
        sock .setsockopt (socket .SOL_SOCKET, socket .SO_REUSEADDR, 1)
        sock .bind((host, port))
        return sock

    def connect_to (self, host, port) :
        sock = socket .socket (socket .AF_INET, socket .SOCK_STREAM)
        sock .connect ((host, port))
        return sock

    def send (self, conn, stream) :
        while self .running :
            try:
                to_send = stream .get_data_to_send ()
                cypher = self .cipher .encrypt (to_send)
                conn .sendall (gzip .compress (urandom (self .PRE) + cypher) + self .END)
                time .sleep (stream .INTERVAL) 

            except socket .error as msg:
                print ('[S] Socket error occured', msg)
                break

            except Exception as e :
                print ("[S] Handling Exception, stopping communications", e)
                traceback .print_exc ()
                stream .stop ()
                self .stop ()
        
        stream .stop ()
        conn .close ()
        print ("[S] Connection closed.")

    def receive (self, conn, stream) :
        residue = b''
        ind = None
        while self .running :
            try:
                cypher = residue
                while True :
                    cypher += conn .recv (8192)
                    lc_ind = len (cypher) - len (self .END)
                    if self .END in cypher [lc_ind : ] :
                        ind = cypher .find (self .END)
                        residue = cypher [ind + len (self .END) : ]
                        cypher = cypher [ : ind]
                        break
                received_data = self .cipher .decrypt (gzip .decompress (cypher) [self .PRE : ])
                stream .process_received_data (received_data)
            except socket .error as msg :
                print ('[R] Socker error received [MSG]', msg)
                break
                
            except KeyboardInterrupt as ki :
                print ("\r[R] Program ended.", ki)
                break

            except Exception as e :
                print ("[R] Handling Exception", e)
                #traceback .print_exc ()
                stream .stop ()
                self .stop ()

        conn .close ()
        print ("[R] Connection closed.")


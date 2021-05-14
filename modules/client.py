import socket
import pickle
from threading import Thread
import traceback

from modules .custom_encryption import CustomEncryption
from modules .communications import Communications
from modules .video_stream import VideoStream
from modules .audio_stream import AudioStream
from modules .player import Player

from modules .params import *

class Client :
    def __init__ (self, remote_host, init_key = INIT_KEY) :
        self .REMOTE_HOST = remote_host
        self .key = init_key
        self .PORT_VID = PORT_VIDEO
        self .PORT_AUD = PORT_AUDIO
        self .PORT_META = PORT_METADATA
        self .comm = None
        self .cipher = None

        self .run ()

    def run (self) :
        self .cipher = CustomEncryption (key = self .key)
        self .comm = Communications (self .cipher)
        try :
            conn_metadata = self .comm .connect_to (self .REMOTE_HOST, self .PORT_META)
            self .LOCAL_HOST = conn_metadata .getsockname () [0]

            #Start video sourve
            self .video = VideoStream ("sample.avi")
            #self .video = VideoStream ()
            self .audio = AudioStream ()

            #Get server metadata
            remote_metadata = conn_metadata .recv (300)
            remote_frame_shape, remote_key = pickle .loads (self .cipher .decrypt (remote_metadata))
            print ("Received Metadata", [remote_frame_shape, remote_key])

            #Send own metadata
            own_frame_shape = self .video .get_frame_shape ()
            own_key = self .cipher .get_new_key ()
            print ("Sending Metadata", [own_frame_shape, own_key])
            own_metadata = self .cipher .encrypt (pickle .dumps ([own_frame_shape, own_key]))
            conn_metadata .sendall (own_metadata)

            #open audio video channels
            sock_video = self .comm .create_conn (self .LOCAL_HOST, self .PORT_VID)
            sock_audio = self .comm .create_conn (self .LOCAL_HOST, self .PORT_AUD)
            sock_video .listen (1)
            sock_audio .listen (1)
            conn_video, _ = sock_video .accept ()
            conn_audio, _ = sock_audio .accept ()

            self .video .set_remote_frame_shape (remote_frame_shape)
            self .cipher .update_own_cipher (own_key)
            self .cipher .update_remote_cipher (remote_key)

            #Start sending the real thing
            video_sending = Thread (target = self .comm .send, args = (conn_video, self .video))
            audio_sending = Thread (target = self .comm .send, args = (conn_audio, self .audio))

            #Receive and render
            video_receiving = Thread (target = self .comm .receive, args = (conn_video, self .video))
            audio_receiving = Thread (target = self .comm .receive, args = (conn_audio, self .audio))

            #enable secure comunication channels
            self .comm .start ()

            #start threads
            video_sending .start ()
            video_receiving .start ()
            audio_sending .start ()
            audio_receiving .start ()

            #rendering
            player = Player (self .audio, self .video, "C")
            player .play ()

            #clean up
            print ("Cleaning up")
            sock_video .close ()
            sock_audio .close ()
            conn_metadata .close ()

        except ConnectionRefusedError as cre :
            print ("Connection refused, check if server is running")
        except Exception as e:
            print ("\r[Cl] Program ended, socket closed", e)
            self .comm .stop ()
            self .video .stop ()
            sock_video .close ()
            sock_audio .close ()
            conn_metadata .close ()

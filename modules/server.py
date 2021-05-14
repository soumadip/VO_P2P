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

class Server :
    def __init__ (self, local_host, init_key = INIT_KEY) :
        self .LOCAL_HOST = local_host
        self .PORT_VID = PORT_VIDEO
        self .PORT_AUD = PORT_AUDIO
        self .PORT_META = PORT_METADATA
        self .key = init_key
        self .comm = None
        self .cipher = None
        
        self .run ()

    def run (self) :
        while True:
            self .cipher = CustomEncryption (key = self .key)
            self .comm = Communications (self .cipher)

            try :
                sock_metadata = self .comm .create_conn (self .LOCAL_HOST, self .PORT_META)
                sock_metadata .listen (1)
                print ("Listening ...", self .LOCAL_HOST)

                conn_metadata, _ = sock_metadata. accept ()
                self .REMOTE_HOST = conn_metadata .getpeername () [0]
                print ('Client connection accepted ', self .REMOTE_HOST)

                #Start video source
                self .video = VideoStream ("sample.avi")
                #self .video = VideoStream ()
                self .audio = AudioStream ()

                #Send own metadata
                own_frame_shape = self .video .get_frame_shape ()
                own_key = self .cipher .get_new_key ()
                print ("Sending Metadata", [own_frame_shape, own_key])
                own_metadata = self .cipher .encrypt (pickle .dumps ([own_frame_shape, own_key]))
                conn_metadata .sendall (own_metadata)
                
                #Get client metadata
                remote_metadata = conn_metadata .recv (300)
                remote_frame_shape, remote_key = pickle .loads (self .cipher .decrypt (remote_metadata))
                print ("Received Metadata", [remote_frame_shape, remote_key])

                self .video .set_remote_frame_shape (remote_frame_shape)
                self .cipher .update_own_cipher (own_key)
                self .cipher .update_remote_cipher (remote_key)

                #make audio video channels
                conn_video = self .comm .connect_to (self .REMOTE_HOST, self .PORT_VID)
                conn_audio = self .comm .connect_to (self .REMOTE_HOST, self .PORT_AUD)

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
                player = Player (self .audio, self .video, "S")
                player .play ()

                #clean up
                print ("Cleaning up")
                conn_metadata .close ()
                sock_metadata .close ()
                conn_video .close ()
                conn_audio .close ()

            except KeyboardInterrupt as ki :
                print ("\r[Se] Breaking Server", ki)
                conn_metadata .close ()
                sock_metadata .close ()
                conn_video .close ()
                conn_audio .close ()
                break

            except socket .error as msg:
                print ("\r[Se] Program ended, socket closed", msg)
                self .video .stop ()
                self .comm .stop ()

            except Exception as e:
                sock_metadata .close ()
                print (e)
                traceback .print_exc ()


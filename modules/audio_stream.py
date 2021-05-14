import pyaudio
import numpy as np
import base64
import traceback
import noisereduce as nr

from modules .params import * 

class AudioStream :
    def __init__ (self) :
        self .INTERVAL = AUDIO_FRAME_INTERVAL
        self .audio = pyaudio .PyAudio()
        self .captured = True
        
        self .in_stream = self .audio .open (format = FORMAT, channels = CHANNELS,
                        rate = RATE, input = True,
                        frames_per_buffer = CHUNK)
        self .out_stream = self .audio .open (format = FORMAT, channels = CHANNELS,
                        rate = RATE, output = True)

        self .stream = self .audio_stream ()
        self .remote_frame = b''
        self .previous_frame = b''
        self .latest_frame = b''

    def audio_stream (self) :
        while self .captured :
            yield (self .in_stream .read (CHUNK))

    def get_next_frame (self) :
        self .previous_frame = self .latest_frame
        self .latest_frame = next (self .stream)
        return self .latest_frame

    def store_frame (self, frame) :
        self .remote_frame = frame

    def get_data_to_send (self) :
        self .latest_frame = self .get_next_frame ()
        data = base64 .b64encode (self .latest_frame)
        return data
  
    def process_received_data (self, data) :
        frame = base64 .b64decode (data)
        self .store_frame (frame)

    def get_output (self) :
        try:
            audio = np .fromstring (self .remote_frame)
            noise = np .fromstring (self .previous_frame)
            recovered = nr .reduce_noise (audio_clip = audio, noise_clip = noise) 
            return recovered .tostring ()
        except Exception as e :
            print ("Exception while reducing noise, sending noisy frame [MSG]", e)
            #traceback .print_exc ()
            return self .remote_frame

    def render (self) :
        self .out_stream .write (self .get_output ())

    def rendering (self) :
        try :
            while (self .captured) :
                self .render ()
        except Exception as e :
            print ("[A] Rendering ended", e)
            traceback .print_exc ()
            self .stop ()

    def release (self) :
        if self .captured :
            self .in_stream .stop_stream ()
            self .out_stream .stop_stream ()
            self .in_stream .close ()
            self .out_stream .close ()
            self .audio .terminate ()
            print ("[A] Release audio source")
    
    def stop (self) :
        self .release ()
        self .captured =  False

    def __exit__ (self) :
        self .stop ()


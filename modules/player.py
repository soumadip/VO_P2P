from threading import Thread

class Player :
    def __init__ (self, astream, vstream, title = 'VIDEO FEED') :
        self .audio_stream = astream
        self .video_stream = vstream
        self .title = title

    def play (self) :
        audio_player = Thread (target = self .audio_stream .rendering, args =())
        audio_player .start ()
        self .video_stream .rendering (self .title)

# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 20:08:40 2019

@author: masavoyat
"""

#!/usr/bin/python
from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn
import struct
import time
import math
import queue


class HTTPStreamServer(ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self._receiverList = list()
        
    def appendReceiver(self, receiver):
        self._receiverList.append(receiver)
    
    def removeReceiver(self, receiver):
        if receiver in self._receiverList:
            self._receiverList.remove(receiver)
    
    def close(self):
        for receiver in self._receiverList:
            self.removeReceiver(receiver)
        self.socket.close()
        

#This class will handles any incoming request from
#the browser 
class streamRequestHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        print(self.server._receiverList)
        print(self.path)
        for receiver in self.server._receiverList:
            if self.path == ("/"+receiver.name):
                q = queue.Queue(10)
                receiver.registerQueue(q)
                try:
                    data = q.get(block=True, timeout=1)
                except queue.Empty:
                    data = None
                if not data: # Queue empty or receiver closing
                    self.send_response(204) # no content
                    self.send_header('Content-type','audio/wav')
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header('Content-type','audio/wav')
                self.end_headers()
                _, payloadType, seq_number, timestamp, samplingFreq = struct.unpack(">BBHII", data[0:12])
                if payloadType == 127:
                    sample_size = 2
                else:
                    sample_size = 1
                # [Bloc de déclaration d'un fichier au format WAVE]
                self.wfile.write(b"RIFF") # FileTypeBlocID
                self.wfile.write(struct.pack('<I', 0xffffffff)) # FileSize => Max
                self.wfile.write(b"WAVE") # FileFormatID
                # [Bloc décrivant le format audio]
                self.wfile.write(b"fmt ") # FormatBlocID
                self.wfile.write(struct.pack('<I', 16)) # FileSize
                self.wfile.write(struct.pack('<H', 1)) # AudioFormat 1:PCM
                self.wfile.write(struct.pack('<H', 1)) # NbrCanaux
                self.wfile.write(struct.pack('<I', samplingFreq)) # Frequence
                self.wfile.write(struct.pack('<I', samplingFreq*sample_size)) # BytePerSec
                self.wfile.write(struct.pack('<H', sample_size)) # BytePerBloc
                self.wfile.write(struct.pack('<H', sample_size*8)) # BitsPerSample
                # [Bloc des données]
                self.wfile.write(b"data") # DataBlocID
                self.wfile.write(struct.pack('<I', 0xffffffff)) # DataSize => Max
                while True:
                    try:
                        data = q.get()        
                        _, newPayloadType, _, _, newSamplingFreq = struct.unpack(">BBHII", data[0:12])
                        if payloadType != newPayloadType or samplingFreq != newSamplingFreq: # Critical stream parameter changed
                            return
                        if not data: # receiver send None so it is closing
                            return
                        self.wfile.write(data[12:])
                    except:
                        print("Stream closed")
                        return
        if self.path == "/tone":
            self.send_response(200)
            self.send_header('Content-type','audio/wav')
            self.end_headers()
            audio_size = 128*1024
            sample_size = 2
            sampling_freq = 48000
            f = 440
            s = [0.1*(2**15)*math.sin(2*math.pi*f*i/sampling_freq) for i in range(audio_size)]
            # [Bloc de déclaration d'un fichier au format WAVE]
            self.wfile.write(b"RIFF") # FileTypeBlocID
#            self.wfile.write(struct.pack('<I', sample_size*audio_size+36)) # FileSize
            self.wfile.write(struct.pack('<I', 0xffffffff)) # FileSize
            self.wfile.write(b"WAVE") # FileFormatID
            # [Bloc décrivant le format audio]
            self.wfile.write(b"fmt ") # FormatBlocID
            self.wfile.write(struct.pack('<I', 16)) # FileSize
            self.wfile.write(struct.pack('<H', 1)) # AudioFormat 1:PCM
            self.wfile.write(struct.pack('<H', 1)) # NbrCanaux
            self.wfile.write(struct.pack('<I', sampling_freq)) # Frequence
            self.wfile.write(struct.pack('<I', sampling_freq*2)) # BytePerSec
            self.wfile.write(struct.pack('<H', 2)) # BytePerBloc
            self.wfile.write(struct.pack('<H', 16)) # BitsPerSample
            
            self.wfile.write(b"data") # DataBlocID
            self.wfile.write(struct.pack('<I', 0xffffffff)) # DataSize
            for j in range(100):
#                self.wfile.write(b"data") # DataBlocID
#                self.wfile.write(struct.pack('<I', sample_size*audio_size)) # DataSize
                b = bytearray(audio_size*sample_size)
                for i in range(audio_size):
        #            self.wfile.write(bytes(sample_size))
                    b[2*i] = int(s[i]) & 0xff
                    b[2*i+1] = (int(s[i])>>8) & 0xff
                print("Send data")
                try:
                    self.wfile.write(b)
                except:
                    print("Stream closed")
                    return
                time.sleep(3)
            
#        if self.path == "/":
#            self.send_response(200)
#            self.send_header('Content-type',"text/html")
#            self.end_headers()
#            self.wfile.write(b'<audio autoplay controls style="width:100%; height:40px;" src="audio.wav"></audio>')
        else:
            self.send_response(404)
            self.end_headers()
        return

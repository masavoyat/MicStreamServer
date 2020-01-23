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
        self.socket.close()
        

#This class will handles any incoming request from
#the browser 
class streamRequestHandler(BaseHTTPRequestHandler):
    
    def send_stream_as_wav(self, receiver):
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
                    receiver.unregisterQueue(q)
                    return
                if not data: # receiver send None so it is closing
                    receiver.unregisterQueue(q)
                    return
                self.wfile.write(data[12:])
            except:
                receiver.unregisterQueue(q)
                print("Stream closed")
                return
    
    def send_tone_as_wav(self):
        self.send_response(200)
        self.send_header('Content-type','audio/wav')
        self.end_headers()
        audio_size = 48000
        sample_size = 2
        sampling_freq = 48000
        f = 480
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
            b = bytearray(audio_size*sample_size)
            for i in range(audio_size):
                b[2*i] = int(s[i]) & 0xff
                b[2*i+1] = (int(s[i])>>8) & 0xff
            try:
                self.wfile.write(b)
            except:
                print("Stream closed")
                return
            time.sleep(1)
    
    def stream_list_page(self):  
        self.send_response(200)
        self.send_header('Content-type',"text/html")
        self.end_headers()
        self.wfile.write(b'<table border="1">')
        self.wfile.write(b'<tr>')
        line = '<th>Stream Name</th>'
        line += '<th>Port</th>'
        line += '<th>Sampling Freq</th>'
        line += '<th>Alive</th>'
        line += '<th>Payload Type</th>'
        line += '<th>Registered queue</th>'
        line += '<th>Wav stream</th>'
        self.wfile.write(line.encode())
        self.wfile.write(b'</tr>')
        for receiver in self.server._receiverList:
            infos = receiver.getInfos()
            self.wfile.write(b'<tr>')
            line = "<td>" + infos["name"] + "</td>"
            line += "<td>" + str(infos["port"]) + "</td>"
            line += "<td>" + str(infos["sampling_frequency"]) + "</td>"
            if infos["last_packet_time"] < time.time() - 1:
                line += "<td>NO</td>"
            else:
                line += "<td>YES</td>"
            line += "<td>" + receiver.PAYLOAD_TYPES_STR[infos["payload_type"]] + "</td>"
            line += "<td>" + str(infos["registered_queue"]) + "</td>"
            line += '<td><a href="/' + infos["name"] + '">WAV</a></td>'
            self.wfile.write(line.encode())
            self.wfile.write(b'</tr>')
        self.wfile.write(b'</table>')  
    
    def do_GET(self):
        #print(self.path)
        for receiver in self.server._receiverList:
            if self.path == ("/"+receiver.name):
                self.send_stream_as_wav(receiver)
                return
        if self.path == "/tone":
            self.send_tone_as_wav()
            return
        if self.path == "/":
            self.stream_list_page()
            return
        self.send_response(404)
        self.end_headers()

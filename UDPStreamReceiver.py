# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 13:52:52 2019

@author: masavoyat
"""
import socket
import threading


class UDPStreamReceiver:
    _BUFFER_SIZE = 1024
    def __init__(self, udp_port, udp_ip="", name=None):
        if name:
            self.name = name
        else:
            self.name = str(udp_port)
        self._thread = threading.Thread(target=self._main_loop)
        self._registeredQueueList = list()
        self._registeredQueueListLock = threading.Lock()
        self._sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
        self._sock.bind((udp_ip, udp_port))
        self._thread.start()
        
    def registerQueue(self, q):
        self._registeredQueueListLock.acquire()
        self._registeredQueueList.append(q)
        self._registeredQueueListLock.release()
        
    def unregisterQueue(self, q):
        self._registeredQueueListLock.acquire()
        if q in self._registeredQueueList:
            self._registeredQueueList.remove(q)
        self._registeredQueueListLock.release()
        
    def _main_loop(self):
        while True:
            try:
                data, addr = self._sock.recvfrom(UDPStreamReceiver._BUFFER_SIZE)
            except:
                data = None # Send None data to advertise socket is dead
            self._registeredQueueListLock.acquire()
            for q in self._registeredQueueList:
                if q.full():
                    q.get_nowait()
                q.put_nowait(data)
            self._registeredQueueListLock.release()
            if not data:
                return
    
    def close(self):
        self._registeredQueueListLock.acquire()
        self._sock.close()
        self._registeredQueueListLock.release()
    
            
            
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 14:09:39 2019

@author: masavoyat
"""

import UDPStreamReceiver
import queue
import time

sr = UDPStreamReceiver.UDPStreamReceiver(2222)

q = queue.Queue(10)
sr.registerQueue(q)

try:
    while True:
        if q.empty():
            time.sleep(1e-3)
        else:
            print(q.get())
except KeyboardInterrupt:
    pass

sr.unregisterQueue(q)
sr.close()
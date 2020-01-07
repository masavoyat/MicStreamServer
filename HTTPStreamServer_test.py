# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 14:59:14 2019

@author: masavoyat
"""

import HTTPStreamServer
import UDPStreamReceiver

PORT_NUMBER = 8080


try:
    #Create a web server and define the handler to manage the
    #incoming request
    server = HTTPStreamServer.HTTPStreamServer(('', PORT_NUMBER), HTTPStreamServer.streamRequestHandler)
    print('Started httpserver on port ' + str(PORT_NUMBER))
    sr1 = UDPStreamReceiver.UDPStreamReceiver(2222)
    server.appendReceiver(sr1)
    sr2 = UDPStreamReceiver.UDPStreamReceiver(2221)
    server.appendReceiver(sr2)
    print("Started stream receivers")
    
    #Wait forever for incoming htto requests
    server.serve_forever()

except KeyboardInterrupt:
    print('Shutting stream receivers')
    sr1.close()
    sr2.close()
    print('Shutting down the web server')
    server.close()
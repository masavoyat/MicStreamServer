# -*- coding: utf-8 -*-
"""
Created on Thu Jan 16 14:17:53 2020

@author: masavoyat
"""

import HTTPStreamServer
import UDPStreamReceiver
import argparse
import sys
import json

parser = argparse.ArgumentParser(description='MicStreamServer application')
parser.add_argument("-f", dest="filepath",
                    help='.json file containing the server configuration',
                    default="config.json")
args = parser.parse_args()
try:
    config_file = open("config.json")
    config_file_content = config_file.read()
    config_file.close()
    config = json.loads(config_file_content.replace("'", "\""))
except FileNotFoundError: 
    sys.exit()

if not "serverPort" in config.keys():
    config["serverPort"] = 8080
if not "streams" in config.keys():
    config["streams"] = list()

sr_list = list()
try:
    #Create a web server and define the handler to manage the
    #incoming request
    server = HTTPStreamServer.HTTPStreamServer(('', config["serverPort"]),
                                               HTTPStreamServer.streamRequestHandler)
    print('Started httpserver on port ' + str(config["serverPort"]))
    for stream in config["streams"]:
        if not "name" in stream.keys():
            stream["name"] = str(stream["port"])
        sr = UDPStreamReceiver.UDPStreamReceiver(stream["port"],
                                                 name=stream["name"])
        server.appendReceiver(sr)
        sr_list.append(sr)
        print("Started stream receiver " + stream["name"] +
              " on port: " + str(stream["port"]))
    
    #Wait forever for incoming htto requests
    server.serve_forever()

except KeyboardInterrupt:
    print('Shutting down stream receivers')
    for sr in sr_list:
        sr.close()
    print('Shutting down the web server')
    server.close()
#! /usr/bin/env python3

import http.server
import socketserver
import json
import time
import os


CONFIG_NAME = 'config.json'
LISTEN_ALL = "0.0.0.0"

DEF_NAME = "Environment sensor exporter"
DEF_PORT = 9902
DEF_CACHE = 30

# global values
obj_config = None
obj_module = None


class PESHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    global obj_config
    global obj_module

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        self.wfile.write(b"# HELP tmp_files Num files in /tmp.\n")
        self.wfile.write(b"# TYPE tmp_files gauge\n")
        v = str(metrics["tmp_files"]).encode()
        self.write.write(b"tmp_files " + v + b"\n")


if __name__ == "__main__":
    print("Loading configuration")
    try:
        fconf = open(CONFIG_NAME, 'r')
    except IOError as e:
        raise Exception("File '{}' open error: {}".format(CONFIG_NAME, e))
    try:
        obj_config = json.load(fconf)
    except:
        raise Exception("json format parse error for '{}'".format(CONFIG_NAME))
    if not "server_name" in obj_config:
        obj_config["server_name"] = DEF_NAME
    if not "port" in obj_config:
        obj_config["port"] = DEF_PORT
    if not "cache" in obj_config:
        obj_config["cache"] = DEF_CACHE
    print("Initializing modules")
    print("Starting server")
    Handler = PESHTTPRequestHandler
    with socketserver.TCPServer((LISTEN_ALL, obj_config["port"]), Handler) as httpd:
        print("Serving at " + str(obj_config["port"]))
        httpd.serve_forever()


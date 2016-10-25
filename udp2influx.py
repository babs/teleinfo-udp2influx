#!/usr/bin/python
"""Listen for teleinfo UDP frames and store them into InfluxDB"""

import json
import logging
import os
import socket
from time import sleep
import urllib2

from Colorize import init_root_logger

init_root_logger()
log = logging.getLogger("udp2influx")

def trame2influx(unxts, trame):
    "Convert a frame to influx line protocol"
    tramedict = dict(
        map(
            lambda x: x.replace('\x02\n', '').split(" ")[:2],
            trame.split("\r\n")
        )
    )
    try:
        return "teleinfo papp=%(papp)d,iinst=%(iinst)d,hchc=%(hchc)d,hchp=%(hchp)d %(ts)d" % {
            'ts': unxts,
            'papp': int(tramedict['PAPP'], 10),
            'iinst': int(tramedict['IINST'], 10),
            'hchc': int(tramedict['HCHC'], 10),
            'hchp': int(tramedict['HCHP'], 10),
        }
    except Exception, exc:
        log.error(exc)
        print unxts
        print trame
        return None

def writelines(influxurl, payload, attempts=2):
    "Write the given line to influxdb instance"
    try:
        log.debug("Wrinting to influxdb: %s", payload)
        req = urllib2.Request(
            influxurl,
            payload)
        filep = urllib2.urlopen(req)
        filep.read()
        filep.close()
    except Exception, exc:
        if attempts == 0:
            log.fatal("Last attempt failed.", exc_info=True)
            raise exc
        else:
            log.warning("error while trying to save records (attempt %d).",
                        3 - attempts,
                        exc_info=True)
            sleep(1)
            writelines(payload, attempts - 1)

def main():
    "Main func."
    log.setLevel(int(os.environ.get('DEBUGLEVEL', "20")))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(
        (os.environ.get("LISTEN_IP", ""),
         int(os.environ.get("LISTEN_PORT", "2101")))
    )
    log.info("Listen to %s:%s",
             os.environ.get("LISTEN_IP", ""),
             os.environ.get("LISTEN_PORT", "2101"))
    influxurl = "http://%s/write?db=%s" % (
        os.environ.get("INFLUX_HOST", "localhost:8086"),
        os.environ.get("INFLUX_DATABASE", "teleinfo"))
    log.info("Will write to %s", influxurl)
    # Main loop
    while True:
        data, _ = sock.recvfrom(1500)
        jsondata = json.loads(data)
        writelines(
            influxurl,
            trame2influx(
                int(float(jsondata['tramets']) * 1000000) * 1000,
                jsondata['trame']))

if __name__ == "__main__":
    main()

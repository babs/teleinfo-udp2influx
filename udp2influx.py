#!/usr/bin/python

import lzma, json, glob, sys, os, urllib2, datetime, socket
from pprint import pprint
from Colorize import init_root_logger
from decimal import Decimal
from time import sleep
import logging

init_root_logger()
log = logging.getLogger("udp2influx")

def trame2influx(ts, trame):
    tramedict = dict(
        map(
            lambda x: x.replace('\x02\n', '').split(" ")[:2],
            trame.split("\r\n")
        )
    )
    try:
        return "teleinfo papp=%(papp)d,iinst=%(iinst)d,hchc=%(hchc)d,hchp=%(hchp)d %(ts)d" % {
        'ts': ts,
        'papp': int(tramedict['PAPP'], 10),
        'iinst': int(tramedict['IINST'], 10),
        'hchc': int(tramedict['HCHC'], 10),
        'hchp': int(tramedict['HCHP'], 10),
        }
    except Exception, e:
        log.error(e)
        print ts
        print trame
        return None

def writelines(payload, attempts=2):
    try:
        log.debug("Wrinting to influxdb: %s", payload)
        req = urllib2.Request(
                              "http://%s/write?db=%s" %
                                  (os.environ.get("INFLUX_HOST", "localhost:8086"),
                                   os.environ.get("INFLUX_DATABASE", "teleinfo")),
                               payload)
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
    except Exception, e:
        if attempts == 0:
            log.fatal("Last attempt failed.", exc_info=True)
            raise e
        else:
            log.warning("error while trying to save records, waiting 30 sec then retry (attempt %d).", 3 - attempts, exc_info=True)
            sleep(1)
            writelines(payload, attempts - 1)

def main():
    log.setLevel(int(os.environ.get('DEBUGLEVEL', "20")))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(
              (os.environ.get("LISTEN_IP", ""),
               int(os.environ.get("LISTEN_PORT", "2101")))
              )
    log.info("Listen to %s:%s", os.environ.get("LISTEN_IP", ""), os.environ.get("LISTEN_PORT", "2101"))
    # Main loop
    while True:
        data, remote = sock.recvfrom(1500)
        jsondata = json.loads(data)
        writelines(trame2influx(int(float(jsondata['tramets']) * 1000000) * 1000, jsondata['trame']))
    pass


if __name__ == "__main__":
    main()

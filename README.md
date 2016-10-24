# teleinfo-udp2influx

Listen to a given UDP port (dft: 2101) for teleinfo frames sent by [teleinfo-sender] and write them to InfluxDB.

* `INFLUX_HOST`: InfluxDB host, format: ip:port, default: localhost:8086
* `INFLUX_DATABASE`: DB to write to, default: teleinfo
* `LISTEN_IP`: ip to listen on, default: '' (all)
* `LISTEN_PORT`: post to listen on, default: 2101


[teleinfo-sender]: https://github.com/babs/teleinfo-sender

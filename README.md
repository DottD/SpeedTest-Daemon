# SpeedTest Daemon

[speedtest_daemon.py](speedtest_daemon.py) is a Python script that starts a daemon that periodically monitors a number of IPs, tracking latency, upload and download speed.

## Usage

Using the daemon is simple: just run the following command:

```bash
python speedtest_daemon.py <time> -o <output> -d <delay> --IPs <json>
```

where:

* _time_ is the time (in seconds) the daemon should live.
* _output_ is a path and basename to the output file (extension should not be included).
* _delay_ time (in seconds) between two consecutive measurements.
* _json_ is the path to a JSON file that contains a {name: IP-address} map (see [IPs.json](IPs.json) for an example).

## Tests

Since this was only a side project, this repository has no tests.

## Contributing

Each contribution is very much appreciated.

## Authors

* [__Filippo Santarelli__](https://github.com/DottD) - Initial work

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

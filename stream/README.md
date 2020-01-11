# Stream for Puzzle Massive

The puzzle-massive-stream.service should be placed in /etc/systemd/system/ in order to function. Note that this is commonly done by the install script.

```
sudo cp puzzle-massive-stream.service /etc/systemd/system/
```

Start and enable the service.

```
sudo systemctl start puzzle-massive-stream
sudo systemctl enable puzzle-massive-stream
```

Stop the service.

```
sudo systemctl stop puzzle-massive-stream
```

View the end of log.

```
sudo journalctl --pager-end _SYSTEMD_UNIT=puzzle-massive-stream.service
```

Follow the log.

```
sudo journalctl --follow _SYSTEMD_UNIT=puzzle-massive-stream.service
```

View details about service.

```
sudo systemctl show puzzle-massive-stream
```

Check the status of the service.

```
sudo systemctl status puzzle-massive-stream.service
```

Reload if puzzle-massive-stream.service file has changed.

```
sudo systemctl daemon-reload
```

# API for Puzzle Massive

The puzzle-massive-api.service should be placed in /etc/systemd/system/ in order to function. Note that this is commonly done by the install script.

```
sudo cp puzzle-massive-api.service /etc/systemd/system/
```

Start and enable the service.

```
sudo systemctl start puzzle-massive-api
sudo systemctl enable puzzle-massive-api
```

Stop the service.

```
sudo systemctl stop puzzle-massive-api
```

View the end of log.

```
sudo journalctl --pager-end _SYSTEMD_UNIT=puzzle-massive-api.service
```

Follow the log.

```
sudo journalctl --follow _SYSTEMD_UNIT=puzzle-massive-api.service
```

View details about service.

```
sudo systemctl show puzzle-massive-api
```

Check the status of the service.

```
sudo systemctl status puzzle-massive-api.service
```

Reload if puzzle-massive-api.service file has changed.

```
sudo systemctl daemon-reload
```


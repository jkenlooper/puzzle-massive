# Chill app for puzzle-massive

The puzzle-massive-chill.service should be placed in /etc/systemd/system/ in order to function. Note that this is commonly done by the install script.

```
sudo cp puzzle-massive-chill.service /etc/systemd/system/
```

Start and enable the service.

```
sudo systemctl start puzzle-massive-chill
sudo systemctl enable puzzle-massive-chill
```

Stop the service.

```
sudo systemctl stop puzzle-massive-chill
```

View the end of log.

```
sudo journalctl --pager-end _SYSTEMD_UNIT=puzzle-massive-chill.service
```

Follow the log.

```
sudo journalctl --follow _SYSTEMD_UNIT=puzzle-massive-chill.service
```

View details about service.

```
sudo systemctl show puzzle-massive-chill
```

Check the status of the service.

```
sudo systemctl status puzzle-massive-chill.service
```

Reload if puzzle-massive-chill.service file has changed.

```
sudo systemctl daemon-reload
```

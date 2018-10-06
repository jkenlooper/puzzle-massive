# Divulger for Puzzle Massive

The puzzle-massive-divulger.service should be placed in /etc/systemd/system/ in order to function. Note that this is commonly done by the install script.

```
sudo cp puzzle-massive-divulger.service /etc/systemd/system/
```

Start and enable the service.

```
sudo systemctl start puzzle-massive-divulger
sudo systemctl enable puzzle-massive-divulger
```

Stop the service.

```
sudo systemctl stop puzzle-massive-divulger
```

View the end of log.

```
sudo journalctl --pager-end _SYSTEMD_UNIT=puzzle-massive-divulger.service
```

Follow the log.

```
sudo journalctl --follow _SYSTEMD_UNIT=puzzle-massive-divulger.service
```

View details about service.

```
sudo systemctl show puzzle-massive-divulger
```

Check the status of the service.

```
sudo systemctl status puzzle-massive-divulger.service
```

Reload if puzzle-massive-divulger.service file has changed.

```
sudo systemctl daemon-reload
```


#!/bin/bash
lncli stop
sudo systemctl stop lnd.service
bitcoin-cli stop
sudo systemctl stop bitcoind.service
sudo reboot

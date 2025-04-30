#!/bin/bash

backup_machine_ssh="<ssh_key>"
machine_username="<username>"
backup_ip="<ip_backup_server>"

scp -i $backup_machine_ssh -r ~/backup/saves/server $machine_username@$backup_ip:/home/$machine_username/
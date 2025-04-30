#!/bin/bash

backup_machine_ssh="<ssh_key>"
machine_username="<username>"
backup_ip="<ip_backup_server>"

scp -i $backup_machine_ssh -p -r $machine_username@$backup_ip:~/server ~/backup/saves
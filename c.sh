#!/bin/bash

# alias ll='ls -la'
# wget http://192.168.0.90/code/auto/c.sh
# chmod +x c.sh
# ./c.sh




for f in c.sh auto_depl.py
  do
    echo ${f}
    curl http://192.168.0.90/code/auto/${f} >${f}
    chmod +x ${f}
  done

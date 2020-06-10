#!/bin/bash

# alias ll='ls -la'
# wget http://192.168.0.90/code/ge-tools/c.sh
# chmod +x c.sh
# ./c.sh
# start python web Server
# python -m http.server 8000


for f in c.sh auto_depl.py
  do
    echo ${f}
    curl http://192.168.0.90/code/ge-tools/${f} >${f}
    chmod +x ${f}
  done

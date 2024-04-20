#!/bin/sh
export PATH=$PATH:/sbin
gunicorn --bind maa-pe-kvm-slc-08vm001.us.oracle.com:5000 --preload --timeout 3000 --graceful-timeout 2000  -k gevent -w 5 LrgRankingApp:app&

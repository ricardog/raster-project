#!/bin/sh

tightvncserver -name trampoline -geometry 1600x1024 -depth 24 :0
xhost +
sleep 1
cat /home/vncuser/.vnc/*.log
pid=`cat /home/vncuser/.vnc/*.pid`
echo "Waiting for pid ${pid} to finish"
tail --pid=${pid} -f /dev/null
#sleep 10000    

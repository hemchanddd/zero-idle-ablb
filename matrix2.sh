#!/bin/bash
set -e
cd ~/zero-idle-research
sudo rm -f /tmp/fc_*.sock
podman rm -f $(podman ps -aq) 2>/dev/null || true
python3 drive.py pcold 5 60 pcold_r5
podman rm -f $(podman ps -aq) 2>/dev/null || true
sleep 3
sudo python3 drive.py fc 5 60 fc_r5
sudo rm -f /tmp/fc_*.sock
sleep 3
sudo python3 drive.py fc 10 60 fc_r10
sudo rm -f /tmp/fc_*.sock
sudo chown hemchand:hemchand results/sustained_fc_*.csv
sleep 3
stress-ng --vm 4 --vm-bytes 6G -t 200s &
STRESS_PID=$!
sleep 3
python3 lb2.py --tag sustained_unik_ctrl_stress &
LB_PID=$!
sleep 2
python3 drive.py unik 20 60 ctrl_stress_r20
kill $LB_PID
wait $LB_PID 2>/dev/null || true
python3 lb2.py --uncontrolled --tag sustained_unik_unctrl_stress &
LB_PID=$!
sleep 2
python3 drive.py unik 20 60 unctrl_stress_r20
kill $LB_PID
wait $LB_PID 2>/dev/null || true
kill $STRESS_PID 2>/dev/null || true
ls results/sustained_*.csv


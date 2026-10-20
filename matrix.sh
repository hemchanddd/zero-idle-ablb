#!/bin/bash
set -e
cd ~/zero-idle-research
sudo rm -f /tmp/fc_*.sock
python3 lb2.py --tag sustained_unik_ctrl &
LB_PID=$!
sleep 2
python3 drive.py unik 20 60 ctrl_r20
python3 drive.py unik 40 60 ctrl_r40
kill $LB_PID
wait $LB_PID 2>/dev/null || true
python3 lb2.py --uncontrolled --tag sustained_unik_unctrl &
LB_PID=$!
sleep 2
python3 drive.py unik 20 60 unctrl_r20
python3 drive.py unik 40 60 unctrl_r40
kill $LB_PID
wait $LB_PID 2>/dev/null || true
python3 drive.py warm 20 60 warm_r20
python3 drive.py warm 40 60 warm_r40
python3 drive.py pcold 10 60 pcold_r10
python3 drive.py pcold 20 60 pcold_r20
sudo python3 drive.py fc 10 60 fc_r10
sudo python3 drive.py fc 20 60 fc_r20
sudo chown hemchand:hemchand results/sustained_fc_*.csv
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

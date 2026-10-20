#!/bin/bash
set -e
cd ~/zero-idle-research
stress-ng --vm 4 --vm-bytes 6G -t 160s &
STRESS=$!
sleep 3
python3 lb2.py --tag sustained_unik_ctrl_stress &
LB=$!
sleep 2
python3 drive.py unik 10 60 ctrl_stress_r10
kill $LB
wait $LB 2>/dev/null || true
python3 lb2.py --uncontrolled --tag sustained_unik_unctrl_stress &
LB=$!
sleep 2
python3 drive.py unik 10 60 unctrl_stress_r10
kill $LB
wait $LB 2>/dev/null || true
kill $STRESS
wait $STRESS 2>/dev/null || true
ls results/sustained_unik_*stress*

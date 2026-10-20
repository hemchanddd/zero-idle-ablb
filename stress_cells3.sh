#!/bin/bash
set -e
cd ~/zero-idle-research
stress-ng --vm 4 --vm-bytes 12G -t 45s &
ST=$!
sleep 3
python3 lb2.py --lmin 2 --tag sustained_unik_ctrl_p3 &
LB=$!
sleep 2
python3 drive.py unik 10 30 ctrl_p3_r10
kill $LB
wait $LB 2>/dev/null || true
kill $ST
wait $ST 2>/dev/null || true
ls results/*_p3_*

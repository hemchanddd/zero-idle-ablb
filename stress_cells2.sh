#!/bin/bash
set -e
cd ~/zero-idle-research
run_cell() {
    mode=$1
    tag=$2
    stress-ng --vm 4 --vm-bytes 12G -t 45s &
    ST=$!
    sleep 3
    if [ "$mode" = "ctrl" ]; then
        python3 lb2.py --tag "$tag" &
    else
        python3 lb2.py --uncontrolled --tag "$tag" &
    fi
    LB=$!
    sleep 2
    python3 drive.py unik 10 30 "${tag#sustained_unik_}_r10"
    kill $LB
    wait $LB 2>/dev/null || true
    kill $ST
    wait $ST 2>/dev/null || true
    sleep 2
}
run_cell unctrl sustained_unik_unctrl_p2
run_cell ctrl sustained_unik_ctrl_p2
ls results/*_p2_*

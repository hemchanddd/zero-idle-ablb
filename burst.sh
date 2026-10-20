#!/bin/bash
for i in $(seq 6); do
    curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://127.0.0.1:8000/ &
done
wait

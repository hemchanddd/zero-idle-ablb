#!/bin/bash
CONCURRENCY=${1:-40}
echo "Sending $CONCURRENCY concurrent requests..."
START=$(date +%s%N)
rm -f curl_results.txt
for i in $(seq $CONCURRENCY); do
    curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/ >> curl_results.txt &
done
wait
END=$(date +%s%N)
SUCCESS=$(grep -c 200 curl_results.txt)
FAIL=$((CONCURRENCY - SUCCESS))
echo "Successes: $SUCCESS"
echo "Failures: $FAIL"
echo "Total time: $(( (END - START) / 1000000 )) ms"

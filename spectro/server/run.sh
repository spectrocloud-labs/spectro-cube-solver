#!/bin/bash

BASE_URL="http://192.168.7.235:8000"
scramb=0
solv=0

while true; do
  scramb=$((scramb + 1))
  echo "Sending scramble cycle $scramb..."
  curl -s -X POST -H "Content-Type: application/json" \
       -d "{\"scramb_cycle\": $scramb}" \
       "$BASE_URL/scramble"
  echo ""
  sleep 15

  solv=$((solv + 1))
  echo "Sending solve cycle $solv..."
  curl -s -X POST -H "Content-Type: application/json" \
       -d "{\"solv_cycle\": $solv}" \
       "$BASE_URL/solve"
  echo ""
  sleep 5
done


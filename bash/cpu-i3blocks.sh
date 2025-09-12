#!/bin/sh
PREV=$(awk '/^cpu / {print $2,$3,$4,$5,$6,$7,$8}' /proc/stat)
sleep 0.5
CURR=$(awk '/^cpu / {print $2,$3,$4,$5,$6,$7,$8}' /proc/stat)

set -- $PREV
U1=$1; N1=$2; S1=$3; I1=$4; W1=$5; H1=$6; SI1=$7
set -- $CURR
U2=$1; N2=$2; S2=$3; I2=$4; W2=$5; H2=$6; SI2=$7

IDLE=$((I2 - I1))
BUSY=$(( (U2-U1)+(N2-N1)+(S2-S1)+(W2-W1)+(H2-H1)+(SI2-SI1) ))
TOTAL=$((IDLE+BUSY))

echo "CPU(s): $((100*BUSY/TOTAL))%"


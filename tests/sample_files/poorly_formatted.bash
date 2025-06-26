#!/bin/bash
# Poorly formatted bash script

function check_status(){
echo "Checking status..."
if[ $# -eq 0 ]
then
   echo "No arguments provided"
   exit 1
fi

local status=$1
case $status in
"active")echo "System is active";;
"inactive")  echo "System is inactive"  ;;
*)echo "Unknown status: $status";;
esac
}

# Bad variable usage
FILES=$(ls /tmp/*.log)
for f in $FILES
do
echo "Processing $f"
done
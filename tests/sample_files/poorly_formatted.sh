#!/bin/bash
# Poorly formatted shell script with various issues

function   process_files(){
    local dir=$1
    if[ -z "$dir" ]
then
echo "Error: directory not provided"
return 1
fi

   for file in $(ls $dir/*.txt)
  do
echo  "Processing: $file"
   if [ -f $file ];then
       cat $file | grep "important"  >results.txt
fi
done
}

VAR1=value1
VAR2="value2"   

   process_files   /tmp

# Function with bad practices
function bad_function() {
rm -rf $1/*
   test $? -eq 0&&echo "success"
}

# Missing quotes and other issues
for i in $(seq 1 10)
do
    echo $i
    [ $i -gt 5 ]&&break
done
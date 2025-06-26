#!/bin/zsh
# Poorly formatted zsh script

function zsh_function(){
local arr=(a b c d)
for item in ${arr[@]}
do
echo  "Item: $item"
done

# Bad practice
eval "echo hello world"

if[ -n "$1" ]
then
echo "First arg: $1"
fi
}

zsh_function "test"
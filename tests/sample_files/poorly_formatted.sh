#!/bin/bash
# Shell fixture for lint and format testing.

process_files() {
	local directory=$1
	if [ -z "$directory" ]; then
		echo "Error: directory not provided"
		return 1
	fi

	for file in "$directory"/*.txt; do
		[ -f "$file" ] || continue
		echo "Processing: $file"
		grep "important" "$file" >results.txt
	done
}

process_files /tmp

bad_function() {
	rm -rf "${1:?}"/*
	echo "success"
}

for i in $(seq 1 10); do
	echo "$i"
	[ "$i" -gt 5 ] && break
done

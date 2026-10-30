#!/bin/sh
# Record the bench sentences on the Pi 5 through PipeWire (benoit-bremaud/confiture#18).
# Usage, on the Pi 5: sh record.sh ~/stt-bench [adult|child]   (sentences.tsv copied there first;
# the optional speaker records only that speaker's sentences)
# Family voices: the folder stays on the Pi 5, never in the repository.
set -eu
dir=$1
speaker=${2:-}
while IFS="$(printf '\t')" read -r file sentence; do
  case $file in "$speaker"*) ;; *) continue ;; esac
  printf '\n%s\n  « %s »\nEntrée pour enregistrer (8 s ; attends 2 s avant de parler)… ' "$file" "$sentence"
  read -r _ </dev/tty
  timeout 8 parecord --rate=16000 --channels=1 --format=s16le --file-format=wav "$dir/$file" || true
done <"$dir/sentences.tsv"

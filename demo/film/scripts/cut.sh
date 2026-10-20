#!/usr/bin/env bash
# Cut a named clip out of a raw take into public/footage/ (gitignored).
# Usage: scripts/cut.sh <take.mov> <start mm:ss.s> <end mm:ss.s> <clip-name.mov> [crop w:h:x:y]
# Example: scripts/cut.sh public/footage/take1-screen.mov 00:12.0 00:26.5 s1-board.mov
set -euo pipefail
in="$1"; ss="$2"; to="$3"; out="public/footage/$4"; crop="${5:-}"
vf="scale=-2:1080:flags=lanczos,fps=30"
[ -n "$crop" ] && vf="crop=$crop,$vf"
ffmpeg -y -loglevel error -ss "$ss" -to "$to" -i "$in" -vf "$vf" -an -c:v libx264 -crf 16 -preset fast -pix_fmt yuv420p "$out"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$out" | xargs printf "%s: %ss\n" "$out"

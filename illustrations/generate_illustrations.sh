#!/usr/bin/env bash
# Render every illustration of the website and copy it into docs/.
#
# Usage (from anywhere):
#   illustrations/generate_illustrations.sh              # all globes and the logo
#   illustrations/generate_illustrations.sh axes logo    # only some of them
#   illustrations/generate_illustrations.sh --preview    # one PNG frame per globe, no copy
#
# Names: seismes, axes, maillage, satellites, magnetique (globe_<name>.py), logo.
# The globes render in parallel (about 1.5 min for all five instead of 2),
# each logging to illustrations/outputs/globe_<name>.log. Renders go to
# illustrations/outputs/, then:
#   - videos (.webm, .mov, .png poster) to docs/videos/,
#   - logos (.svg) to docs/images/logo/, and the dark logo (.png) as the favicon.

set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
docs="$(cd "$here/../docs" && pwd)"
outputs="$here/outputs"

preview=""
names=()
for arg in "$@"; do
    case "$arg" in
        --preview) preview="--preview" ;;
        -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
        *) names+=("$arg") ;;
    esac
done
[ ${#names[@]} -eq 0 ] && names=(seismes axes maillage satellites magnetique logo)

cd "$here"
mkdir -p "$outputs"
uv sync --quiet  # once, before the parallel runs

# Globes: all at once, in the background
globes=() pids=()
for name in "${names[@]}"; do
    [ "$name" = logo ] && continue
    if [ ! -f "globe_$name.py" ]; then
        echo "unknown illustration: $name" >&2
        exit 1
    fi
    echo "== globe_$name (log: outputs/globe_$name.log)"
    uv run --no-sync "globe_$name.py" $preview > "$outputs/globe_$name.log" 2>&1 &
    globes+=("$name") pids+=($!)
done

# Logo: fast, meanwhile
if [[ " ${names[*]} " == *" logo "* && -z "$preview" ]]; then
    echo "== logo"
    uv run --no-sync logo.py
    cp "$outputs/logo/logo_icon.svg" "$outputs/logo/logo_icon_light.svg" "$docs/images/logo/"
    cp "$outputs/logo/logo_icon.png" "$docs/images/logo/favicon.png"
fi

failed=0
for i in "${!globes[@]}"; do
    name="${globes[$i]}"
    if wait "${pids[$i]}"; then
        echo "done globe_$name"
        [ -z "$preview" ] && cp "$outputs/globe_$name".{webm,mov,png} "$docs/videos/"
    else
        echo "FAILED globe_$name, see outputs/globe_$name.log" >&2
        failed=1
    fi
done

[ -z "$preview" ] && [ $failed -eq 0 ] && echo "copied into docs/videos and docs/images/logo"
exit $failed

#!/bin/sh
# APPLY.sh <chunks-dir> <target-root> — decode a hand-pasted sync bundle.
# Reads MANIFEST.txt, finds each record in SYNC-*.txt, stages it and verifies
# bytes and sha256 before any write, refuses absolute or .. paths, prints one
# PASS/FAIL <path> line per manifest file, exits 0 only if all PASS.
# POSIX sh; idempotent.
set -u

if [ $# -ne 2 ] || [ ! -d "$1" ] || [ ! -f "$1/MANIFEST.txt" ]; then
	echo "usage: sh APPLY.sh <chunks-dir> <target-root>" >&2
	exit 2
fi
chunks=$1
target=$2
manifest=$chunks/MANIFEST.txt

if command -v sha256sum >/dev/null 2>&1; then
	sha_cmd="sha256sum"
else
	sha_cmd="shasum -a 256"
fi
if printf 'YQ==' | base64 -d >/dev/null 2>&1; then
	set -- base64 -d
elif printf 'YQ==' | base64 --decode >/dev/null 2>&1; then
	set -- base64 --decode
else
	set -- base64 -D
fi
b64_cmd=$1
b64_flag=$2

staging=$(mktemp -d) || exit 2
trap 'rm -rf "$staging"' EXIT

fails=0
while read -r want_sha want_bytes rel; do
	[ -n "${rel:-}" ] || continue
	bad=""
	case /$rel/ in
		//*) bad=absolute ;;
		*/../*|*/..) bad=dotdot ;;
	esac
	if [ -n "$bad" ]; then
		echo "FAIL $rel unsafe-path"
		fails=$((fails + 1))
		continue
	fi

	hdr=""
	chunk=""
	for f in "$chunks"/SYNC-*.txt; do
		[ -f "$f" ] || continue
		line=$(awk -v pat="BEGIN $rel " 'index($0, pat) == 1 { print; exit }' "$f")
		if [ -n "$line" ]; then hdr=$line; chunk=$f; break; fi
	done
	if [ -z "$hdr" ]; then
		echo "FAIL $rel no-record-in-chunks"
		fails=$((fails + 1))
		continue
	fi
	rest=${hdr#"BEGIN $rel "}
	rec_bytes=${rest%% *}
	rec_sha=${rest##* }
	if [ "$rec_bytes" != "$want_bytes" ] || [ "$rec_sha" != "$want_sha" ]; then
		echo "FAIL $rel manifest-mismatch"
		fails=$((fails + 1))
		continue
	fi

	awk -v b="BEGIN $rel " -v e="END $rel" \
		'index($0, b) == 1 { inb = 1; next } inb && $0 == e { exit } inb' \
		"$chunk" > "$staging/payload.b64"
	if [ -s "$staging/payload.b64" ]; then
		"$b64_cmd" "$b64_flag" < "$staging/payload.b64" > "$staging/payload" 2>/dev/null \
			|| { echo "FAIL $rel base64-decode"; fails=$((fails + 1)); continue; }
	else
		: > "$staging/payload"
	fi
	got_bytes=$(wc -c < "$staging/payload" | tr -d ' \t')
	got_sha=$($sha_cmd "$staging/payload" | awk '{print $1}')
	if [ "$got_bytes" != "$want_bytes" ]; then
		echo "FAIL $rel bytes-mismatch-got-$got_bytes"
		fails=$((fails + 1))
		continue
	fi
	if [ "$got_sha" != "$want_sha" ]; then
		echo "FAIL $rel sha-mismatch"
		fails=$((fails + 1))
		continue
	fi

	mkdir -p "$target/$(dirname "$rel")" || { echo "FAIL $rel mkdir-failed"; fails=$((fails + 1)); continue; }
	cat "$staging/payload" > "$target/$rel" || { echo "FAIL $rel write-failed"; fails=$((fails + 1)); continue; }
	echo "PASS $rel"
done < "$manifest"

[ "$fails" -eq 0 ] || exit 1
exit 0

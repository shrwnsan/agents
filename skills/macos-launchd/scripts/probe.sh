#!/bin/bash
#
# probe.sh — inspect (and optionally park-test) the launchd disabled-services
# store for the current user's gui domain.
#
# Usage:
#   probe.sh [label]        Read-only: print the resolved gui target, the
#                           exact store verdict for LABEL (disabled / enabled
#                           / absent / unknown), and whether the job is
#                           loaded. With no label, print the whole store.
#   probe.sh --park-test    Mutating but self-contained: bootstrap a throwaway
#                           /bin/true job, disable it, print the exact store
#                           line, then clean up through an EXIT trap. Verifies
#                           the store line format on this macOS version.
#
# No other flags. Never uses sudo. Read-only mode never mutates anything.

set -u

PROGNAME="probe.sh"

usage() {
    cat <<EOF
Usage:
  $PROGNAME [label]      read-only inspection of one label, or the whole
                         store if no label is given
  $PROGNAME --park-test  throwaway-label park test (verifies store format)

No other flags are accepted. This script never uses sudo.
EOF
}

die() {
    printf '%s: error: %s\n' "$PROGNAME" "$1" >&2
    exit "${2:-1}"
}

# --- environment guards ------------------------------------------------------

if [ "$(id -u)" -eq 0 ]; then
    die "running as root: gui/0 is not a valid user domain (the sudo trap). Run as the real user; resolve their UID with 'id -u <user>' if you must act on another account." 3
fi

uid="$(id -u)"
domain="gui/$uid"

# --- argument validation -----------------------------------------------------

MODE="store"   # store | label | park
LABEL=""

if [ $# -eq 0 ]; then
    MODE="store"
else
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --park-test)
            [ $# -eq 1 ] || die "--park-test takes no other arguments" 2
            MODE="park"
            ;;
        -*)
            usage >&2
            die "unknown flag: $1 (only [label] or --park-test are accepted)" 2
            ;;
        "")
            die "empty label is not a valid argument" 2
            ;;
        *)
            [ $# -eq 1 ] || die "expected exactly one label (got $# arguments)" 2
            case "$1" in
                *[!A-Za-z0-9._-]*)
                    die "invalid label '$1': allowed characters are A-Z a-z 0-9 . _ -" 2
                    ;;
            esac
            LABEL="$1"
            MODE="label"
            ;;
    esac
fi

# --- read-only helpers -------------------------------------------------------

STORE_OUT=""
STORE_RC=0

read_store() {
    STORE_OUT="$(launchctl print-disabled "$domain" 2>&1)"
    STORE_RC=$?
}

# store_verdict LABEL -> disabled | enabled | absent | unknown
# Exact whole-line match on whitespace-stripped lines. Presence-greps are
# wrong here: prefix collisions and persistent "=> enabled" lines both lie.
store_verdict() {
    _label="$1"
    if [ "$STORE_RC" -ne 0 ]; then
        printf 'unknown'
        return 0
    fi
    _stripped="$(printf '%s\n' "$STORE_OUT" | sed 's/^[[:space:]]*//')"
    if printf '%s\n' "$_stripped" | grep -Fxq -e "\"${_label}\" => disabled"; then
        printf 'disabled'
    elif printf '%s\n' "$_stripped" | grep -Fxq -e "\"${_label}\" => enabled"; then
        printf 'enabled'
    else
        printf 'absent'
    fi
}

# loaded_state LABEL -> loaded | not-loaded
loaded_state() {
    if launchctl print "$domain/$1" >/dev/null 2>&1; then
        printf 'loaded'
    else
        printf 'not-loaded'
    fi
}

# --- park test ---------------------------------------------------------------

PARK_LABEL=""
PARK_PLIST=""

park_cleanup() {
    # bootout of an unloaded job exits 0 harmlessly; enable flips the store
    # line back so only an inert "=> enabled" residue remains afterwards.
    launchctl bootout "$domain/$PARK_LABEL" >/dev/null 2>&1
    launchctl enable "$domain/$PARK_LABEL" >/dev/null 2>&1
    if [ -n "$PARK_PLIST" ]; then
        rm -f "$PARK_PLIST"
    fi
}

park_test() {
    PARK_LABEL="com.local.launchd-probe.$RANDOM$RANDOM"
    PARK_PLIST="$HOME/Library/LaunchAgents/$PARK_LABEL.plist"
    trap park_cleanup EXIT

    if [ ! -d "$HOME/Library/LaunchAgents" ]; then
        mkdir -p "$HOME/Library/LaunchAgents" || die "cannot create $HOME/Library/LaunchAgents" 4
    fi

    cat >"$PARK_PLIST" <<PLIST || die "cannot write $PARK_PLIST" 4
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>$PARK_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/true</string>
    </array>
    <key>RunAtLoad</key><true/>
</dict>
</plist>
PLIST

    err="$(launchctl bootstrap "$domain" "$PARK_PLIST" 2>&1)"
    rc=$?
    if [ "$rc" -ne 0 ]; then
        die "bootstrap rc=$rc: ${err:-<no stderr output>} (causes: label disabled, already bootstrapped, or bad plist path — see references/gotchas.md)" 5
    fi

    if ! launchctl disable "$domain/$PARK_LABEL" >/dev/null 2>&1; then
        die "disable failed unexpectedly for probe label $PARK_LABEL" 5
    fi

    read_store
    expected="\"$PARK_LABEL\" => disabled"
    observed="$(printf '%s\n' "$STORE_OUT" | sed 's/^[[:space:]]*//' | grep -Fx -e "$expected" || true)"

    echo "park-test label:     $PARK_LABEL"
    echo "expected store line: $expected"
    if [ -n "$observed" ]; then
        echo "observed store line: $observed"
        echo "VERDICT: format is '\"<label>\" => disabled'; exact-line matchers are safe on this macOS version."
    elif [ "$STORE_RC" -ne 0 ]; then
        die "print-disabled failed (rc=$STORE_RC): $STORE_OUT" 5
    else
        echo "VERDICT: expected line NOT found; this macOS version uses a different store format."
        echo "Observed print-disabled output:"
        printf '%s\n' "$STORE_OUT" | sed 's/^/    /'
        echo "Do NOT trust '=> disabled' matchers here; build them from the observed format."
    fi

    echo
    echo "Residue note: after cleanup the store keeps an inert \"$PARK_LABEL\" => enabled line."
    echo "Store entries are upsert-only and cannot be deleted; this residue is harmless."
}

# --- read-only reporting -----------------------------------------------------

username() {
    id -un 2>/dev/null || printf 'uid %s' "$uid"
}

report_store() {
    read_store
    echo "target: $domain (user $(username))"
    if [ "$STORE_RC" -ne 0 ]; then
        echo "store:  UNKNOWN (launchctl print-disabled failed, rc=$STORE_RC):" >&2
        printf '%s\n' "$STORE_OUT" | sed 's/^/    /' >&2
        echo "A failed read means the flag is unknown; never treat it as disabled." >&2
        exit 6
    fi
    if [ -z "$STORE_OUT" ]; then
        echo "store:  empty (no explicit entries; every label is enabled by default)"
    else
        printf '%s\n' "$STORE_OUT" | sed 's/^/    /'
    fi
}

report_label() {
    read_store
    verdict="$(store_verdict "$LABEL")"
    state="$(loaded_state "$LABEL")"
    echo "target: $domain/$LABEL (user $(username))"
    echo "store:  $verdict"
    echo "job:    $state"
    case "$verdict" in
        unknown)
            echo "warning: store unreadable; print-disabled said:" >&2
            printf '%s\n' "$STORE_OUT" | sed 's/^/    /' >&2
            echo "Flag is UNKNOWN, not disabled. Check that gui/$uid is the right domain." >&2
            exit 6
            ;;
        disabled)
            if [ "$state" = "loaded" ]; then
                echo "state:  RUNNING-DISABLED: running now, will NOT survive the next login."
                echo "        To park fully: 'launchctl bootout $domain/$LABEL' (disable already done)."
            else
                echo "state:  parked: not loaded, and RunAtLoad cannot resurrect it at login."
            fi
            ;;
        enabled)
            echo "state:  enabled (explicit '=> enabled' store line)"
            ;;
        absent)
            echo "state:  enabled (no store line; enabled is the default)"
            ;;
    esac
}

# --- dispatch ----------------------------------------------------------------

case "$MODE" in
    store) report_store ;;
    label) report_label ;;
    park)  park_test ;;
esac

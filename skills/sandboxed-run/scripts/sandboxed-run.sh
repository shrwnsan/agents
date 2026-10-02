#!/bin/sh
# sandboxed-run — one-command containment for running untrusted or vendored code.
#
# Puts a run behind three quarantines, then tears them down:
#   1. packages  — fresh throwaway venv (pip installs die with the run)
#   2. git/files — code runs in a throwaway clone or copy, never your working tree
#   3. creds     — env scrubbed to a small allowlist; HOME and TMPDIR live in the sandbox
#
# Honest scope: process hygiene, not a jail. The child can still read
# world-readable files and reach the network (the scrub drops proxy/CA vars,
# so credential-injecting proxied egress usually fails — the safe direction).
# Use a container when the code must not be trusted with the filesystem at all.

set -eu

prog=sandboxed-run

usage() {
  cat <<EOF
Usage: $prog [options] -- command [args...]

Runs a command against untrusted or vendored code with a fresh venv, a
throwaway clone or copy of the code under test, and a credential-free
environment. The sandbox is deleted on exit; the command's exit code is
preserved.

Options:
  -C DIR          Stage DIR as the code under test and use it as cwd.
                  Inside a git work tree: throwaway clone (committed state
                  only; uncommitted changes trigger a note). Otherwise:
                  byte copy with .git dropped.
  --copy          Force the byte copy (includes uncommitted changes).
  --no-venv       Skip the venv (non-python runs).
  --require-venv  Fail instead of continuing when no venv can be built.
  --env NAME      Pass the parent's NAME through the scrub.
  --env NAME=VAL  Set NAME to VAL inside the sandbox (applied last, so it can
                  re-point HOME/TMPDIR outside the sandbox when a run truly
                  needs that).
  --keep          Keep the sandbox for debugging; path printed to stderr.
  -h, --help      Show this help.
EOF
}

die() {
  printf '%s: %s\n' "$prog" "$*" >&2
  exit 2
}

TARGET=
FORCE_COPY=0
NO_VENV=0
REQUIRE_VENV=0
KEEP=0
ENV_ALLOW=

while [ $# -gt 0 ]; do
  case $1 in
    -C)
      [ $# -ge 2 ] || die 'option -C needs a directory argument'
      TARGET=$2
      shift 2
      ;;
    --copy) FORCE_COPY=1; shift ;;
    --no-venv) NO_VENV=1; shift ;;
    --require-venv) REQUIRE_VENV=1; shift ;;
    --env)
      [ $# -ge 2 ] || die 'option --env needs NAME or NAME=VALUE'
      env_name=${2%%=*}
      case $env_name in
        '' | *[!A-Za-z0-9_]*) die "not a valid environment name: \"$env_name\"" ;;
      esac
      ENV_ALLOW="$ENV_ALLOW$2
"
      shift 2
      ;;
    --keep) KEEP=1; shift ;;
    -h | --help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*) die "unknown option: $1 (see --help)" ;;
    *) die "commands must come after \"--\" (see --help)" ;;
  esac
done

[ $# -ge 1 ] || die 'no command given — put it after "--" (see --help)'

ORIG_PWD=$(pwd)
TMPBASE=${TMPDIR:-/tmp}
SANDBOX=$(mktemp -d "$TMPBASE/sandboxed-run.XXXXXX") || die 'mktemp failed'

cleanup() {
  status=$?
  cd "$ORIG_PWD" 2>/dev/null || cd /
  if [ "$KEEP" -eq 1 ]; then
    printf '%s: kept for inspection: %s\n' "$prog" "$SANDBOX" >&2
  else
    case $SANDBOX in
      "$TMPBASE"/sandboxed-run.*) rm -rf "$SANDBOX" ;;
      *) printf '%s: refusing to delete unexpected sandbox path: %s\n' "$prog" "$SANDBOX" >&2 ;;
    esac
  fi
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

# --- stage the code under test -----------------------------------------------
# clone: full isolation — the sandbox gets its own .git, so untrusted commits,
# hooks, and config writes land in the clone's object store, never the source.
# copy: for non-repo dirs, subdirs of a repo, or when dirty state is wanted.
MODE=scratch
RUN_DIR=$SANDBOX/run
mkdir "$RUN_DIR"

if [ -n "$TARGET" ]; then
  [ -d "$TARGET" ] || die "not a directory: $TARGET"
  TARGET=$(cd "$TARGET" && pwd) || die "cannot enter: $TARGET"
  if [ "$FORCE_COPY" -eq 0 ]; then
    if repo_top=$(git -C "$TARGET" rev-parse --show-toplevel 2>/dev/null); then
      if [ "$repo_top" = "$TARGET" ]; then
        MODE=clone
        git clone --no-hardlinks --quiet -- "$TARGET" "$RUN_DIR" ||
          die 'git clone failed'
        if [ -n "$(git -C "$TARGET" status --porcelain 2>/dev/null)" ]; then
          printf '%s: note: uncommitted changes exist; the sandbox runs committed state only (use --copy to include them)\n' "$prog" >&2
        fi
      fi
    fi
  fi
  if [ "$MODE" != clone ]; then
    MODE=copy
    (cd "$TARGET" && cp -R -p . "$RUN_DIR") || die 'copy failed'
    rm -rf "$RUN_DIR/.git"
  fi
fi
cd "$RUN_DIR"

# --- fresh venv --------------------------------------------------------------
# Quarantines pip installs. Soft-fails when no python exists (a non-python run
# should not die for this); --require-venv hardens it when a run needs pip.
VENV_NOTE=off
if [ "$NO_VENV" -eq 0 ]; then
  if sandbox_py=$(command -v python3 || command -v python); then
    if "$sandbox_py" -m venv "$SANDBOX/venv" >/dev/null 2>&1; then
      PATH="$SANDBOX/venv/bin:$PATH"
      export PATH
      VENV_NOTE="fresh ($("$SANDBOX/venv/bin/python" -V 2>&1))"
    else
      VENV_NOTE=skipped-creation-failed
      if [ "$REQUIRE_VENV" -eq 1 ]; then
        die '--require-venv set but venv creation failed'
      fi
    fi
  else
    VENV_NOTE=skipped-no-python
    if [ "$REQUIRE_VENV" -eq 1 ]; then
      die '--require-venv set but no python interpreter found'
    fi
  fi
fi
PYTHONNOUSERSITE=1
export PYTHONNOUSERSITE

# --- env scrub ----------------------------------------------------------------
# Default-deny: everything not allowlisted is unset — tokens, proxy/CA vars,
# GIT_DIR/GIT_WORK_TREE hijacks, SSH/GPG agents. Then HOME and TMPDIR are
# re-pointed into the sandbox, and explicit --env NAME=VALUE entries apply last.
set -f   # names, not globs — multi-line values can leave glob-y lines in the list
for var in $(env | sed 's/=.*//'); do
  case $var in
    PATH | SHELL | USER | LOGNAME | LANG | TERM | LC_* | PYTHONDONTWRITEBYTECODE) continue ;;
  esac
  if printf '%s' "$ENV_ALLOW" | grep -qxF -- "$var"; then continue; fi
  unset -v "$var" 2>/dev/null || :
done
set +f

mkdir -p "$SANDBOX/home" "$SANDBOX/tmp"
HOME=$SANDBOX/home
export HOME
TMPDIR=$SANDBOX/tmp
export TMPDIR

if [ -n "$ENV_ALLOW" ]; then
  while IFS= read -r env_entry; do
    [ -n "$env_entry" ] || continue
    case $env_entry in
      *=*) export "$env_entry" ;;
    esac
  done <<EOF
$ENV_ALLOW
EOF
fi

printf '%s: sandbox=%s mode=%s venv=%s home=sandbox env=allowlist\n' \
  "$prog" "$SANDBOX" "$MODE" "$VENV_NOTE" >&2

"$@"

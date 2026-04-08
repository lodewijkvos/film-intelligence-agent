#!/usr/bin/env bash
set -euo pipefail

film-intel initdb
film-intel run-weekly --dry-run

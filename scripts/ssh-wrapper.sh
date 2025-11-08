#!/bin/bash
# =============================================================================
# S.Y.N.A.P.S.E. ENGINE SSH Command Wrapper
# =============================================================================
# This script restricts SSH access to only execute start/stop commands.
#
# Security: When this key is used via SSH, only these two commands are allowed:
# - start-metal-servers
# - stop-metal-servers
#
# Any other command will be rejected.
# =============================================================================

case "$SSH_ORIGINAL_COMMAND" in
  "start-metal-servers")
    exec /opt/homebrew/bin/bash /Users/dperez/Documents/Programming/SYNAPSE_ENGINE/scripts/start-host-llama-servers.sh
    ;;
  "stop-metal-servers")
    exec /opt/homebrew/bin/bash /Users/dperez/Documents/Programming/SYNAPSE_ENGINE/scripts/stop-host-llama-servers.sh
    ;;
  *)
    echo "ERROR: Unauthorized command. Only 'start-metal-servers' and 'stop-metal-servers' are allowed." >&2
    exit 1
    ;;
esac

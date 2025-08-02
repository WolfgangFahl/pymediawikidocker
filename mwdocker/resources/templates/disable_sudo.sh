#!/bin/bash
# WF 2025-08-02
#
# disable sudo access
#

disable_sudo() {
  echo "🔒 Disabling sudo access..."
  if [ -f /etc/sudoers.d/www-data ]; then
    echo "🗑️  Removing /etc/sudoers.d/www-data"
    sudo rm -f /etc/sudoers.d/www-data
  fi
  if command -v sudo >/dev/null; then
    echo "🧼 Purging sudo package (relying on cached privileges)"
    sudo apt-get purge -y sudo
  else
    echo "✅ sudo already removed or not present"
  fi
}

disable_sudo

#!/bin/bash
# install the required extensions
# WF 2021-06-23

# git_get - clone if missing, else pull
# param $1 - the url
# param $2 - the directory to clone to
# param $3 - the options (optional)
git_get() {
  local url="$1"
  local dir="$2"
  local options="$3"

  if [ -d "$dir" ]; then
    if [ -d "$dir/.git" ]; then
      git -C "$dir" pull --ff-only
    else
      echo "warning: $dir exists but is not a git repo" >&2
    fi
  else
    git clone ${options} "$url" "$dir"
  fi
}

{% for extension in extensions %}
# {{ extension.name }}
# {{ extension.url }}
{{ extension.asScript(branch) | safe }}
{% endfor %}

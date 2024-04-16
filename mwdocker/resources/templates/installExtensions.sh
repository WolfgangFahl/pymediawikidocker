#!/bin/bash
# install the required extensions
# WF 2021-06-23
cd /var/www/html/extensions
{% for extension in extensions %}
# {{ extension.name }}
# {{ extension.url }}
{{ extension.asScript(branch) | safe }}
{% endfor %}
# install composer based extensions
cd /var/www/html
composer update --no-dev
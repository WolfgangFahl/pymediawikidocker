# general LocalSettings
{% if smwVersion %}
# enable Support for Semantic MediaWiki
# see https://www.semantic-mediawiki.org/wiki/Help:EnableSemantics
# Version of SemanticMediaWiki at install time: {{smwVersion}}
enableSemantics();     
{% endif %}
{% for extension in extensions %}
# {{ extension.name }}
# {{ extension.url }}
{{ extension.getLocalSettingsLine(mwShortVersion) }}{% endfor %}
# modified defaults
# https://www.mediawiki.org/wiki/Manual:$wgEnableUploads
$wgEnableUploads = true;
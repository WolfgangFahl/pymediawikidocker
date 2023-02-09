# general LocalSettings
{% if smwVersion %}
# enable Support for Semantic MediaWiki
# see https://www.semantic-mediawiki.org/wiki/Help:EnableSemantics
# Version of SemanticMediaWiki at install time: {{smwVersion}}
{% if smwVersion >= "4" %}
wfLoadExtension( 'SemanticMediaWiki' );
{% endif %}
enableSemantics();
# https://www.semantic-mediawiki.org/wiki/Help:$smwgQMaxInlineLimit
$smwgQMaxLimit=10000;
$smwgQMaxInlineLimit=2000;
{% endif %}
{% for extension in extensions %}
# {{ extension.name }}
# {{ extension.url }}
{{ extension.getLocalSettingsLine(mwShortVersion) }}{% endfor %}
# modified defaults
# https://www.mediawiki.org/wiki/Manual:$wgEnableUploads
$wgEnableUploads = true;
# https://github.com/WolfgangFahl/pymediawikidocker/issues/30:
$wgDeprecationReleaseLimit = "1.35.0";
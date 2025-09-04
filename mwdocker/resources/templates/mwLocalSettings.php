# general LocalSettings
$wgEnableAPI = true;
{% if smw_version %}
# enable Support for Semantic MediaWiki
# see https://www.semantic-mediawiki.org/wiki/Help:EnableSemantics
# Version of SemanticMediaWiki at install time: {{smw_version}}
{% if smw_version >= "4" %}
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
# settings for warnings
# https://github.com/WolfgangFahl/pymediawikidocker/issues/72
$wgDevelopmentWarnings = false;
# error_reporting( E_ALL & ~E_DEPRECATED & ~E_STRICT );
# no warnings
# ini_set( 'display_errors', 0 );
# -------------------------------------------------------------------
# Optional secret cookie security (enabled if MW_SECRET_COOKIE is set)
# -------------------------------------------------------------------

$secret_cookie     = getenv('MW_SECRET_COOKIE');       # secret value
$secret_cookie_ttl = getenv('MW_SECRET_COOKIE_TTL');   # optional lifetime in seconds

if ($secret_cookie) {
    # if TTL is set -> use it; otherwise 0 = session cookie (expires on browser close)
    $expiry = $secret_cookie_ttl ? time() + intval($secret_cookie_ttl) : 0;

    # on login: set cookie
    $wgHooks['UserLoginComplete'][] = function ( $user, &$inject_html, $direct = false ) use ( $secret_cookie, $expiry ) {
        setcookie('mw_secret', $secret_cookie, $expiry, '/', '', true, true);
        return true;
    };

    # on logout: delete cookie immediately
    $wgHooks['UserLogout'][] = function ( $user, &$inject_html = '', $oldName = null ) {
        setcookie('mw_secret', '', time() - 1, '/', '', true, true);
        return true;
    };
}



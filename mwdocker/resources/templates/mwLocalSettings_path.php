## The URL base path to the directory containing the wiki;
## defaults for all runtime URL paths are based off of this.
## For more information on customizing the URLs
## (like /w/index.php/Page_title to /wiki/Page_title) please see:
## https://www.mediawiki.org/wiki/Manual:Short_URL
$wgScriptPath = "";

{% if config.article_path %}
## Set wgArticlePath if config.article_path is provided
$wgArticlePath = "{{ config.article_path }}";

## The protocol and server name to use in fully-qualified URLs (without port)
$wgServer = "http://{{hostname}}";
{% else %}
## The protocol and server name to use in fully-qualified URLs (with port)
$wgServer = "http://{{hostname}}:{{port}}";
{% endif %}

## The URL path to static resources (images, scripts, etc.)
$wgResourceBasePath = $wgScriptPath;
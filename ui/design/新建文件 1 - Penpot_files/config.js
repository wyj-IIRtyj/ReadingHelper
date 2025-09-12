var penpotFlags = "enable-email-blacklist enable-audit-log enable-audit-log-archive enable-audit-log-gc enable-user-feedback enable-smtp disable-log-emails disable-backend-asserts disable-demo-users disable-telemetry enable-auto-file-snapshot enable-terms-and-privacy-checkbox enable-login-with-google enable-login-with-github enable-login-with-gitlab enable-newsletter-subscription enable-feature-plugins enable-quotes enable-soft-quotes enable-webhooks enable-urepl-server enable-prepl-server enable-access-tokens enable-rpc-climit enable-file-validation enable-soft-file-schema-validation enable-subscriptions disable-feature-text-editor-v2";

var penpotPluginsWhitelist = [
  "https://lorem-ipsum-penpot-plugin.pages.dev",  "https://contrast-penpot-plugin.pages.dev",  "https://icons-penpot-plugin.pages.dev",  "https://table-penpot-plugin.pages.dev",  "https://create-palette-penpot-plugin.pages.dev",  "https://rename-layers-penpot-plugin.pages.dev"  ];

var penpotPluginsListUri = "https://penpot.app/penpothub/plugins";


var penpotTermsOfServiceURI = "https://penpot.app/terms";
var penpotPrivacyPolicyURI = "https://penpot.app/privacy";

function getFeatureFlagFromLocalStorage(flag, value) {
  if (!localStorage.hasOwnProperty(flag)) {
    localStorage.setItem(flag, (Math.random() >= 0.5) ? value : "control");
  }
  return localStorage.getItem(flag);
}

var cachedFeatureFlags = {};
var forcedExternalFeatureKeys = [];
var forcedExternalFeatureFlags = forcedExternalFeatureKeys.reduce((o, key) => ({ ...o, [key]: getFeatureFlagFromLocalStorage(key, 'test')}), {});

function externalFeatureFlag(flag, value) {
  if (forcedExternalFeatureFlags[flag] !== undefined) {
    return forcedExternalFeatureFlags[flag] == value;
  } else if (window.posthog) {
    var flagValue = window.posthog.getFeatureFlag(flag);
    saveCachedFeatureFlag(flag, flagValue);
    return flagValue == value;
  }
}

function externalSessionId() {
  if (window.posthog && window.posthog.get_session_id) {
    return window.posthog.get_session_id();
  }
}

function initializeCachedFeatureFlags() {
  posthog.onFeatureFlags(function () {
    cachedFeatureFlags = { ...forcedExternalFeatureFlags }
    var flags = posthog.featureFlags.getFlags();

    flags.forEach(flag => {
      cachedFeatureFlags[flag] = window.posthog.getFeatureFlag(flag);
    });
  })
}

function saveCachedFeatureFlag(flag, value) {
  if (value === undefined) {
    delete cachedFeatureFlags[flag];
  } else {
    cachedFeatureFlags[flag] = value;
  }
}

function externalContextInfo() {
  return { featureFlags: cachedFeatureFlags };
}

window.onload = () => {
  initializeExternalConfigInfo();
}

function initializeExternalConfigInfo() {
  if (window.posthog) initializeCachedFeatureFlags();
}


var _paq = window._paq || [];
_paq.push(["setDoNotTrack", true]);
_paq.push(["disableCookies"]);
_paq.push(['trackPageView']);
(function() {
  var u="https://matomo.kaleidos.net/";
  _paq.push(['setTrackerUrl', u+'matomo.php']);
  _paq.push(['setSiteId', '6']);
  var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
  g.type='text/javascript'; g.async=true; g.defer=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
})();

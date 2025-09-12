(function(){"use strict";/*! js-cookie v3.0.5 | MIT */function u(n){for(var e=1;e<arguments.length;e++){var o=arguments[e];for(var i in o)n[i]=o[i]}return n}var S={read:function(n){return n[0]==='"'&&(n=n.slice(1,-1)),n.replace(/(%[\dA-F]{2})+/gi,decodeURIComponent)},write:function(n){return encodeURIComponent(n).replace(/%(2[346BF]|3[AC-F]|40|5[BDE]|60|7[BCD])/g,decodeURIComponent)}};function m(n,e){function o(t,s,a){if(!(typeof document>"u")){a=u({},e,a),typeof a.expires=="number"&&(a.expires=new Date(Date.now()+a.expires*864e5)),a.expires&&(a.expires=a.expires.toUTCString()),t=encodeURIComponent(t).replace(/%(2[346B]|5E|60|7C)/g,decodeURIComponent).replace(/[()]/g,escape);var c="";for(var r in a)a[r]&&(c+="; "+r,a[r]!==!0&&(c+="="+a[r].split(";")[0]));return document.cookie=t+"="+n.write(s,t)+c}}function i(t){if(!(typeof document>"u"||arguments.length&&!t)){for(var s=document.cookie?document.cookie.split("; "):[],a={},c=0;c<s.length;c++){var r=s[c].split("="),d=r.slice(1).join("=");try{var k=decodeURIComponent(r[0]);if(a[k]=n.read(d,k),t===k)break}catch{}}return t?a[t]:a}}return Object.create({set:o,get:i,remove:function(t,s){o(t,"",u({},s,{expires:-1}))},withAttributes:function(t){return m(this.converter,u({},this.attributes,t))},withConverter:function(t){return m(u({},this.converter,t),this.attributes)}},{attributes:{value:Object.freeze(e)},converter:{value:Object.freeze(n)}})}var p=m(S,{path:"/"});const l={cookie:{name:"cookie-consent-v2",policyUrl:"https://penpot.app/cookie",options:{expires:new Date(new Date().getFullYear()+1,0,1)}}},_=`@import url('https://fonts.googleapis.com/css2?family=Work+Sans&display=swap');

.CookieConsent_wrapper {
  --font-size-00: 0.5em;
  --font-size-0: 0.75em;
  --font-size-1: 1em;
  --font-size-2: 1.1em;
  --font-size-3: 1.25em;
  --font-size-4: 1.5em;
  --font-size-5: 2em;
  --font-size-6: 2.5em;
  --font-size-7: 3em;
  --font-size-8: 3.5em;
  --gray-60: #1f1f1f;
  --gray-canvas: #f6f6f6;
  --dark-gray: #1c2022;
  --primary: #31efb8;
  --size-000: -0.5em;
  --size-00: -0.25em;
  --size-1: 0.25em;
  --size-2: 0.5em;
  --size-3: 1em;
  --size-4: 1.25em;
  --size-5: 1.5em;
  --size-6: 1.75em;
  --size-7: 2em;
  --size-8: 3em;
  --size-9: 4em;
  --size-10: 5em;
  --size-11: 7.5em;
  --size-12: 10em;
  --size-13: 15em;
  --size-14: 20em;
  --size-15: 30em;
  all: initial;
  box-sizing: border-box;
  margin: 0;
  isolation: isolate;
  display: flex;
  font-size: 16px !important;
  justify-content: center;
  inline-size: 100%;
  position: fixed;
  inset-block-end: var(--size-6);
  z-index: 100;
}

.CookieConsent_panel {
  container-type: inline-size;
  background: var(--gray-60);
  color: var(--gray-canvas);
  padding: var(--size-5);
  line-height: 1.5;
  inline-size: 90%;
  max-inline-size: 1280px;
  box-shadow: 0 10px 30px 0 hsla(220, 3%, 40%, 0.25);
  border-radius: 8px;
  font-size: var(--font-size-1);
  font-family: Work Sans, sans-serif;
  border: 1px solid #a599c6;
}

.CookieConsent_msg {
  margin: 0;
  max-width: max-content;
  font-size: var(--font-size-1);
}

.CookieConsent_link {
  color: var(--gray-canvas);
  font-weight: 600;
}

.CookieConsent_link:hover {
  color: #e6e6e6;
  font-weight: 600;
  text-decoration: none;
}

.CookieConsent_button {
  border-radius: 8px;
  border: none;
  color: var(--dark-gray);
  padding: 12px 16px;
  font-family: Work Sans, sans-serif;
  font-size: var(--font-size-1);
}

.CookieConsent_button:hover {
  color: var(--primary);
  background-color: var(--dark-gray);
  cursor: pointer;
}

.CookieConsent_accept {
  background-color: var(--primary);
}

.CookieConsent_decline {
  background-color: #c6c9d7;
}

.CookieConsent_actions {
  display: flex;
  gap: var(--size-5);
  margin-block-start: var(--size-5);
  flex-shrink: 0;
}

.CookieConsent_inner {
  align-items: center;
}

@container (min-width: 768px) {
  .CookieConsent_inner {
    display: flex;
    gap: var(--size-5);
  }

  .CookieConsent_actions {
    margin-block-start: 0;
  }
}

.CookieSettings {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}

.CookieSettings.hidden {
  display: none;
}

.CookiesContainer {
  align-items: flex-start;
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 10px 0;
}

.CookieSettings_panel {
  background: var(--gray-60);
  color: var(--gray-canvas);
  font-family: Work Sans, sans-serif;
  padding: 20px;
  border-radius: 8px;
  max-width: 500px;
  margin-inline: 0.5rem;
  text-align: center;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
}

.CookieSettings_actions {
  margin-top: 10px;
}

.CookieItem {
  text-align: left;
}

.CookieSwitchLabel {
  color: #fff;
  flex: 1;
  flex-grow: 1;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--font-size-1);
  font-family: Work Sans, sans-serif;
  cursor: pointer;
  min-width: 200px;
  font-weight: bold;
}

.CookieSwitchLabel input {
  display: none;
}

.CookieSwitch {
  flex-shrink: 0;
  position: relative;
  width: 40px;
  height: 20px;
  background-color: #ccc;
  border-radius: 20px;
  transition: background-color 0.3s ease-in-out;
}

.CookieSwitch::before {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  background-color: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform 0.3s ease-in-out;
}

.CookieSwitchLabel input:checked + .CookieSwitch {
  background-color: #31efb8;
}

.CookieSwitchLabel input:checked + .CookieSwitch::before {
  transform: translateX(20px);
}

#cookie-technical + .CookieSwitch {
  background-color: #31efb8;
  cursor: not-allowed;
}

#cookie-technical + .CookieSwitch::before {
  transform: translateX(20px) !important;
}

.CookieDescription {
  font-size: 0.9em;
  color: #fff;
  padding: 0.5rem 0;
  max-width: 90%;
  line-height: 1.4;
  margin: 0;
}

.CookiesContainer .CookieItemPolicy {
  color: white;
  text-decoration: underline;
}

.CookiesContainer .CookieItemPolicy:hover {
  text-decoration: none;
  color: #e6e6e6;
}

.CookieSeparator {
  border-top: 1px solid #626369;
  border-color: #626369;
  border-bottom: 0;
  margin: 0.5rem 0;
}

.CookieTitle {
  font-size: 1.5rem;
  margin-top: 0;
  margin-bottom: 0.5rem;
}

.CookieSubtitle {
  font-size: 1rem;
  margin: 1rem 0;
}
`,L=`<div class="CookieConsent_wrapper">
  <div class="CookieConsent_panel">
    <div class="CookieConsent_inner">
      <div class="CookieConsent_msg">
        {{ message }}
        <a class="CookieConsent_link" target="_blank" data-link>{{ link }}</a>.
      </div>
      <div class="CookieConsent_actions">
        <button
          type="button"
          class="CookieConsent_button CookieConsent_accept"
          data-accept
        >
          {{ accept }}
        </button>
        <button
          type="button"
          class="CookieConsent_button CookieConsent_decline"
          data-decline
        >
          {{ decline }}
        </button>
        <button
          type="button"
          class="CookieConsent_button CookieConsent_customize"
          data-customize
        >
          {{ customize }}
        </button>
      </div>
    </div>
  </div>
  <div id="cookie-settings-modal" class="CookieSettings hidden">
    <div class="CookieSettings_panel">
      <h2 class="CookieTitle">{{ configure-cookies }}</h2>
      <p class="CookieSubtitle">{{ select-cookies }}</p>
      <hr class="CookieSeparator" />

      <div class="CookiesContainer">
        <!-- Technical Cookies (Static, always enabled) -->
        <div class="CookieItem">
          <label class="CookieSwitchLabel">
            <input type="checkbox" id="cookie-technical" checked disabled />
            <span class="CookieSwitch"></span>
            {{ cookie-technical }}
          </label>
          <p class="CookieDescription">{{ cookie-technical-description }}</p>
        </div>

        <!-- Analytics Cookies -->
        <div class="CookieItem">
          <label class="CookieSwitchLabel">
            <input type="checkbox" id="cookie-analytics" checked />
            <span class="CookieSwitch"></span>
            {{ cookie-analytics }}
          </label>
          <p class="CookieDescription">{{ cookie-analytics-description }}</p>
        </div>

        <!-- Marketing Cookies -->
        <div class="CookieItem">
          <label class="CookieSwitchLabel">
            <input type="checkbox" id="cookie-marketing" />
            <span class="CookieSwitch"></span>
            {{ cookie-marketing }}
          </label>
          <p class="CookieDescription">{{ cookie-marketing-description }}</p>
        </div>
        <div class="CookieItem">
          <a class="CookieItemPolicy" target="_blank" data-link-config>
            {{ check-cookie-policy }}</a
          >
        </div>
      </div>

      <div class="CookieSettings_actions">
        <button
          class="CookieConsent_button CookieConsent_accept"
          id="save-cookie-settings"
        >
          {{ save }}
        </button>
        <button
          class="CookieConsent_button CookieConsent_decline"
          id="close-cookie-settings"
        >
          {{ cancel }}
        </button>
      </div>
    </div>
  </div>
</div>
`,y={en:{message:"This website uses first-party and third-party cookies to enhance navigation, analyze traffic, and personalize content. You can accept all, reject them, or customize their use.",link:"Cookie Policy",accept:"Accept all",decline:"Reject all",customize:"Customize cookies","configure-cookies":"Configure cookies","select-cookies":"Select the cookies you want to allow","cookie-technical":"Technical Cookies (Necessary)","cookie-technical-description":"These cookies are essential for the website to function properly.","cookie-analytics":"Analytics Cookies","cookie-analytics-description":"These cookies collect anonymous data about how visitors interact with the website.","cookie-marketing":"Marketing Cookies","cookie-marketing-description":"These cookies are used to track users across websites.","check-cookie-policy":"Check our cookie policy",save:"Save",cancel:"Cancel"},es:{message:"Este sitio web utiliza cookies propias y de terceros para mejorar la navegación, analizar el tráfico y personalizar contenido. Puedes aceptar todas, rechazarlas o configurar su uso.",link:"Política de cookies",accept:"Aceptar todas",decline:"Rechazar todas",customize:"Configurar cookies","configure-cookies":"Configurar cookies","select-cookies":"Selecciona las cookies que deseas permitir","cookie-technical":"Cookies Técnicas (Necesarias)","cookie-technical-description":"Estas cookies son esenciales para el funcionamiento del sitio web.","cookie-analytics":"Cookies Analíticas","cookie-analytics-description":"Estas cookies recopilan datos anónimos sobre cómo los visitantes interactúan con el sitio web.","cookie-marketing":"Cookies de Marketing","cookie-marketing-description":"Estas cookies se utilizan para rastrear a los usuarios en diferentes sitios web.","check-cookie-policy":"Revisa nuestra politica de cookies",save:"Guardar",cancel:"Cancelar"}};function E(n,e="en"){if(navigator.language in n)return navigator.language;const o=navigator.language.split("-")[0];if(o in n)return o;for(const i of navigator.languages)if(i in n)return i;return e}function T(n,e,o){return n[e][o.trim()]}const v={getLanguage:E,getTranslation:T},f={TECHNICAL:"technical",ANALYTICS:"analytics",MARKETING:"marketing"};function A(n){if(!n.onAccept||!n.onDecline||typeof n.onAccept!="function"||typeof n.onDecline!="function")throw new TypeError("You must provide onAccept and onDecline functions");function e(z){return g=>{g.preventDefault(),z(g),document.body.removeChild(c)}}const o=v.getLanguage(y),i=document.createElement("style");i.textContent=_,document.head.appendChild(i);const t=new DOMParser,s=L.replace(/\{\{(.*?)\}\}/g,(z,g)=>v.getTranslation(y,o,g)),a=t.parseFromString(s,"text/html"),c=document.importNode(a.body.firstElementChild,!0),r=c.querySelector("[data-link]"),d=c.querySelector("[data-link-config]");r.href=n.policyUrl,d.href=n.policyUrl;const k=c.querySelector("[data-accept]"),x=["technical","analytics","marketing"];k.addEventListener("click",e(()=>n.onAccept(x)),{once:!0}),c.querySelector("[data-decline]").addEventListener("click",e(n.onDecline),{once:!0}),c.querySelector("[data-customize]").addEventListener("click",()=>b(n)),document.body.appendChild(c)}function b(n){const e=[f.ANALYTICS,f.MARKETING],o=document.getElementById("cookie-settings-modal");o.classList.remove("hidden"),e.forEach(i=>document.getElementById(`cookie-${i}`).checked=n.values.includes(i)),document.getElementById("close-cookie-settings").addEventListener("click",()=>o.classList.add("hidden")),document.getElementById("save-cookie-settings").addEventListener("click",()=>{const i=e.map(s=>document.getElementById(`cookie-${s}`).checked?s:!1).filter(s=>!!s);i.unshift(f.TECHNICAL),o.classList.add("hidden"),n.onAccept(i);const t=document.querySelector(".CookieConsent_wrapper");t&&t.remove()})}window.showCookieSettingsPanel=b;function I(n,e){window.dataLayer=window.dataLayer||[];function o(){window.dataLayer.push(arguments)}e&&typeof e=="object"&&o("consent","default",e),function(i,t,s,a,c){i[a]=i[a]||[],i[a].push({"gtm.start":new Date().getTime(),event:"gtm.js"});var r=t.getElementsByTagName(s)[0],d=t.createElement(s),k="";d.async=!0,d.src="https://www.googletagmanager.com/gtm.js?id="+c+k,r.parentNode.insertBefore(d,r)}(window,document,"script","dataLayer",n)}function D(){window.addEventListener("hashchange",function(e){"gtag"in window?gtag("event","page_view",{page_title:window.title,page_location:location.href}):console.warn("gtag not found")})}function h(n){let e;try{e=JSON.parse(p.get("cookie-consent-v2"))}catch{e={technical:!0,analytics:!1,marketing:!1}}const o={analytics_storage:e.analytics?"granted":"denied",ad_storage:e.marketing?"granted":"denied",ad_personalization:e.marketing?"granted":"denied",ad_user_data:e.marketing?"granted":"denied"};B(n,o)}function U(){switch(location.origin){case"https://help.penpot.app":break;case"https://community.penpot.dev":case"https://community.penpot.app":break;case"https://design.penpot.dev":case"https://design.penpot.app":D();break}}function B(n,e){I(n.get("gtm"),e),U()}function C(){if(document&&document.currentScript&&document.currentScript.src)return new URL(document.currentScript.src).searchParams;if(typeof window<"u"&&window.location&&window.location.href)return new URL(window.location.href).searchParams;try{const n=require("url").pathToFileURL(__filename).href;return new URL(n).searchParams}catch(n){return console.error("Could not determine the URL to get the parameters:",n),new URLSearchParams}}function R(){const n=location.hostname.match(/(\.?penpot\.(local|dev|app))/);if(n){const[,e]=n;return e.startsWith(".")?e:`.${e}`}}function w(){const n=R();return n?{...l.cookie.options,domain:n}:{...l.cookie.options}}function j(){const n=p.get(l.cookie.name);let e=[];if(n)try{e=JSON.parse(n)}catch{e=n.split(",")}A({policyUrl:l.cookie.policyUrl,values:e,onAccept:o=>{let i;Array.isArray(o)?i={technical:o.includes("technical"),analytics:o.includes("analytics"),marketing:o.includes("marketing")}:i=o,p.set(l.cookie.name,JSON.stringify(i),w()),h(C())},onDecline:()=>{const o={technical:!0,analytics:!1,marketing:!1};p.set(l.cookie.name,JSON.stringify(o),w()),h(C())}})}function P(){return!p.get(l.cookie.name)&&!location.pathname.startsWith("/plasmic-host")}P()?j():h(C())})();

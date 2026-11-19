/* Moj Elektro Plus panel. Source: frontend/src (MIT). Built with esbuild. */
var F="Europe/Ljubljana";function s(n){return String(n??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function Z(n,t=2){let a=new Intl.NumberFormat(n==="sl"?"sl-SI":"en-GB",{minimumFractionDigits:0,maximumFractionDigits:t});return e=>e==null||Number.isNaN(e)?"\u2014":a.format(e)}function L(n){return n==="sl"?"sl-SI":"en-GB"}function $(n,t){return t?new Intl.DateTimeFormat(L(n),{timeZone:F,year:"numeric",month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"}).format(new Date(t)):""}function P(n,t){return new Intl.DateTimeFormat(L(n),{timeZone:F,hour:"2-digit",minute:"2-digit"}).format(new Date(t))}function k(n,t,a={day:"numeric",month:"short"}){let[e,r,o]=t.split("-").map(Number);return new Intl.DateTimeFormat(L(n),{timeZone:"UTC",...a}).format(new Date(Date.UTC(e,r-1,o)))}function I(n,t){return k(n,t,{month:"short",year:"numeric"})}var h={top:12,right:8,bottom:26,left:48};function B(n){if(!(n>0))return 1;let t=10**Math.floor(Math.log10(n));for(let a of[1,2,2.5,5,10])if(a*t>=n)return a*t;return 10*t}function W(n){let{points:t,resolution:a,mode:e,width:r,height:o,active:i,label:c,fmt:u}=n,p=a==="interval"&&e==="power"?4:1,f=t.some(l=>l.export!==void 0&&l.export!==null),_=t.map(l=>l.import==null?null:l.import*p),x=t.map(l=>l.export==null?null:l.export*p),y=B(Math.max(0,..._.filter(l=>l!=null))),w=f?B(Math.max(0,...x.filter(l=>l!=null))):0,j=Math.max(10,r-h.left-h.right),E=Math.max(10,o-h.top-h.bottom),q=y+w||1,v=h.top+E*y/q,M=E/q,S=Math.max(t.length,1),b=j/S,R=Math.max(1,b*(S>200?1:.72)),m=[];for(let l of[0,.5,1]){let d=y*l,g=v-d*M;m.push(`<line x1="${h.left}" x2="${r-h.right}" y1="${g}" y2="${g}" class="grid"/>`,`<text x="${h.left-6}" y="${g+4}" class="axis" text-anchor="end">${s(u(d))}</text>`)}if(f){let l=v+w*M;m.push(`<line x1="${h.left}" x2="${r-h.right}" y1="${l}" y2="${l}" class="grid"/>`,`<text x="${h.left-6}" y="${l+4}" class="axis" text-anchor="end">\u2212${s(u(w))}</text>`)}t.forEach((l,d)=>{let g=h.left+d*b+(b-R)/2,D=[];d===i&&D.push("active");let ot=a==="interval"&&l.import_q&&l.import_q.length>0,nt=a!=="interval"&&l.present>0&&l.present<l.expected;if(_[d]==null)m.push(`<rect x="${g}" y="${v-3}" width="${R}" height="3" class="missing ${D.join(" ")}" data-i="${d}"/>`);else{let C=Math.max(_[d]*M,_[d]>0?1:0);m.push(`<rect x="${g}" y="${v-C}" width="${R}" height="${C}" class="bar import ${ot?"flagged":""} ${nt?"partial":""} ${D.join(" ")}" data-i="${d}"/>`)}if(f&&x[d]!=null){let C=Math.max(x[d]*M,x[d]>0?1:0);m.push(`<rect x="${g}" y="${v}" width="${R}" height="${C}" class="bar export ${D.join(" ")}" data-i="${d}"/>`)}m.push(`<rect x="${h.left+d*b}" y="${h.top}" width="${b}" height="${E}" class="hit" data-i="${d}"/>`)}),m.push(`<line x1="${h.left}" x2="${r-h.right}" y1="${v}" y2="${v}" class="zero"/>`);let rt=Math.max(1,Math.ceil(S/Math.max(2,Math.floor(j/70))));return t.forEach((l,d)=>{if(d%rt)return;let g=h.left+d*b+b/2;m.push(`<text x="${g}" y="${o-8}" class="axis" text-anchor="middle">${s(c(l))}</text>`)}),`<svg viewBox="0 0 ${r} ${o}" width="${r}" height="${o}" aria-hidden="true" focusable="false">${m.join("")}</svg>`}var K=n=>String(n).padStart(2,"0");function A(n){return`${n.getUTCFullYear()}-${K(n.getUTCMonth()+1)}-${K(n.getUTCDate())}`}function T(n){let[t,a,e]=n.split("-").map(Number);return new Date(Date.UTC(t,a-1,e))}function z(n,t){let a=T(n);return a.setUTCDate(a.getUTCDate()+t),A(a)}function N(n){return`${n.slice(0,7)}-01`}function V(n,t){let a=T(N(n));return a.setUTCMonth(a.getUTCMonth()+t),A(a)}function O(n){return/^\d{4}-\d{2}-\d{2}$/.test(n||"")?A(T(n))===n:!1}function Y(n=new Date){let t=new Intl.DateTimeFormat("en-CA",{timeZone:"Europe/Ljubljana",year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(n),a=e=>t.find(r=>r.type===e).value;return`${a("year")}-${a("month")}-${a("day")}`}var G=["latest","last7","last30","thisMonth","prevMonth","last12"];function Q(n,t,a){let e=t||z(a,-1);switch(n){case"latest":return{start:e,end:e};case"last7":return{start:z(e,-6),end:e};case"last30":return{start:z(e,-29),end:e};case"thisMonth":return{start:N(a),end:a};case"prevMonth":return{start:V(a,-1),end:z(N(a),-1)};case"last12":return{start:V(a,-11),end:a};default:throw new Error(`unknown preset ${n}`)}}function it(n,t){return Math.round((T(t)-T(n))/864e5)+1}var U={title:"Moj Elektro",meter:"Meter",range:"Period",from:"From",to:"To",apply:"Apply",presets:{latest:"Latest day",last7:"Last 7 days",last30:"Last 30 days",thisMonth:"This month",prevMonth:"Previous month",last12:"Last 12 months",custom:"Custom"},imported:"Imported",exported:"Exported",exportNotProvided:"Not provided for this meter",exportUnknown:"Not yet known",dailyAverage:"Daily average",dailyAverageHint:"Complete days only",peak:"Peak 15-min average demand",coverage:"Coverage",partial:"Partial period",complete:"Complete",flagged:"{n} flagged readings",noFlagged:"No quality flags",delayedTitle:"Delayed data",delayedText:"Moj Elektro publishes readings with a delay, usually the next day and sometimes later. 15-minute values are not live.",latestMeasurement:"Latest measurement",lastRefresh:"Last refresh",never:"never",refresh:"Refresh",refreshRange:"Re-download this period",exportCsv:"Export CSV",showTable:"Show table",hideTable:"Hide table",energy:"Energy (kWh)",power:"Average power (kW)",chartIntervals:"15-minute values",chartDays:"Daily totals",chartMonths:"Monthly totals",missing:"Missing",flaggedLegend:"Flagged quality",loading:"Loading\u2026",noMeters:"No meters are set up. Add the Moj Elektro Plus integration under Settings \u2192 Devices & services.",noData:"No readings are stored for this period.",noDataBackfill:"History is still downloading. Data appears as months complete.",errorTitle:"Could not load data",retry:"Retry",offline:"Home Assistant is offline. Showing the last loaded data.",backfill:"History download",backfillRunning:"Downloading month {done} of {total}",backfillComplete:"History complete",backfillError:"History download stopped: {error}",backfillRetry:"Resume download",rangeRunning:"Re-downloading: {done} of {total}",timezoneNote:"Days and months follow Europe/Ljubljana time.",costNote:"Costs are not shown: tariffs, network charges and taxes are not part of meter data.",time:"Time",date:"Date",month:"Month",value:"Value",quality:"Quality",adminOnly:"Only administrators can refresh data.",started:"Download started",menu:"Menu",kwh:"kWh",kw:"kW",at:"at"},lt={title:"Moj Elektro",meter:"Merilno mesto",range:"Obdobje",from:"Od",to:"Do",apply:"Uporabi",presets:{latest:"Zadnji dan",last7:"Zadnjih 7 dni",last30:"Zadnjih 30 dni",thisMonth:"Ta mesec",prevMonth:"Prej\u0161nji mesec",last12:"Zadnjih 12 mesecev",custom:"Po meri"},imported:"Prejeta energija",exported:"Oddana energija",exportNotProvided:"Za to merilno mesto ni na voljo",exportUnknown:"\u0160e ni znano",dailyAverage:"Dnevno povpre\u010Dje",dailyAverageHint:"Samo celotni dnevi",peak:"Najvi\u0161ja 15-min povpre\u010Dna mo\u010D",coverage:"Pokritost",partial:"Delno obdobje",complete:"Celotno",flagged:"{n} meritev z oznako kakovosti",noFlagged:"Brez oznak kakovosti",delayedTitle:"Podatki z zamikom",delayedText:"Moj Elektro objavlja meritve z zamikom, obi\u010Dajno naslednji dan, v\u010Dasih pozneje. 15-minutne vrednosti niso sprotne.",latestMeasurement:"Zadnja meritev",lastRefresh:"Zadnja osve\u017Eitev",never:"nikoli",refresh:"Osve\u017Ei",refreshRange:"Ponovno prenesi obdobje",exportCsv:"Izvozi CSV",showTable:"Prika\u017Ei tabelo",hideTable:"Skrij tabelo",energy:"Energija (kWh)",power:"Povpre\u010Dna mo\u010D (kW)",chartIntervals:"15-minutne vrednosti",chartDays:"Dnevne vsote",chartMonths:"Mese\u010Dne vsote",missing:"Manjka",flaggedLegend:"Oznaka kakovosti",loading:"Nalaganje\u2026",noMeters:"Ni nastavljenih merilnih mest. Dodajte integracijo Moj Elektro Plus pod Nastavitve \u2192 Naprave in storitve.",noData:"Za to obdobje ni shranjenih meritev.",noDataBackfill:"Zgodovina se \u0161e prena\u0161a. Podatki se prika\u017Eejo, ko so meseci preneseni.",errorTitle:"Podatkov ni bilo mogo\u010De nalo\u017Eiti",retry:"Poskusi znova",offline:"Home Assistant ni povezan. Prikazani so nazadnje nalo\u017Eeni podatki.",backfill:"Prenos zgodovine",backfillRunning:"Prena\u0161am mesec {done} od {total}",backfillComplete:"Zgodovina je prenesena",backfillError:"Prenos zgodovine se je ustavil: {error}",backfillRetry:"Nadaljuj prenos",rangeRunning:"Ponovni prenos: {done} od {total}",timezoneNote:"Dnevi in meseci so po \u010Dasu Europe/Ljubljana.",costNote:"Stro\u0161ki niso prikazani: tarife, omre\u017Enina in davki niso del merilnih podatkov.",time:"\u010Cas",date:"Datum",month:"Mesec",value:"Vrednost",quality:"Kakovost",adminOnly:"Podatke lahko osve\u017Eijo le skrbniki.",started:"Prenos se je za\u010Del",menu:"Meni",kwh:"kWh",kw:"kW",at:"ob"},dt={en:U,sl:lt};function X(n){return(n?.locale?.language||n?.language||"en").toLowerCase().startsWith("sl")?"sl":"en"}function J(n){let t=dt[n]||U;return(a,e={})=>{let r=a.split(".").reduce((o,i)=>o?.[i],t)??a.split(".").reduce((o,i)=>o?.[i],U)??a;return String(r).replace(/\{(\w+)\}/g,(o,i)=>String(e[i]??""))}}var tt=`
:host {
  display: block;
  min-height: 100vh;
  background: var(--primary-background-color, #fafafa);
  color: var(--primary-text-color, #212121);
  font-family: var(--paper-font-body1_-_font-family, var(--ha-font-family-body, Roboto, sans-serif));
  --me-import: var(--energy-grid-consumption-color, #488fc2);
  --me-export: var(--energy-grid-return-color, #8353d1);
  --me-flagged: var(--warning-color, #ffa600);
  --me-missing: var(--disabled-text-color, #bdbdbd);
  --me-radius: var(--ha-card-border-radius, 12px);
}
* { box-sizing: border-box; }
.toolbar {
  display: flex; align-items: center; gap: 8px;
  height: var(--header-height, 56px); padding: 0 16px;
  background: var(--app-header-background-color, var(--primary-color));
  color: var(--app-header-text-color, var(--text-primary-color, #fff));
  position: sticky; top: 0; z-index: 2;
  padding-top: env(safe-area-inset-top);
}
.toolbar h1 { font-size: 20px; font-weight: 400; margin: 0; }
.page { max-width: 1200px; margin: 0 auto; padding: 16px; display: grid; gap: 16px; }
.card {
  background: var(--card-background-color, #fff);
  border-radius: var(--me-radius);
  box-shadow: var(--ha-card-box-shadow, none);
  border: 1px solid var(--divider-color, rgba(0,0,0,.12));
  padding: 16px;
}
h2 { font-size: 16px; font-weight: 500; margin: 0; }
button {
  font: inherit; cursor: pointer; border-radius: 8px; padding: 8px 14px; min-height: 40px;
  border: 1px solid var(--primary-color); background: var(--primary-color);
  color: var(--text-primary-color, #fff);
}
button.secondary, button.chip {
  background: transparent; color: var(--primary-text-color);
  border-color: var(--divider-color, rgba(0,0,0,.2));
}
button.chip[aria-pressed="true"] {
  background: var(--primary-color); color: var(--text-primary-color, #fff); border-color: var(--primary-color);
}
button.icon { background: transparent; border: 0; color: inherit; font-size: 22px; min-width: 40px; }
button:disabled { opacity: .5; cursor: default; }
button:focus-visible, select:focus-visible, input:focus-visible, #chart:focus-visible {
  outline: 2px solid var(--primary-color); outline-offset: 2px;
}
.controls { display: grid; gap: 12px; }
.presets { display: flex; flex-wrap: wrap; gap: 8px; }
.custom { display: flex; flex-wrap: wrap; gap: 8px; align-items: end; }
.field { display: grid; gap: 4px; font-size: 12px; color: var(--secondary-text-color); }
select, input {
  font: inherit; font-size: 14px; color: var(--primary-text-color); min-height: 40px;
  background: var(--input-fill-color, var(--secondary-background-color, transparent));
  border: 1px solid var(--divider-color, rgba(0,0,0,.2)); border-radius: 8px; padding: 6px 10px;
}
.status { display: grid; gap: 12px; }
.delayed { padding: 10px 12px; border-radius: 8px; background: rgba(var(--rgb-info-color, 3,155,229), .12); }
dl { margin: 0; display: flex; flex-wrap: wrap; gap: 8px 32px; }
dt { font-size: 12px; color: var(--secondary-text-color); }
dd { margin: 0; font-weight: 500; }
.actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.progress { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.progress progress { flex: 1 1 160px; height: 8px; accent-color: var(--primary-color); }
.progress.ok { color: var(--success-color, #43a047); }
.progress.warn, .warn { color: var(--error-color, #db4437); }
.muted, .foot { color: var(--secondary-text-color); font-size: 13px; }
.banner { padding: 10px 14px; border-radius: 8px; background: var(--card-background-color); border: 1px solid currentColor; }
.banner.info { color: var(--info-color, #039be5); }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
.stat {
  background: var(--card-background-color, #fff); border-radius: var(--me-radius);
  border: 1px solid var(--divider-color, rgba(0,0,0,.12)); padding: 14px; display: grid; gap: 4px; align-content: start;
}
.stat .label { font-size: 13px; color: var(--secondary-text-color); }
.stat .value { font-size: 24px; font-weight: 500; }
.stat .value.small { font-size: 15px; font-weight: 400; }
.stat small { font-size: 13px; color: var(--secondary-text-color); }
.stat .sub { font-size: 12px; color: var(--secondary-text-color); display: block; }
.badge { display: inline-block; padding: 1px 8px; border-radius: 10px; background: var(--me-flagged); color: #000; }
.loading { opacity: .55; transition: opacity .2s; }
.chart-head { display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.chart-tools, .seg { display: flex; flex-wrap: wrap; gap: 6px; }
.chart-wrap { width: 100%; overflow: hidden; }
#chart { width: 100%; border-radius: 8px; }
svg { display: block; max-width: 100%; height: auto; }
svg .grid { stroke: var(--divider-color, rgba(0,0,0,.12)); stroke-width: 1; }
svg .zero { stroke: var(--secondary-text-color); stroke-width: 1; }
svg .axis { fill: var(--secondary-text-color); font-size: 11px; }
svg .bar.import { fill: var(--me-import); }
svg .bar.export { fill: var(--me-export); }
svg .bar.flagged { fill: var(--me-flagged); }
svg .bar.partial { opacity: .6; }
svg .missing { fill: var(--me-missing); }
svg .active { stroke: var(--primary-text-color); stroke-width: 1.5; }
svg .hit { fill: transparent; }
.tooltip { min-height: 22px; font-size: 13px; margin-top: 6px; }
.legend { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12px; color: var(--secondary-text-color); margin-top: 8px; }
.sw { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: middle; }
.sw.import { background: var(--me-import); } .sw.export { background: var(--me-export); }
.sw.flagged { background: var(--me-flagged); } .sw.missing { background: var(--me-missing); }
.state { padding: 32px 16px; text-align: center; color: var(--secondary-text-color); }
.error h2 { color: var(--error-color, #db4437); }
.table-wrap { max-height: 420px; overflow: auto; margin-top: 12px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.12)); }
thead th { position: sticky; top: 0; background: var(--card-background-color, #fff); }
@media (max-width: 600px) {
  .page { padding: 12px; gap: 12px; }
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .stat .value { font-size: 20px; }
  .custom .field { flex: 1 1 130px; }
}
@media (prefers-reduced-motion: reduce) { .loading { transition: none; } }
`;var et="mojelektro_plus",st="mojelektro_plus.selected_meter",at=3e3,ct=40,pt=new Set(["unknown_command","not_found"]);function ht(){try{return window.localStorage.getItem(st)}catch{return null}}function ut(n){try{window.localStorage.setItem(st,n)}catch{}}var H=class extends HTMLElement{constructor(){super(),this.attachShadow({mode:"open"}),this._state={status:"loading",meters:[],entryId:null,preset:"latest",start:null,end:null,data:null,dataLoading:!1,error:null,mode:"energy",showTable:!1,active:null,notice:null},this._seq=0,this._startRetries=0,this._width=640,this._onClick=this._onClick.bind(this),this._onChange=this._onChange.bind(this),this._onKey=this._onKey.bind(this),this._onPointer=this._onPointer.bind(this),this.shadowRoot.addEventListener("click",this._onClick),this.shadowRoot.addEventListener("change",this._onChange),this.shadowRoot.addEventListener("keydown",this._onKey),this.shadowRoot.addEventListener("pointermove",this._onPointer)}set hass(t){let a=!this._hass,e=this._hass?.connected!==!1,r=this._lang;if(this._hass=t,this._lang=X(t),this._t=J(this._lang),a){this._init();return}(r!==this._lang||e!==(t.connected!==!1))&&(this._render(),!e&&t.connected!==!1&&this._reload()),this._menu&&(this._menu.hass=t)}get hass(){return this._hass}set narrow(t){let a=this._narrow!==t;this._narrow=t,a&&this._hass&&this._render()}set panel(t){this._panel=t}set route(t){this._route=t}connectedCallback(){!this._resize&&typeof ResizeObserver<"u"&&(this._resize=new ResizeObserver(t=>{let a=Math.floor(t[0].contentRect.width);a&&Math.abs(a-this._width)>4&&(this._width=a,this._renderChartOnly())})),this._hass&&!this._unsub&&this._initialised&&this._subscribe()}disconnectedCallback(){this._resize?.disconnect(),this._unsubscribe(),clearTimeout(this._debounce),clearTimeout(this._subRetry),clearTimeout(this._loadRetry)}_ws(t,a={}){return this._hass.callWS({type:`${et}/${t}`,...a})}async _init(){this._initialised=!0,this._render(),this._subscribe(),await this._loadMeters(!0)}async _subscribe(){if(!(this._unsub||!this._hass?.connection))try{this._unsub=await this._hass.connection.subscribeMessage(t=>this._onServerUpdate(t),{type:`${et}/subscribe`})}catch{this._unsub=null,clearTimeout(this._subRetry),this.isConnected&&(this._subRetry=setTimeout(()=>this._subscribe(),at))}}_unsubscribe(){if(this._unsub){let t=this._unsub;this._unsub=null,Promise.resolve(t()).catch(()=>{})}}_onServerUpdate(t){if(!t||t.entry_id!==this._state.entryId){this._loadMeters(!1);return}clearTimeout(this._debounce),this._debounce=setTimeout(()=>this._reload(),800)}async _reload(){await this._loadMeters(!1),this._state.start&&await this._loadData()}async _loadMeters(t){try{let a=await this._ws("meters");this._startRetries=0;let e=a.meters||[],r=this._state;if(r.meters=e,!e.length){r.status="empty",this._render();return}if(!e.some(o=>o.entry_id===r.entryId)){let o=ht();r.entryId=e.some(i=>i.entry_id===o)?o:e[0].entry_id}if(r.status="ready",t){this._applyPreset("latest");return}this._render()}catch(a){if(pt.has(a?.code)&&this._startRetries<ct){this._startRetries+=1,clearTimeout(this._loadRetry),this._loadRetry=setTimeout(()=>this._loadMeters(t),at);return}this._state.status="error",this._state.error=a?.message||String(a),this._render()}}get _meter(){return this._state.meters.find(t=>t.entry_id===this._state.entryId)||null}_applyPreset(t){let a=this._state,e=Q(t,this._meter?.latest_day,Y());a.preset=t,a.start=e.start,a.end=e.end,a.active=null,this._loadData()}async _loadData(){let t=this._state;if(!t.entryId||!t.start)return;let a=++this._seq;t.dataLoading=!0,t.error=null,this._render();try{let e=await this._ws("data",{entry_id:t.entryId,start:t.start,end:t.end,resolution:"auto"});if(a!==this._seq)return;t.data=e,t.dataLoading=!1,t.active!=null&&t.active>=e.points.length&&(t.active=null)}catch(e){if(a!==this._seq)return;t.dataLoading=!1,t.error=e?.message||String(e)}this._render()}_onClick(t){let a=t.target.closest("[data-action]");if(!a){let o=t.target.closest("[data-i]");o&&(this._state.active=Number(o.dataset.i),this._renderChartOnly());return}let e=a.dataset.action,r=this._state;e==="preset"?this._applyPreset(a.dataset.preset):e==="apply-range"?this._applyCustom():e==="retry"?r.status==="error"?this._init():this._loadData():e==="refresh"?this._refresh(!1):e==="refresh-range"?this._refresh(!0):e==="backfill"?this._backfill():e==="csv"?this._csv():e==="mode"?(r.mode=a.dataset.mode,this._render()):e==="table"?(r.showTable=!r.showTable,this._render()):e==="menu"&&this.dispatchEvent(new Event("hass-toggle-menu",{bubbles:!0,composed:!0}))}_onChange(t){t.target.id==="meter"&&(this._state.entryId=t.target.value,ut(t.target.value),this._state.data=null,this._applyPreset(this._state.preset==="custom"?"latest":this._state.preset))}_onKey(t){if(t.target.id==="chart"){let a=this._state,e=a.data?.points?.length||0;if(!e)return;let r=a.active??-1;if(t.key==="ArrowRight")r=Math.min(e-1,r+1);else if(t.key==="ArrowLeft")r=Math.max(0,r<0?e-1:r-1);else if(t.key==="Home")r=0;else if(t.key==="End")r=e-1;else return;t.preventDefault(),a.active=r,this._renderChartOnly()}else(t.target.id==="start"||t.target.id==="end")&&t.key==="Enter"&&this._applyCustom()}_onPointer(t){let a=t.target.closest?.("rect.hit");if(!a)return;let e=Number(a.dataset.i);e!==this._state.active&&(this._state.active=e,this._renderChartOnly())}_applyCustom(){let t=this.shadowRoot,a=t.getElementById("start")?.value,e=t.getElementById("end")?.value,r=this._state;if(!O(a)||!O(e)||e<a){r.notice={kind:"error",text:this._t("errorTitle")},this._render();return}r.preset="custom",r.start=a,r.end=e,r.notice=null,r.active=null,this._loadData()}async _refresh(t){let a=this._state;try{let e={entry_id:a.entryId};t&&Object.assign(e,{start:a.start,end:a.end}),await this._ws("refresh",e),a.notice={kind:"info",text:this._t("started")}}catch(e){a.notice={kind:"error",text:e?.message||String(e)}}this._render(),this._reload()}async _backfill(){try{await this._ws("backfill",{entry_id:this._state.entryId})}catch(t){this._state.notice={kind:"error",text:t?.message||String(t)}}this._reload()}async _csv(){let t=this._state;try{let a=t.data?.resolution||"auto",e=await this._ws("csv",{entry_id:t.entryId,start:t.start,end:t.end,resolution:a}),r=new Blob([e.csv],{type:"text/csv;charset=utf-8"}),o=URL.createObjectURL(r),i=document.createElement("a");i.href=o,i.download=e.filename,this.shadowRoot.appendChild(i),i.click(),i.remove(),setTimeout(()=>URL.revokeObjectURL(o),1e3)}catch(a){t.notice={kind:"error",text:a?.message||String(a)},this._render()}}_fmt(t=2){return Z(this._lang,t)}_pointLabel(t,a=!0){let e=this._state.data?.resolution;return e==="interval"?P(this._lang,t.end):e==="month"?I(this._lang,t.start):a?k(this._lang,t.start):k(this._lang,t.start,{dateStyle:"medium"})}_render(){let t=this._t,a=this._state,e=this._hass?.connected===!1,r=a.status==="loading"?`<div class="state" role="status">${s(t("loading"))}</div>`:a.status==="empty"?`<div class="state">${s(t("noMeters"))}</div>`:a.status==="error"?`<div class="card error" role="alert"><h2>${s(t("errorTitle"))}</h2><p>${s(a.error)}</p><button data-action="retry">${s(t("retry"))}</button></div>`:this._content();this.shadowRoot.innerHTML=`
      <style>${tt}</style>
      <div class="toolbar">
        ${this._narrow?'<span id="menu-slot"></span>':""}
        <h1>${s(t("title"))}</h1>
      </div>
      <main class="page" aria-busy="${a.dataLoading||a.status==="loading"}">
        ${e?`<div class="banner warn" role="status">${s(t("offline"))}</div>`:""}
        ${r}
      </main>`,this._mountMenu();let o=this.shadowRoot.getElementById("chart-wrap");o&&this._resize&&(this._resize.disconnect(),this._resize.observe(o))}_mountMenu(){let t=this.shadowRoot.getElementById("menu-slot");if(t)if(customElements.get("ha-menu-button")){let a=document.createElement("ha-menu-button");a.hass=this._hass,a.narrow=this._narrow,t.appendChild(a),this._menu=a}else t.innerHTML=`<button class="icon" data-action="menu" aria-label="${s(this._t("menu"))}">\u2630</button>`}_content(){let t=this._t,a=this._state,e=this._meter,r=!!this._hass?.user?.is_admin;return`
      <section class="controls card" aria-label="${s(t("range"))}">
        <label class="field">${s(t("meter"))}
          <select id="meter">${a.meters.map(o=>`<option value="${s(o.entry_id)}" ${o.entry_id===a.entryId?"selected":""}>${s(o.title)}</option>`).join("")}</select>
        </label>
        <div class="presets" role="group" aria-label="${s(t("range"))}">
          ${G.map(o=>`<button class="chip" data-action="preset" data-preset="${o}" aria-pressed="${a.preset===o}">${s(t(`presets.${o}`))}</button>`).join("")}
        </div>
        <div class="custom">
          <label class="field">${s(t("from"))}<input id="start" type="date" value="${s(a.start)}" min="${s(e?.earliest_allowed||"")}"></label>
          <label class="field">${s(t("to"))}<input id="end" type="date" value="${s(a.end)}"></label>
          <button data-action="apply-range">${s(t("apply"))}</button>
        </div>
      </section>
      ${this._statusCard(e,r)}
      ${a.notice?`<div class="banner ${a.notice.kind==="error"?"warn":"info"}" role="status">${s(a.notice.text)}</div>`:""}
      ${this._dataSection(e,r)}
      <p class="foot">${s(t("timezoneNote"))} ${s(t("costNote"))}</p>`}_statusCard(t,a){let e=this._t;if(!t)return"";let r=t.backfill||{},o=t.job,i="";if(o){let c=o.kind==="range"?"rangeRunning":"backfillRunning";i=`<div class="progress"><span>${s(e(c,{done:o.done+1>o.total?o.total:o.done+1,total:o.total}))}</span>
        <progress max="${o.total}" value="${o.done}" aria-label="${s(e("backfill"))}"></progress></div>`}else r.state==="error"?i=`<div class="progress warn">${s(e("backfillError",{error:r.error||""}))}
        ${a?`<button data-action="backfill">${s(e("backfillRetry"))}</button>`:""}</div>`:r.state==="complete"&&(i=`<div class="progress ok">${s(e("backfillComplete"))}</div>`);return`
      <section class="card status" aria-label="${s(e("delayedTitle"))}">
        <div class="delayed"><strong>${s(e("delayedTitle"))}</strong> \u2014 ${s(e("delayedText"))}</div>
        <dl>
          <div><dt>${s(e("latestMeasurement"))}</dt><dd>${t.latest_reading?s($(this._lang,t.latest_reading)):"\u2014"}</dd></div>
          <div><dt>${s(e("lastRefresh"))}</dt><dd>${t.last_success?s($(this._lang,t.last_success)):s(e("never"))}</dd></div>
        </dl>
        ${i}
        <div class="actions">
          ${a?`<button data-action="refresh">${s(e("refresh"))}</button>
                 <button data-action="refresh-range" class="secondary">${s(e("refreshRange"))}</button>`:`<span class="muted">${s(e("adminOnly"))}</span>`}
          <button data-action="csv" class="secondary" ${this._state.data?"":"disabled"}>${s(e("exportCsv"))}</button>
        </div>
      </section>`}_dataSection(t,a){let e=this._t,r=this._state;if(r.error&&!r.data)return`<div class="card error" role="alert"><h2>${s(e("errorTitle"))}</h2><p>${s(r.error)}</p><button data-action="retry">${s(e("retry"))}</button></div>`;if(!r.data)return`<div class="state" role="status">${s(e("loading"))}</div>`;let o=r.data,i=o.summary,c=o.points.some(j=>j.import!=null),u=this._fmt(2),p=i.import,f=o.export_status!=="available"?`<div class="stat"><span class="label">${s(e("exported"))}</span><span class="value small">${s(e(o.export_status==="not_provided"?"exportNotProvided":"exportUnknown"))}</span></div>`:`<div class="stat"><span class="label">${s(e("exported"))}</span><span class="value">${u(i.export?.total)} <small>${e("kwh")}</small></span></div>`,_=i.peak?`${this._fmt(3)(i.peak.power_kw)} <small>${e("kw")}</small><span class="sub">${s($(this._lang,i.peak.interval_end))}</span>`:"\u2014",x=r.error?`<div class="banner warn" role="alert">${s(r.error)} <button data-action="retry">${s(e("retry"))}</button></div>`:"",y=e(o.resolution==="interval"?"chartIntervals":o.resolution==="day"?"chartDays":"chartMonths"),w=c?"":`<div class="state">${s(t?.backfill?.state==="running"||t?.job?e("noDataBackfill"):e("noData"))}</div>`;return`
      ${x}
      <section class="stats ${r.dataLoading?"loading":""}" aria-live="polite">
        <div class="stat"><span class="label">${s(e("imported"))}</span><span class="value">${u(p.total)} <small>${e("kwh")}</small></span>
          <span class="sub">${p.complete?s(e("complete")):`<span class="badge">${s(e("partial"))}</span>`}</span></div>
        ${f}
        <div class="stat"><span class="label">${s(e("dailyAverage"))}</span><span class="value">${u(i.daily_average)} <small>${e("kwh")}</small></span><span class="sub">${s(e("dailyAverageHint"))}</span></div>
        <div class="stat"><span class="label">${s(e("peak"))}</span><span class="value">${_}</span></div>
        <div class="stat"><span class="label">${s(e("coverage"))}</span><span class="value">${this._fmt(1)(p.coverage)} <small>%</small></span>
          <span class="sub">${p.flagged?s(e("flagged",{n:p.flagged})):s(e("noFlagged"))}</span></div>
      </section>
      <section class="card chart-card ${r.dataLoading?"loading":""}">
        <div class="chart-head">
          <h2>${s(y)}</h2>
          <div class="chart-tools">
            ${o.resolution==="interval"?`<div role="group" class="seg">
                    <button class="chip" data-action="mode" data-mode="energy" aria-pressed="${r.mode==="energy"}">${s(e("energy"))}</button>
                    <button class="chip" data-action="mode" data-mode="power" aria-pressed="${r.mode==="power"}">${s(e("power"))}</button>
                  </div>`:""}
            <button class="chip" data-action="table" aria-expanded="${r.showTable}">${s(r.showTable?e("hideTable"):e("showTable"))}</button>
          </div>
        </div>
        ${w}
        <div id="chart-wrap" class="chart-wrap">
          <div id="chart" tabindex="0" role="group" aria-roledescription="chart" aria-label="${s(y)}">${c?this._chartSvg():""}</div>
          <div id="tooltip" class="tooltip" aria-live="polite">${c?this._tooltip():""}</div>
        </div>
        <div class="legend">
          <span><i class="sw import"></i>${s(e("imported"))}</span>
          ${o.export_status==="available"?`<span><i class="sw export"></i>${s(e("exported"))}</span>`:""}
          <span><i class="sw flagged"></i>${s(e("flaggedLegend"))}</span>
          <span><i class="sw missing"></i>${s(e("missing"))}</span>
        </div>
        ${r.showTable?this._table():""}
      </section>`}_chartSvg(){let t=this._state.data,a=Math.max(260,this._width),e=this._narrow?200:260,r=t.resolution==="interval"?2:0;return W({points:t.points,resolution:t.resolution,mode:this._state.mode,width:a,height:e,active:this._state.active,label:o=>this._pointLabel(o),fmt:this._fmt(r)})}_tooltip(){let t=this._t,a=this._state,e=a.data?.points?.[a.active];if(!e)return"";let r=this._fmt(3),o=a.data.resolution==="interval"&&a.mode==="power",i=p=>p==null?s(t("missing")):`${r(o?p*4:p)} ${t(o?"kw":"kwh")}`,c=a.data.resolution==="interval"?`${$(this._lang,e.start)} \u2013 ${P(this._lang,e.end)}`:a.data.resolution==="month"?I(this._lang,e.start):k(this._lang,e.start,{dateStyle:"full"}),u=a.data.resolution==="interval"?(e.import_q||[]).map(p=>a.meters.find(f=>f.entry_id===a.entryId)?.qualities?.[p]||p).join(", "):e.expected?`${this._fmt(1)(e.coverage)} % ${t("coverage").toLowerCase()}${e.flagged?`, ${t("flagged",{n:e.flagged})}`:""}`:"";return`<strong>${s(c)}</strong> \xB7 ${s(t("imported"))}: ${i(e.import)}${e.export!==void 0?` \xB7 ${s(t("exported"))}: ${i(e.export)}`:""}${u?` \xB7 ${s(u)}`:""}`}_table(){let t=this._t,a=this._state.data,e=this._fmt(3),r=a.resolution==="interval"?t("time"):a.resolution==="day"?t("date"):t("month"),o=a.export_status==="available",i=a.points.map(c=>{let u=a.resolution==="interval"?$(this._lang,c.end):this._pointLabel(c,!1),p=a.resolution==="interval"?(c.import_q||[]).join(" "):`${this._fmt(1)(c.coverage)} %`;return`<tr><th scope="row">${s(u)}</th><td>${c.import==null?s(t("missing")):e(c.import)}</td>${o?`<td>${c.export==null?s(t("missing")):e(c.export)}</td>`:""}<td>${s(p)}</td></tr>`}).join("");return`<div class="table-wrap"><table><thead><tr><th scope="col">${s(r)}</th><th scope="col">${s(t("imported"))} (${t("kwh")})</th>${o?`<th scope="col">${s(t("exported"))} (${t("kwh")})</th>`:""}<th scope="col">${s(a.resolution==="interval"?t("quality"):t("coverage"))}</th></tr></thead><tbody>${i}</tbody></table></div>`}_renderChartOnly(){let t=this.shadowRoot.getElementById("chart"),a=this.shadowRoot.getElementById("tooltip");!t||!this._state.data||this._state.data.points.some(e=>e.import!=null)&&(t.innerHTML=this._chartSvg(),a&&(a.innerHTML=this._tooltip()))}};customElements.get("mojelektro-plus-panel")||customElements.define("mojelektro-plus-panel",H);export{H as MojElektroPanel,it as spanDays};

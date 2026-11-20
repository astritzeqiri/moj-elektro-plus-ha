/* Moj Elektro Plus panel. Source: frontend/src (MIT). Built with esbuild. */
var G="Europe/Ljubljana";function s(n){return String(n??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}function K(n,t=2,e=0){let a=new Intl.NumberFormat(n==="sl"?"sl-SI":"en-GB",{minimumFractionDigits:e,maximumFractionDigits:t});return r=>r==null||Number.isNaN(r)?"\u2014":a.format(r)}function I(n){return n==="sl"?"sl-SI":"en-GB"}function w(n,t){return t?new Intl.DateTimeFormat(I(n),{timeZone:G,year:"numeric",month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"}).format(new Date(t)):""}function H(n,t){return new Intl.DateTimeFormat(I(n),{timeZone:G,hour:"2-digit",minute:"2-digit"}).format(new Date(t))}function $(n,t,e={day:"numeric",month:"short"}){let[a,r,o]=t.split("-").map(Number);return new Intl.DateTimeFormat(I(n),{timeZone:"UTC",...e}).format(new Date(Date.UTC(a,r-1,o)))}function U(n,t){return $(n,t,{month:"short",year:"numeric"})}function Y(n,t,e){let a=o=>{let[i,l,u]=o.split("-").map(Number);return new Date(Date.UTC(i,l-1,u))},r=new Intl.DateTimeFormat(I(n),{timeZone:"UTC",day:"numeric",month:"short",year:"numeric"});return typeof r.formatRange=="function"?r.formatRange(a(t),a(e)):`${r.format(a(t))} \u2013 ${r.format(a(e))}`}var h={top:12,right:8,bottom:26,left:48};function Q(n){if(!(n>0))return 1;let t=10**Math.floor(Math.log10(n));for(let e of[1,2,2.5,5,10])if(e*t>=n)return e*t;return 10*t}function X(n){let{points:t,resolution:e,mode:a,width:r,height:o,active:i,label:l,fmt:u}=n,c=e==="interval"&&a==="power"?4:1,_=t.some(d=>d.export>0),M=t.map(d=>d.import==null?null:d.import*c),T=t.map(d=>d.export==null?null:d.export*c),L=Q(Math.max(0,...M.filter(d=>d!=null))),R=_?Q(Math.max(0,...T.filter(d=>d!=null))):0,j=Math.max(10,r-h.left-h.right),D=Math.max(10,o-h.top-h.bottom),z=L+R||1,g=h.top+D*L/z,S=D/z,O=Math.max(t.length,1),y=j/O,E=Math.max(1,y*(O>200?1:.72)),f=[];for(let d of[0,.5,1]){let p=L*d,b=g-p*S;f.push(`<line x1="${h.left}" x2="${r-h.right}" y1="${b}" y2="${b}" class="grid"/>`,`<text x="${h.left-6}" y="${b+4}" class="axis" text-anchor="end">${s(u(p))}</text>`)}if(_){let d=g+R*S;f.push(`<line x1="${h.left}" x2="${r-h.right}" y1="${d}" y2="${d}" class="grid"/>`,`<text x="${h.left-6}" y="${d+4}" class="axis" text-anchor="end">\u2212${s(u(R))}</text>`)}t.forEach((d,p)=>{let b=h.left+p*y+(y-E)/2,P=[];p===i&&P.push("active");let pt=e==="interval"&&d.import_q&&d.import_q.length>0,ht=e!=="interval"&&d.present>0&&d.present<d.expected;if(M[p]==null)f.push(`<rect x="${b}" y="${g-3}" width="${E}" height="3" class="missing ${P.join(" ")}" data-i="${p}"/>`);else{let A=Math.max(M[p]*S,M[p]>0?1:0);f.push(`<rect x="${b}" y="${g-A}" width="${E}" height="${A}" class="bar import ${pt?"flagged":""} ${ht?"partial":""} ${P.join(" ")}" data-i="${p}"/>`)}if(_&&T[p]!=null){let A=Math.max(T[p]*S,T[p]>0?1:0);f.push(`<rect x="${b}" y="${g}" width="${E}" height="${A}" class="bar export ${P.join(" ")}" data-i="${p}"/>`)}f.push(`<rect x="${h.left+p*y}" y="${h.top}" width="${y}" height="${D}" class="hit" data-i="${p}"/>`)}),f.push(`<line x1="${h.left}" x2="${r-h.right}" y1="${g}" y2="${g}" class="zero"/>`);let ct=Math.max(1,Math.ceil(O/Math.max(2,Math.floor(j/70))));return t.forEach((d,p)=>{if(p%ct)return;let b=h.left+p*y+y/2;f.push(`<text x="${b}" y="${o-8}" class="axis" text-anchor="middle">${s(l(d))}</text>`)}),`<svg viewBox="0 0 ${r} ${o}" width="${r}" height="${o}" aria-hidden="true" focusable="false">${f.join("")}</svg>`}var J=n=>String(n).padStart(2,"0");function Z(n){return`${n.getUTCFullYear()}-${J(n.getUTCMonth()+1)}-${J(n.getUTCDate())}`}function C(n){let[t,e,a]=n.split("-").map(Number);return new Date(Date.UTC(t,e-1,a))}function m(n,t){let e=C(n);return e.setUTCDate(e.getUTCDate()+t),Z(e)}function N(n){return`${n.slice(0,7)}-01`}function k(n,t){let e=C(N(n));return e.setUTCMonth(e.getUTCMonth()+t),Z(e)}function V(n){return/^\d{4}-\d{2}-\d{2}$/.test(n||"")?Z(C(n))===n:!1}function B(n=new Date){let t=new Intl.DateTimeFormat("en-CA",{timeZone:"Europe/Ljubljana",year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(n),e=a=>t.find(r=>r.type===a).value;return`${e("year")}-${e("month")}-${e("day")}`}var et=["latest","last7","last30","thisMonth","prevMonth","last12"];function at(n,t,e){let a=t||m(e,-1);switch(n){case"latest":return{start:a,end:a};case"last7":return{start:m(a,-6),end:a};case"last30":return{start:m(a,-29),end:a};case"thisMonth":return{start:N(e),end:e};case"prevMonth":return{start:k(e,-1),end:m(N(e),-1)};case"last12":return{start:k(e,-11),end:e};default:throw new Error(`unknown preset ${n}`)}}function q(n,t){return Math.round((C(t)-C(n))/864e5)+1}function tt(n,t){return n<t?n:t}function rt(n,t,e,a,r){if(e.unit==="month"){let l=N(n);if(a<0)return{start:k(l,-e.n),end:m(l,-1)};let u=k(l,e.n);return{start:u,end:tt(m(k(u,e.n),-1),r)}}let o=e.n||q(n,t);if(a<0)return{start:m(n,-o),end:m(n,-1)};let i=tt(m(t,o),r);return{start:m(i,-(o-1)),end:i}}var v={chevronLeft:"M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z",chevronRight:"M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z",refresh:"M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z",download:"M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z",history:"M13.5,8H12V13L16.28,15.54L17,14.33L13.5,12.25V8M13,3A9,9 0 0,0 4,12H1L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.32,18.21 8.06,16.94L6.64,18.36C8.27,20 10.5,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3",clock:"M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z",check:"M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z",menu:"M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"};function x(n){return`<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="${n}"/></svg>`}var F={title:"Moj Elektro",meter:"Meter",range:"Period",from:"From",to:"To",apply:"Apply",presets:{latest:"Latest day",last7:"Last 7 days",last30:"Last 30 days",thisMonth:"This month",prevMonth:"Previous month",last12:"Last 12 months",custom:"Custom"},imported:"Imported",exported:"Exported",exportNotProvided:"Not provided for this meter",exportUnknown:"Not yet known",dailyAverage:"Daily average",dailyAverageHint:"Complete days only",peak:"Peak 15-min average demand",coverage:"Coverage",partial:"Partial period",complete:"Complete",flagged:"{n} flagged readings",noFlagged:"No quality flags",delayedTitle:"Delayed data",delayedText:"Moj Elektro publishes readings with a delay, usually the next day and sometimes later. 15-minute values are not live.",latestMeasurement:"Latest measurement",lastRefresh:"Last refresh",never:"never",refresh:"Refresh",refreshRange:"Re-download this period",exportCsv:"Export CSV",showTable:"Show table",hideTable:"Hide table",energy:"Energy (kWh)",power:"Average power (kW)",chartIntervals:"15-minute values",chartDays:"Daily totals",chartMonths:"Monthly totals",missing:"Missing",flaggedLegend:"Flagged quality",loading:"Loading\u2026",noMeters:"No meters are set up. Add the Moj Elektro Plus integration under Settings \u2192 Devices & services.",noData:"No readings are stored for this period.",noDataBackfill:"History is still downloading. Data appears as months complete.",errorTitle:"Could not load data",retry:"Retry",offline:"Home Assistant is offline. Showing the last loaded data.",backfill:"History download",backfillRunning:"Downloading month {done} of {total}",backfillComplete:"History complete",backfillError:"History download stopped: {error}",backfillRetry:"Resume download",rangeRunning:"Re-downloading: {done} of {total}",timezoneNote:"Days and months follow Europe/Ljubljana time.",costNote:"Costs are not shown: tariffs, network charges and taxes are not part of meter data.",time:"Time",date:"Date",month:"Month",value:"Value",quality:"Quality",adminOnly:"Only administrators can refresh data.",started:"Download started",menu:"Menu",kwh:"kWh",kw:"kW",at:"at",previousPeriod:"Previous period",nextPeriod:"Next period",readings:"{present} of {expected} readings"},ut={title:"Moj Elektro",meter:"Merilno mesto",range:"Obdobje",from:"Od",to:"Do",apply:"Uporabi",presets:{latest:"Zadnji dan",last7:"Zadnjih 7 dni",last30:"Zadnjih 30 dni",thisMonth:"Ta mesec",prevMonth:"Prej\u0161nji mesec",last12:"Zadnjih 12 mesecev",custom:"Po meri"},imported:"Prejeta energija",exported:"Oddana energija",exportNotProvided:"Za to merilno mesto ni na voljo",exportUnknown:"\u0160e ni znano",dailyAverage:"Dnevno povpre\u010Dje",dailyAverageHint:"Samo celotni dnevi",peak:"Najvi\u0161ja 15-min povpre\u010Dna mo\u010D",coverage:"Pokritost",partial:"Delno obdobje",complete:"Celotno",flagged:"{n} meritev z oznako kakovosti",noFlagged:"Brez oznak kakovosti",delayedTitle:"Podatki z zamikom",delayedText:"Moj Elektro objavlja meritve z zamikom, obi\u010Dajno naslednji dan, v\u010Dasih pozneje. 15-minutne vrednosti niso sprotne.",latestMeasurement:"Zadnja meritev",lastRefresh:"Zadnja osve\u017Eitev",never:"nikoli",refresh:"Osve\u017Ei",refreshRange:"Ponovno prenesi obdobje",exportCsv:"Izvozi CSV",showTable:"Prika\u017Ei tabelo",hideTable:"Skrij tabelo",energy:"Energija (kWh)",power:"Povpre\u010Dna mo\u010D (kW)",chartIntervals:"15-minutne vrednosti",chartDays:"Dnevne vsote",chartMonths:"Mese\u010Dne vsote",missing:"Manjka",flaggedLegend:"Oznaka kakovosti",loading:"Nalaganje\u2026",noMeters:"Ni nastavljenih merilnih mest. Dodajte integracijo Moj Elektro Plus pod Nastavitve \u2192 Naprave in storitve.",noData:"Za to obdobje ni shranjenih meritev.",noDataBackfill:"Zgodovina se \u0161e prena\u0161a. Podatki se prika\u017Eejo, ko so meseci preneseni.",errorTitle:"Podatkov ni bilo mogo\u010De nalo\u017Eiti",retry:"Poskusi znova",offline:"Home Assistant ni povezan. Prikazani so nazadnje nalo\u017Eeni podatki.",backfill:"Prenos zgodovine",backfillRunning:"Prena\u0161am mesec {done} od {total}",backfillComplete:"Zgodovina je prenesena",backfillError:"Prenos zgodovine se je ustavil: {error}",backfillRetry:"Nadaljuj prenos",rangeRunning:"Ponovni prenos: {done} od {total}",timezoneNote:"Dnevi in meseci so po \u010Dasu Europe/Ljubljana.",costNote:"Stro\u0161ki niso prikazani: tarife, omre\u017Enina in davki niso del merilnih podatkov.",time:"\u010Cas",date:"Datum",month:"Mesec",value:"Vrednost",quality:"Kakovost",adminOnly:"Podatke lahko osve\u017Eijo le skrbniki.",started:"Prenos se je za\u010Del",menu:"Meni",kwh:"kWh",kw:"kW",at:"ob",previousPeriod:"Prej\u0161nje obdobje",nextPeriod:"Naslednje obdobje",readings:"{present} od {expected} meritev"},mt={en:F,sl:ut};function st(n){return(n?.locale?.language||n?.language||"en").toLowerCase().startsWith("sl")?"sl":"en"}function ot(n){let t=mt[n]||F;return(e,a={})=>{let r=e.split(".").reduce((o,i)=>o?.[i],t)??e.split(".").reduce((o,i)=>o?.[i],F)??e;return String(r).replace(/\{(\w+)\}/g,(o,i)=>String(a[i]??""))}}var nt=`
:host {
  display: block;
  min-height: 100vh;
  background: var(--primary-background-color, #fafafa);
  color: var(--primary-text-color, #212121);
  font-family: var(--ha-font-family-body, var(--paper-font-body1_-_font-family, Roboto, sans-serif));
  --me-import: var(--energy-grid-consumption-color, #488fc2);
  --me-export: var(--energy-grid-return-color, #8353d1);
  --me-flagged: var(--warning-color, #ffa600);
  --me-missing: var(--disabled-text-color, #bdbdbd);
  --me-ok: var(--success-color, #43a047);
  --me-radius: var(--ha-card-border-radius, 12px);
  --me-line: var(--divider-color, rgba(0, 0, 0, 0.12));
  --me-quiet: var(--secondary-text-color, #727272);
  --me-hover: rgba(var(--rgb-primary-text-color, 33, 33, 33), 0.06);
  --me-press: rgba(var(--rgb-primary-color, 3, 169, 244), 0.14);
}
* { box-sizing: border-box; }
::selection { background: var(--me-press); }
.visually-hidden {
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap;
}
.ic { width: 20px; height: 20px; fill: currentColor; flex: none; }

/* Header bar, matching Home Assistant's own panels. */
.toolbar {
  display: flex; align-items: center; gap: 4px;
  min-height: var(--header-height, 56px); padding: 0 12px 0 16px;
  background: var(--app-header-background-color, var(--primary-color));
  color: var(--app-header-text-color, var(--text-primary-color, #fff));
  border-bottom: var(--app-header-border-bottom, none);
  position: sticky; top: 0; z-index: 2;
  padding-top: env(safe-area-inset-top);
}
.toolbar h1 { font-size: 20px; font-weight: 400; margin: 0 0 0 4px; }

.page { max-width: 1120px; margin: 0 auto; padding: 16px 24px 32px; display: grid; gap: 16px; }
/* Grid items default to their content width; let wide rows scroll instead. */
.page > * { min-width: 0; }

/* Buttons */
button {
  font: inherit; font-size: 14px; font-weight: 500; cursor: pointer;
  border-radius: 18px; padding: 0 16px; min-height: 36px;
  border: 1px solid var(--primary-color); background: var(--primary-color);
  color: var(--text-primary-color, #fff);
}
button:disabled { opacity: 0.45; cursor: default; }
.chip {
  background: transparent; color: var(--primary-text-color);
  border-color: var(--me-line); font-weight: 400;
}
.chip:not(:disabled):hover { background: var(--me-hover); }
.chip[aria-pressed="true"] {
  background: var(--me-press); color: var(--primary-color);
  border-color: transparent; font-weight: 500;
}
.icon-btn {
  display: inline-grid; place-items: center; width: 40px; min-height: 40px; padding: 0;
  border: 0; border-radius: 50%; background: transparent; color: inherit;
}
.icon-btn:not(:disabled):hover { background: var(--me-hover); }
.text-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 0 12px;
  border: 0; background: transparent; color: var(--primary-color);
}
.text-btn:not(:disabled):hover { background: var(--me-press); }
button:focus-visible, select:focus-visible, input:focus-visible,
#chart:focus-visible {
  outline: 2px solid var(--primary-color); outline-offset: 2px;
}

/* Range controls */
.controls { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; }
.presets { display: flex; flex-wrap: wrap; gap: 6px; }
.chip[aria-expanded="true"] { border-color: var(--primary-color); }
.meter-pick select { min-width: 200px; }
select, input {
  font: inherit; font-size: 14px; color: var(--primary-text-color); min-height: 36px;
  background: var(--card-background-color, #fff);
  border: 1px solid var(--me-line); border-radius: 8px; padding: 4px 10px;
}
.custom-fields { display: flex; flex-wrap: wrap; gap: 8px; align-items: end; flex-basis: 100%; }
.custom-fields[hidden] { display: none; }
.field { display: grid; gap: 4px; font-size: 12px; color: var(--me-quiet); }

/* Period heading: what the numbers below describe. */
.period { display: grid; gap: 2px; padding-top: 8px; }
.period-row { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; }
.period-title { display: flex; align-items: center; gap: 4px; min-width: 0; margin-left: -8px; }
.period h2 { font-size: 24px; font-weight: 400; line-height: 1.25; margin: 0 4px; text-wrap: balance; }
.period-actions { display: flex; flex-wrap: wrap; gap: 4px; }
.meter-name { margin: 0; color: var(--me-quiet); font-size: 14px; }

/* Summary: one surface, the total leads, the other figures follow. */
.summary {
  display: grid; grid-template-columns: minmax(220px, auto) 1fr; gap: 24px; align-items: start;
  background: var(--card-background-color, #fff); border: 1px solid var(--me-line);
  border-radius: var(--me-radius); padding: 20px 24px;
}
.total { display: grid; gap: 6px; }
.total-label, .figures dt { font-size: 13px; color: var(--me-quiet); }
.total-value { font-size: 40px; line-height: 1.1; font-weight: 400; font-variant-numeric: tabular-nums; }
.total-value small, .figures small { font-size: 0.5em; color: var(--me-quiet); font-weight: 400; }
.total-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; font-size: 13px; }
.pill { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 500; }
.pill.ok { color: var(--me-ok); background: rgba(var(--rgb-success-color, 67, 160, 71), 0.14); }
.pill.partial { color: var(--primary-text-color); background: rgba(var(--rgb-warning-color, 255, 166, 0), 0.22); }
.quiet { color: var(--me-quiet); }
.figures {
  margin: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px 24px; padding-left: 24px; border-left: 1px solid var(--me-line); align-self: stretch;
}
.figures div { display: grid; gap: 4px; align-content: start; }
.figures dd { margin: 0; font-size: 20px; font-variant-numeric: tabular-nums; }
.figures dd .quiet { font-size: 14px; }
.sub { display: block; font-size: 12px; color: var(--me-quiet); margin-top: 2px; }

/* Chart */
.card {
  background: var(--card-background-color, #fff);
  border-radius: var(--me-radius); border: 1px solid var(--me-line);
  box-shadow: var(--ha-card-box-shadow, none); padding: 16px 20px;
}
h2 { font-size: 16px; font-weight: 500; margin: 0; }
.chart-head { display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.chart-tools, .seg { display: flex; flex-wrap: wrap; gap: 6px; }
.chart-wrap { width: 100%; overflow: hidden; }
#chart { width: 100%; border-radius: 8px; }
svg:not(.ic) { display: block; max-width: 100%; height: auto; }
svg .grid { stroke: var(--me-line); stroke-width: 1; }
svg .zero { stroke: var(--me-quiet); stroke-width: 1; }
svg .axis { fill: var(--me-quiet); font-size: 11px; font-variant-numeric: tabular-nums; }
svg .bar.import { fill: var(--me-import); }
svg .bar.export { fill: var(--me-export); }
svg .bar.flagged { fill: var(--me-flagged); }
svg .bar.partial { opacity: 0.6; }
svg .missing { fill: var(--me-missing); }
svg .active { stroke: var(--primary-text-color); stroke-width: 1.5; }
svg .hit { fill: transparent; }
.tooltip { min-height: 22px; font-size: 13px; margin-top: 6px; font-variant-numeric: tabular-nums; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 12px; color: var(--me-quiet); margin-top: 8px; }
.sw { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: middle; }
.sw.import { background: var(--me-import); } .sw.export { background: var(--me-export); }
.sw.flagged { background: var(--me-flagged); } .sw.missing { background: var(--me-missing); }
.table-wrap { max-height: 420px; overflow: auto; margin-top: 12px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--me-line); }
thead th { position: sticky; top: 0; background: var(--card-background-color, #fff); }

/* Delayed-data notice and data status: always visible, never loud. */
.status {
  display: flex; flex-wrap: wrap; align-items: center; gap: 12px 32px;
  padding: 14px 0 0; border-top: 1px solid var(--me-line); font-size: 14px;
}
.delayed { display: flex; gap: 10px; align-items: flex-start; flex: 1 1 100%; color: var(--me-quiet); }
.delayed p { margin: 0; max-width: 72ch; }
.delayed strong { color: var(--primary-text-color); font-weight: 500; }
.delayed .ic { color: var(--info-color, #039be5); margin-top: 1px; }
.facts { margin: 0; display: flex; flex-wrap: wrap; gap: 8px 32px; }
.facts dt { font-size: 12px; color: var(--me-quiet); }
.facts dd { margin: 0; font-variant-numeric: tabular-nums; }
.progress { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.progress progress { width: 180px; height: 6px; accent-color: var(--primary-color); }
.progress.ok { color: var(--me-ok); }
.progress.warn, .warn { color: var(--error-color, #db4437); }
.actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-left: auto; }
.muted, .foot { color: var(--me-quiet); font-size: 13px; }
.foot { margin: 0; }

/* States */
.banner { padding: 10px 14px; border-radius: 8px; background: var(--card-background-color); border: 1px solid currentColor; }
.banner.info { color: var(--info-color, #039be5); }
.loading { opacity: 0.55; transition: opacity 0.2s ease-out; }
.state { padding: 32px 16px; text-align: center; color: var(--me-quiet); }
.error h2 { color: var(--error-color, #db4437); }

@media (max-width: 720px) {
  .page { padding: 12px 16px 24px; gap: 14px; }
  .summary { grid-template-columns: 1fr; gap: 16px; padding: 16px; }
  .figures { padding-left: 0; border-left: 0; padding-top: 16px; border-top: 1px solid var(--me-line); grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .total-value { font-size: 34px; }
  .period h2 { font-size: 20px; }
  .card { padding: 14px; }
  .meter-pick, .meter-pick select { width: 100%; }
  /* One swipeable row of presets instead of four rows of chips. */
  .controls { display: grid; grid-template-columns: minmax(0, 1fr); }
  .presets {
    flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; min-width: 0;
    margin: 0 -16px; padding: 2px 16px; scroll-padding-inline: 16px;
  }
  .presets::-webkit-scrollbar { display: none; }
  .presets .chip { flex: none; }
  .custom-fields .field { flex: 1 1 130px; }
  .actions { margin-left: 0; }
}
@media (prefers-reduced-motion: reduce) { .loading { transition: none; } }
`;var it="mojelektro_plus",dt="mojelektro_plus.selected_meter",lt=3e3,gt=40,ft={latest:{unit:"day",n:1},last7:{unit:"day",n:7},last30:{unit:"day",n:30},thisMonth:{unit:"month",n:1},prevMonth:{unit:"month",n:1},last12:{unit:"month",n:12}},bt=new Set(["unknown_command","not_found"]);function vt(){try{return window.localStorage.getItem(dt)}catch{return null}}function xt(n){try{window.localStorage.setItem(dt,n)}catch{}}var W=class extends HTMLElement{constructor(){super(),this.attachShadow({mode:"open"}),this._state={status:"loading",meters:[],entryId:null,preset:"latest",start:null,end:null,data:null,dataLoading:!1,error:null,mode:"energy",showTable:!1,active:null,notice:null},this._seq=0,this._startRetries=0,this._width=640,this._onClick=this._onClick.bind(this),this._onChange=this._onChange.bind(this),this._onKey=this._onKey.bind(this),this._onPointer=this._onPointer.bind(this),this.shadowRoot.addEventListener("click",this._onClick),this.shadowRoot.addEventListener("change",this._onChange),this.shadowRoot.addEventListener("keydown",this._onKey),this.shadowRoot.addEventListener("pointermove",this._onPointer)}set hass(t){let e=!this._hass,a=this._hass?.connected!==!1,r=this._lang;if(this._hass=t,this._lang=st(t),this._t=ot(this._lang),e){this._init();return}(r!==this._lang||a!==(t.connected!==!1))&&(this._render(),!a&&t.connected!==!1&&this._reload()),this._menu&&(this._menu.hass=t)}get hass(){return this._hass}set narrow(t){let e=this._narrow!==t;this._narrow=t,e&&this._hass&&this._render()}set panel(t){this._panel=t}set route(t){this._route=t}connectedCallback(){!this._resize&&typeof ResizeObserver<"u"&&(this._resize=new ResizeObserver(t=>{let e=Math.floor(t[0].contentRect.width);e&&Math.abs(e-this._width)>4&&(this._width=e,this._renderChartOnly())})),this._hass&&!this._unsub&&this._initialised&&this._subscribe()}disconnectedCallback(){this._resize?.disconnect(),this._unsubscribe(),clearTimeout(this._debounce),clearTimeout(this._subRetry),clearTimeout(this._loadRetry)}_ws(t,e={}){return this._hass.callWS({type:`${it}/${t}`,...e})}async _init(){this._initialised=!0,this._render(),this._subscribe(),await this._loadMeters(!0)}async _subscribe(){if(!(this._unsub||!this._hass?.connection))try{this._unsub=await this._hass.connection.subscribeMessage(t=>this._onServerUpdate(t),{type:`${it}/subscribe`})}catch{this._unsub=null,clearTimeout(this._subRetry),this.isConnected&&(this._subRetry=setTimeout(()=>this._subscribe(),lt))}}_unsubscribe(){if(this._unsub){let t=this._unsub;this._unsub=null,Promise.resolve(t()).catch(()=>{})}}_onServerUpdate(t){if(!t||t.entry_id!==this._state.entryId){this._loadMeters(!1);return}clearTimeout(this._debounce),this._debounce=setTimeout(()=>this._reload(),800)}async _reload(){await this._loadMeters(!1),this._state.start&&await this._loadData()}async _loadMeters(t){try{let e=await this._ws("meters");this._startRetries=0;let a=e.meters||[],r=this._state;if(r.meters=a,!a.length){r.status="empty",this._render();return}if(!a.some(o=>o.entry_id===r.entryId)){let o=vt();r.entryId=a.some(i=>i.entry_id===o)?o:a[0].entry_id}if(r.status="ready",t){this._applyPreset("latest");return}this._render()}catch(e){if(bt.has(e?.code)&&this._startRetries<gt){this._startRetries+=1,clearTimeout(this._loadRetry),this._loadRetry=setTimeout(()=>this._loadMeters(t),lt);return}this._state.status="error",this._state.error=e?.message||String(e),this._render()}}get _meter(){return this._state.meters.find(t=>t.entry_id===this._state.entryId)||null}_applyPreset(t){let e=this._state,a=at(t,this._meter?.latest_day,B());e.preset=t,e.start=a.start,e.end=a.end,e.unit=ft[t],e.customOpen=!1,e.active=null,this._loadData()}_stepBounds(){let t=this._state;if(!t.start)return{prev:!1,next:!1};let e=B(),a=this._meter,r=t.unit?.unit==="month"?e:a?.latest_day||e,o=a?.earliest_allowed||"0000-01-01";return{prev:t.start>o,next:t.end<r,first:o,last:r}}_step(t){let e=this._state,a=this._stepBounds();if(t<0&&!a.prev||t>0&&!a.next)return;let r=e.unit||{unit:"day",n:q(e.start,e.end)},o=rt(e.start,e.end,r,t,a.last);e.start=o.start,e.end=o.end,e.unit=r,e.preset="custom",e.active=null,this._loadData()}async _loadData(){let t=this._state;if(!t.entryId||!t.start)return;let e=++this._seq;t.dataLoading=!0,t.error=null,this._render();try{let a=await this._ws("data",{entry_id:t.entryId,start:t.start,end:t.end,resolution:"auto"});if(e!==this._seq)return;t.data=a,t.dataLoading=!1,t.active!=null&&t.active>=a.points.length&&(t.active=null)}catch(a){if(e!==this._seq)return;t.dataLoading=!1,t.error=a?.message||String(a)}this._render()}_onClick(t){let e=t.target.closest("[data-action]");if(!e){let o=t.target.closest("[data-i]");o&&(this._state.active=Number(o.dataset.i),this._renderChartOnly());return}let a=e.dataset.action,r=this._state;a==="preset"?this._applyPreset(e.dataset.preset):a==="step"?this._step(Number(e.dataset.dir)):a==="custom"?(r.customOpen=!r.customOpen,this._render(),r.customOpen&&this.shadowRoot.getElementById("start")?.focus()):a==="apply-range"?this._applyCustom():a==="retry"?r.status==="error"?this._init():this._loadData():a==="refresh"?this._refresh(!1):a==="refresh-range"?this._refresh(!0):a==="backfill"?this._backfill():a==="csv"?this._csv():a==="mode"?(r.mode=e.dataset.mode,this._render()):a==="table"?(r.showTable=!r.showTable,this._render()):a==="menu"&&this.dispatchEvent(new Event("hass-toggle-menu",{bubbles:!0,composed:!0}))}_onChange(t){t.target.id==="meter"&&(this._state.entryId=t.target.value,xt(t.target.value),this._state.data=null,this._applyPreset(this._state.preset==="custom"?"latest":this._state.preset))}_onKey(t){if(t.target.id==="chart"){let e=this._state,a=e.data?.points?.length||0;if(!a)return;let r=e.active??-1;if(t.key==="ArrowRight")r=Math.min(a-1,r+1);else if(t.key==="ArrowLeft")r=Math.max(0,r<0?a-1:r-1);else if(t.key==="Home")r=0;else if(t.key==="End")r=a-1;else return;t.preventDefault(),e.active=r,this._renderChartOnly()}else(t.target.id==="start"||t.target.id==="end")&&t.key==="Enter"&&this._applyCustom()}_onPointer(t){let e=t.target.closest?.("rect.hit");if(!e)return;let a=Number(e.dataset.i);a!==this._state.active&&(this._state.active=a,this._renderChartOnly())}_applyCustom(){let t=this.shadowRoot,e=t.getElementById("start")?.value,a=t.getElementById("end")?.value,r=this._state;if(!V(e)||!V(a)||a<e){r.notice={kind:"error",text:this._t("errorTitle")},this._render();return}r.preset="custom",r.start=e,r.end=a,r.unit={unit:"day",n:q(e,a)},r.notice=null,r.active=null,this._loadData()}async _refresh(t){let e=this._state;try{let a={entry_id:e.entryId};t&&Object.assign(a,{start:e.start,end:e.end}),await this._ws("refresh",a),e.notice={kind:"info",text:this._t("started")}}catch(a){e.notice={kind:"error",text:a?.message||String(a)}}this._render(),this._reload()}async _backfill(){try{await this._ws("backfill",{entry_id:this._state.entryId})}catch(t){this._state.notice={kind:"error",text:t?.message||String(t)}}this._reload()}async _csv(){let t=this._state;try{let e=t.data?.resolution||"auto",a=await this._ws("csv",{entry_id:t.entryId,start:t.start,end:t.end,resolution:e}),r=new Blob([a.csv],{type:"text/csv;charset=utf-8"}),o=URL.createObjectURL(r),i=document.createElement("a");i.href=o,i.download=a.filename,this.shadowRoot.appendChild(i),i.click(),i.remove(),setTimeout(()=>URL.revokeObjectURL(o),1e3)}catch(e){t.notice={kind:"error",text:e?.message||String(e)},this._render()}}_fmt(t=2,e=0){return K(this._lang,t,e)}_pointLabel(t,e=!0){let a=this._state.data?.resolution;return a==="interval"?H(this._lang,t.end):a==="month"?U(this._lang,t.start):e?$(this._lang,t.start):$(this._lang,t.start,{dateStyle:"medium"})}_render(){let t=this._t,e=this._state,a=this._hass?.connected===!1,r=e.status==="loading"?`<div class="state" role="status">${s(t("loading"))}</div>`:e.status==="empty"?`<div class="state">${s(t("noMeters"))}</div>`:e.status==="error"?`<div class="card error" role="alert"><h2>${s(t("errorTitle"))}</h2><p>${s(e.error)}</p><button data-action="retry">${s(t("retry"))}</button></div>`:this._content();this.shadowRoot.innerHTML=`
      <style>${nt}</style>
      <div class="toolbar">
        ${this._narrow?'<span id="menu-slot"></span>':""}
        <h1>${s(t("title"))}</h1>
      </div>
      <main class="page" aria-busy="${e.dataLoading||e.status==="loading"}">
        ${a?`<div class="banner warn" role="status">${s(t("offline"))}</div>`:""}
        ${r}
      </main>`,this._mountMenu();let o=this.shadowRoot.getElementById("chart-wrap");o&&this._resize&&(this._resize.disconnect(),this._resize.observe(o))}_mountMenu(){let t=this.shadowRoot.getElementById("menu-slot");if(t)if(customElements.get("ha-menu-button")){let e=document.createElement("ha-menu-button");e.hass=this._hass,e.narrow=this._narrow,t.appendChild(e),this._menu=e}else t.innerHTML=`<button class="icon-btn" data-action="menu" aria-label="${s(this._t("menu"))}">${x(v.menu)}</button>`}_content(){let t=this._t,e=this._state,a=this._meter,r=!!this._hass?.user?.is_admin,o=e.meters.length>1,i=e.preset==="custom";return`
      <section class="controls" aria-label="${s(t("range"))}">
        ${o?`<label class="meter-pick"><span class="visually-hidden">${s(t("meter"))}</span>
                <select id="meter">${e.meters.map(l=>`<option value="${s(l.entry_id)}" ${l.entry_id===e.entryId?"selected":""}>${s(l.title)}</option>`).join("")}</select></label>`:""}
        <div class="presets" role="group" aria-label="${s(t("range"))}">
          ${et.map(l=>`<button class="chip" data-action="preset" data-preset="${l}" aria-pressed="${e.preset===l}">${s(t(`presets.${l}`))}</button>`).join("")}
          <button class="chip" data-action="custom" aria-expanded="${!!e.customOpen}" aria-controls="custom-fields" aria-pressed="${i}">${s(t("presets.custom"))}</button>
        </div>
        <div class="custom-fields" id="custom-fields" ${e.customOpen?"":"hidden"}>
          <label class="field">${s(t("from"))}<input id="start" type="date" value="${s(e.start)}" min="${s(a?.earliest_allowed||"")}"></label>
          <label class="field">${s(t("to"))}<input id="end" type="date" value="${s(e.end)}"></label>
          <button data-action="apply-range">${s(t("apply"))}</button>
        </div>
      </section>
      ${e.notice?`<div class="banner ${e.notice.kind==="error"?"warn":"info"}" role="status">${s(e.notice.text)}</div>`:""}
      ${this._periodHeader(a,r,o)}
      ${this._dataSection(a,r)}
      ${this._statusLine(a,r)}
      <p class="foot">${s(t("timezoneNote"))} ${s(t("costNote"))}</p>`}_periodLabel(){let t=this._state;return t.start?t.start===t.end?$(this._lang,t.start,{weekday:"short",day:"numeric",month:"long",year:"numeric"}):t.start.endsWith("-01")&&t.end===m(k(t.start,1),-1)?$(this._lang,t.start,{month:"long",year:"numeric"}):Y(this._lang,t.start,t.end):""}_periodHeader(t,e,a){let r=this._t,o=this._state,i=this._stepBounds();return`
      <section class="period" aria-label="${s(r("range"))}">
        <div class="period-row">
          <div class="period-title">
            <button class="icon-btn" data-action="step" data-dir="-1" aria-label="${s(r("previousPeriod"))}" ${i.prev?"":"disabled"}>${x(v.chevronLeft)}</button>
            <h2 id="period-heading" aria-live="polite">${s(this._periodLabel())}</h2>
            <button class="icon-btn" data-action="step" data-dir="1" aria-label="${s(r("nextPeriod"))}" ${i.next?"":"disabled"}>${x(v.chevronRight)}</button>
          </div>
          <div class="period-actions">
            ${e?`<button class="text-btn" data-action="refresh">${x(v.refresh)}<span>${s(r("refresh"))}</span></button>`:""}
            <button class="text-btn" data-action="csv" ${o.data?"":"disabled"}>${x(v.download)}<span>${s(r("exportCsv"))}</span></button>
          </div>
        </div>
        ${t?`<p class="meter-name">${a?"":`${s(t.title)} \xB7 `}${s(r("latestMeasurement"))} ${t.latest_reading?s(w(this._lang,t.latest_reading)):"\u2014"} (${s(r("delayedTitle").toLowerCase())})</p>`:""}
      </section>`}_statusLine(t,e){let a=this._t;if(!t)return"";let r=t.backfill||{},o=t.job,i="";if(o){let l=o.kind==="range"?"rangeRunning":"backfillRunning";i=`<div class="progress"><span>${s(a(l,{done:o.done+1>o.total?o.total:o.done+1,total:o.total}))}</span>
        <progress max="${o.total}" value="${o.done}" aria-label="${s(a("backfill"))}"></progress></div>`}else r.state==="error"?i=`<div class="progress warn">${s(a("backfillError",{error:r.error||""}))}
        ${e?`<button class="text-btn" data-action="backfill">${s(a("backfillRetry"))}</button>`:""}</div>`:r.state==="complete"&&(i=`<div class="progress ok">${x(v.check)}<span>${s(a("backfillComplete"))}</span></div>`);return`
      <section class="status" aria-label="${s(a("delayedTitle"))}">
        <div class="delayed">${x(v.clock)}
          <p><strong>${s(a("delayedTitle"))}</strong> \u2014 ${s(a("delayedText"))}</p>
        </div>
        <dl class="facts">
          <div><dt>${s(a("latestMeasurement"))}</dt><dd>${t.latest_reading?s(w(this._lang,t.latest_reading)):"\u2014"}</dd></div>
          <div><dt>${s(a("lastRefresh"))}</dt><dd>${t.last_success?s(w(this._lang,t.last_success)):s(a("never"))}</dd></div>
        </dl>
        ${i}
        <div class="actions">
          ${e?`<button class="text-btn" data-action="refresh-range">${x(v.history)}<span>${s(a("refreshRange"))}</span></button>`:`<span class="muted">${s(a("adminOnly"))}</span>`}
        </div>
      </section>`}_dataSection(t,e){let a=this._t,r=this._state;if(r.error&&!r.data)return`<div class="card error" role="alert"><h2>${s(a("errorTitle"))}</h2><p>${s(r.error)}</p><button data-action="retry">${s(a("retry"))}</button></div>`;if(!r.data)return`<div class="state" role="status">${s(a("loading"))}</div>`;let o=r.data,i=o.summary,l=o.points.some(g=>g.import!=null),u=this._fmt(2,2),c=i.import,_=(i.days||1)>1,M=o.export_status!=="available"?`<span class="quiet">${s(a(o.export_status==="not_provided"?"exportNotProvided":"exportUnknown"))}</span>`:`${u(i.export?.total)} <small>${a("kwh")}</small>`,T=i.peak?`${this._fmt(2,2)(i.peak.power_kw)} <small>${a("kw")}</small><span class="sub">${s(a("at"))} ${s(_?w(this._lang,i.peak.interval_end):H(this._lang,i.peak.interval_end))}</span>`:"\u2014",L=c.complete?`<span class="pill ok">${s(a("complete"))}</span>`:`<span class="pill partial">${s(a("partial"))} \xB7 ${this._fmt(1)(c.coverage)} %</span>`,R=r.error?`<div class="banner warn" role="alert">${s(r.error)} <button data-action="retry">${s(a("retry"))}</button></div>`:"",j=a(o.resolution==="interval"?"chartIntervals":o.resolution==="day"?"chartDays":"chartMonths"),D=l?"":`<div class="state">${s(t?.backfill?.state==="running"||t?.job?a("noDataBackfill"):a("noData"))}</div>`,z=o.points.some(g=>g.export>0);return`
      ${R}
      <section class="summary ${r.dataLoading?"loading":""}" aria-live="polite" aria-labelledby="period-heading">
        <div class="total">
          <span class="total-label">${s(a("imported"))}</span>
          <span class="total-value">${u(c.total)} <small>${a("kwh")}</small></span>
          <span class="total-meta">${L}
            <span class="quiet">${s(a("readings",{present:c.present,expected:c.expected}))}${c.flagged?` \xB7 ${s(a("flagged",{n:c.flagged}))}`:""}</span></span>
        </div>
        <dl class="figures">
          <div><dt>${s(a("exported"))}</dt><dd>${M}</dd></div>
          ${_?`<div><dt>${s(a("dailyAverage"))}</dt><dd>${u(i.daily_average)} <small>${a("kwh")}</small><span class="sub">${s(a("dailyAverageHint"))}</span></dd></div>`:""}
          <div><dt>${s(a("peak"))}</dt><dd>${T}</dd></div>
        </dl>
      </section>
      <section class="card chart-card ${r.dataLoading?"loading":""}">
        <div class="chart-head">
          <h2>${s(j)}</h2>
          <div class="chart-tools">
            ${o.resolution==="interval"?`<div role="group" class="seg" aria-label="${s(j)}">
                    <button class="chip" data-action="mode" data-mode="energy" aria-pressed="${r.mode==="energy"}">${s(a("energy"))}</button>
                    <button class="chip" data-action="mode" data-mode="power" aria-pressed="${r.mode==="power"}">${s(a("power"))}</button>
                  </div>`:""}
            <button class="chip" data-action="table" aria-expanded="${r.showTable}">${s(r.showTable?a("hideTable"):a("showTable"))}</button>
          </div>
        </div>
        ${D}
        <div id="chart-wrap" class="chart-wrap">
          <div id="chart" tabindex="0" role="group" aria-roledescription="chart" aria-label="${s(j)}">${l?this._chartSvg():""}</div>
          <div id="tooltip" class="tooltip" aria-live="polite">${l?this._tooltip():""}</div>
        </div>
        <div class="legend">
          <span><i class="sw import"></i>${s(a("imported"))}</span>
          ${z?`<span><i class="sw export"></i>${s(a("exported"))}</span>`:""}
          <span><i class="sw flagged"></i>${s(a("flaggedLegend"))}</span>
          <span><i class="sw missing"></i>${s(a("missing"))}</span>
        </div>
        ${r.showTable?this._table():""}
      </section>`}_chartSvg(){let t=this._state.data,e=Math.max(260,this._width),a=this._narrow?200:260,r=t.resolution==="interval"?2:0;return X({points:t.points,resolution:t.resolution,mode:this._state.mode,width:e,height:a,active:this._state.active,label:o=>this._pointLabel(o),fmt:this._fmt(r)})}_tooltip(){let t=this._t,e=this._state,a=e.data?.points?.[e.active];if(!a)return"";let r=this._fmt(3),o=e.data.resolution==="interval"&&e.mode==="power",i=c=>c==null?s(t("missing")):`${r(o?c*4:c)} ${t(o?"kw":"kwh")}`,l=e.data.resolution==="interval"?`${w(this._lang,a.start)} \u2013 ${H(this._lang,a.end)}`:e.data.resolution==="month"?U(this._lang,a.start):$(this._lang,a.start,{dateStyle:"full"}),u=e.data.resolution==="interval"?(a.import_q||[]).map(c=>e.meters.find(_=>_.entry_id===e.entryId)?.qualities?.[c]||c).join(", "):a.expected?`${this._fmt(1)(a.coverage)} % ${t("coverage").toLowerCase()}${a.flagged?`, ${t("flagged",{n:a.flagged})}`:""}`:"";return`<strong>${s(l)}</strong> \xB7 ${s(t("imported"))}: ${i(a.import)}${a.export!==void 0?` \xB7 ${s(t("exported"))}: ${i(a.export)}`:""}${u?` \xB7 ${s(u)}`:""}`}_table(){let t=this._t,e=this._state.data,a=this._fmt(3),r=e.resolution==="interval"?t("time"):e.resolution==="day"?t("date"):t("month"),o=e.export_status==="available",i=e.points.map(l=>{let u=e.resolution==="interval"?w(this._lang,l.end):this._pointLabel(l,!1),c=e.resolution==="interval"?(l.import_q||[]).join(" "):`${this._fmt(1)(l.coverage)} %`;return`<tr><th scope="row">${s(u)}</th><td>${l.import==null?s(t("missing")):a(l.import)}</td>${o?`<td>${l.export==null?s(t("missing")):a(l.export)}</td>`:""}<td>${s(c)}</td></tr>`}).join("");return`<div class="table-wrap"><table><thead><tr><th scope="col">${s(r)}</th><th scope="col">${s(t("imported"))} (${t("kwh")})</th>${o?`<th scope="col">${s(t("exported"))} (${t("kwh")})</th>`:""}<th scope="col">${s(e.resolution==="interval"?t("quality"):t("coverage"))}</th></tr></thead><tbody>${i}</tbody></table></div>`}_renderChartOnly(){let t=this.shadowRoot.getElementById("chart"),e=this.shadowRoot.getElementById("tooltip");!t||!this._state.data||this._state.data.points.some(a=>a.import!=null)&&(t.innerHTML=this._chartSvg(),e&&(e.innerHTML=this._tooltip()))}};customElements.get("mojelektro-plus-panel")||customElements.define("mojelektro-plus-panel",W);export{W as MojElektroPanel,q as spanDays};

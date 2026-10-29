/* Static OpenFIDS preview: translate the real NQA feed into local API responses. */
(() => {
  'use strict';
  const SOURCE='https://flights.nqa.au/v1/flights';
  const nativeFetch=window.fetch.bind(window);
  const base=new URL('.',document.currentScript.src);
  let cache=null, timestamp=0, pending=null;
  const json=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
  const str=x=>x==null?'':String(x);
  function convert(raw){
    if(!raw||typeof raw!=='object'||!['A','D'].includes(raw.direction)||!raw.scheduled)return null;
    const p=raw.port||{},a=raw.aircraft||{},s=raw.status||{},carrier=str(raw.airline).toUpperCase();
    const code=str(raw.flight);
    const number=str(raw.flightNumber)||(code.startsWith(carrier)?code.slice(carrier.length):'');
    return {id:'NQA-'+str(raw.airport)+'-'+(raw.id||raw.direction+'-'+code+'-'+raw.scheduled),
      airport:str(raw.airport),vector:raw.direction,public:raw.public,airline:carrier,flightNumber:number,
      portIATA:str(p.iata),portName:str(p.name),terminal:str(raw.terminal),scheduled:raw.scheduled,
      estimated:raw.estimated||null,actual:raw.actual||null,onBlock:raw.onBlock||null,offBlock:raw.offBlock||null,
      statusMsgPublic:str(s.public),gate:str(raw.gate),stand:str(raw.stand),carousel:str(raw.carousel),
      acType:str(a.type),acRego:str(a.registration),codeShares:Array.isArray(raw.codeShares)?raw.codeShares:[],
      flightType:str(raw.flightType)};
  }
  function tell(feed){
    const status=document.getElementById('demoConnection');
    if(status)status.textContent=feed.ok&&!feed.stale?'NQA connected · '+feed.count+' flights':(feed.count?'Offline · showing last received flights':'Feed unavailable · retrying');
    if(parent!==window)parent.postMessage({type:'openfids-demo-feed',ok:!!feed.ok,stale:!!feed.stale,
      count:Number.isFinite(feed.count)?feed.count:null},location.origin);
  }
  async function requestFeed(){
    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),12000);
    let data;
    try {
      const r=await nativeFetch(SOURCE,{mode:'cors',cache:'no-store',signal:controller.signal});
      if(!r.ok)throw Error('NQA HTTP '+r.status);
      data=await r.json();
    } finally { clearTimeout(timeout); }
    if(!Array.isArray(data?.flights))throw Error('Invalid flight data');
    const flights=data.flights.map(convert).filter(Boolean);
    const feed={ok:!data.stale,stale:!!data.stale,source:SOURCE,sourceTimestamp:data.sourceTimestamp,
      receivedAt:data.receivedAt,staleReasons:data.staleReasons||[],count:flights.length,
      updated:new Date().toLocaleTimeString('en-AU',{timeZone:'Australia/Brisbane',hour12:false}),
      message:data.stale?'NQA reports stale data':'Live NQA flight feed'};
    cache={flights,feed};timestamp=Date.now();tell(feed);return cache;
  }
  async function load(){
    if(cache&&Date.now()-timestamp<15000)return cache;
    if(!pending)pending=requestFeed().finally(()=>{pending=null;});
    return pending;
  }
  window.fetch=async function(input,init){
    const url=typeof input==='string'?input:input?.url;
    if(!url)return nativeFetch(input,init);
    let path;
    try{const parsed=new URL(url,location.href);
      if(parsed.origin!==location.origin)return nativeFetch(input,init);
      path=parsed.pathname.replace(/.*\/api\//,'/api/');
    }catch(e){return nativeFetch(input,init);}
    const method=(init?.method||(input instanceof Request?input.method:'GET')).toUpperCase();
    if(path==='/api/status'&&method==='GET')return json({app:'openfids-demo',data_dir:'Read-only online demo',
      title:'Cairns Airport FIDS',customTitle:'',defaultAirport:'CNS',feed:cache?.feed||{ok:false,message:'Connecting'}});
    if(path==='/api/database'&&method==='GET')return nativeFetch(new URL('database.json',base));
    if(path==='/api/flights'&&method==='GET'){
      try{return json(await load());}
      catch(e){const feed={ok:false,stale:true,source:SOURCE,message:'NQA feed unavailable: '+e.message,
        count:cache?.flights.length||0,sourceTimestamp:cache?.feed.sourceTimestamp};
        if(cache)cache={flights:cache.flights,feed};
        tell(feed);return json({flights:cache?.flights||[],feed});}
    }
    if(path==='/api/custom-flights'&&method==='GET')return json({flights:[]});
    if(path.startsWith('/api/'))return json({detail:'Disabled in read-only demo'},403);
    return nativeFetch(input,init);
  };
  document.addEventListener('DOMContentLoaded',()=>{
    document.querySelectorAll('[data-panel="add"], #quit').forEach(x=>{x.style.display='none';x.setAttribute('aria-hidden','true');});
    const banner=document.createElement('div');
    banner.className='demo-banner';
    banner.innerHTML='<a href="../" target="_top">← OpenFIDS</a><span>Browser demo · preferences stay in this browser</span><span id="demoConnection" role="status">Connecting…</span>';
    document.body.prepend(banner);
    const style=document.createElement('style');
    style.textContent='.demo-banner{position:fixed;inset:0 0 auto;z-index:999;min-height:34px;display:flex;gap:16px;align-items:center;justify-content:space-between;padding:8px 16px;background:#142532;color:#b5edcf;font:11px system-ui,sans-serif;border-bottom:1px solid #ffffff20}.demo-banner a{color:inherit;text-decoration:none;font-weight:700}body{padding-top:36px}body .app>aside{top:36px;height:calc(100vh - 36px)}@media(max-width:600px){.demo-banner>span:nth-child(2){display:none}}';
    document.head.append(style);
    const label=document.querySelector('.brand .lbl');if(label)label.title='OpenFIDS interactive read-only demo';
  });
  document.addEventListener('keydown',e=>{
    if(e.key.toLowerCase()!=='n'||e.ctrlKey||e.metaKey||e.altKey)return;
    if(['INPUT','SELECT','TEXTAREA'].includes(document.activeElement?.tagName))return;
    e.stopImmediatePropagation();e.preventDefault();
  },true);
})();

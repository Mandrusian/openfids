/* Exercise the static API adapter without a browser or a live airport feed. */
const vm=require('node:vm');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const source=fs.readFileSync('docs/demo/shim.js','utf8');
const fixture={flights:[null,{airport:'CNS',id:1,direction:'A',scheduled:'2026-10-29T16:00:00+10:00',airline:'QF',flight:'QF123',flightNumber:123,gate:22,port:{iata:'SYD',name:'Sydney'},aircraft:{type:'738'},status:{public:'Landed'}}],stale:false};
let now=0, calls=0, failure=false, body=fixture;
class Clock extends Date {static now(){return now;}}
const context={URL,Response,Request,AbortController,setTimeout,clearTimeout,Date:Clock,location:new URL('https://example.test/openfids/demo/'),document:{currentScript:{src:'https://example.test/openfids/demo/shim.js'},getElementById(){return null;},addEventListener(){}},parent:{postMessage(){}},window:{fetch:async(input)=>{if(String(input).includes('database.json'))return new Response('{}');calls++;if(failure)throw Error('Network disconnected');return new Response(JSON.stringify(body));}}};
vm.runInNewContext(source,context);
const fetch=context.window.fetch;
(async()=>{
  const [a,b]=await Promise.all([fetch('/api/flights'),fetch('/openfids/api/flights')]);
  const data=await a.json();await b.json();
  assert.equal(calls,1,'concurrent loads share one feed request');
  assert.equal(data.flights.length,1,'invalid rows are ignored');
  assert.equal(data.flights[0].flightNumber,'123');
  assert.equal(data.flights[0].gate,'22');
  assert.equal(data.feed.ok,true);
  assert.equal((await fetch('/api/custom-flights',{method:'POST'})).status,403);
  assert.equal((await fetch('/api/quit',{method:'POST'})).status,403);
  assert.deepEqual(await (await fetch('/api/database')).json(),{});
  now=16000;failure=true;
  const offline=await (await fetch('/api/flights')).json();
  assert.equal(offline.feed.ok,false);assert.equal(offline.feed.stale,true);
  assert.equal(offline.flights.length,1,'last received flights survive failure');
  failure=false;body={flights:fixture.flights,stale:true};
  const stale=await (await fetch('/api/flights')).json();
  assert.equal(stale.feed.ok,false);assert.equal(stale.feed.stale,true);
  now=32000;body={invalid:true};
  assert.equal((await (await fetch('/api/flights')).json()).feed.ok,false);
  now=48000;body=fixture;
  assert.equal((await (await fetch('/api/flights')).json()).feed.ok,true,'recovers after failure');
  console.log('PASS: static demo paths, numeric fields, deduplication, stale data, offline recovery and write protection');
})().catch(error=>{console.error(error);process.exitCode=1;});

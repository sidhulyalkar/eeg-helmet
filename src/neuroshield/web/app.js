"use strict";
// Synchronized render only. No diagnostic logic or contact with real biosignals.
const $ = (id) => document.getElementById(id);
const paramKeys = ["mount_k_n_m","mount_c_ns_m","mount_travel_mm","liner_k_n_m","liner_c_ns_m"];
const state = {config:null, output:null, index:0, playing:false, lastFrame:null, pending:false};
const theme = {cyan:"#5bddd1", blue:"#75aaff", orange:"#ffae82", purple:"#b59dff", subtle:"#5f7690", text:"#e5f1ff"};
const clamp = (x,a,b)=>Math.min(b,Math.max(a,x));
const number = (x,n=1)=>Number(x).toLocaleString("en-US",{minimumFractionDigits:n,maximumFractionDigits:n});
const trace = (obj,key)=>obj?.traces?.[key] || [];

function params(){return Object.fromEntries(paramKeys.map(k=>[k,Number($(k).value)]));}
function showParams(){
  const p=params();
  $("v_mount_k_n_m").textContent=number(p.mount_k_n_m/1000,0)+" kN/m";
  $("v_mount_c_ns_m").textContent=number(p.mount_c_ns_m,0)+" Ns/m";
  $("v_mount_travel_mm").textContent=number(p.mount_travel_mm,1)+" mm";
  $("v_liner_k_n_m").textContent=number(p.liner_k_n_m/1000,0)+" kN/m";
  $("v_liner_c_ns_m").textContent=number(p.liner_c_ns_m,0)+" Ns/m";
}
function setParams(obj){paramKeys.forEach(k=>{$(k).value=obj[k]});showParams();}
function setLoading(yes){state.pending=yes;$("simulate").disabled=yes;$("simulate").textContent=yes?"Computing comparison...":"↗ Run comparison";}
async function run(){
  if(state.pending)return;
  state.playing=false;state.lastFrame=null;$("play").textContent="▶ Play";
  setLoading(true);
  try{
    const res=await fetch("/api/compare",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({scenario:$("scenario").value,parameters:params()})});
    const data=await res.json();if(!res.ok)throw new Error(data.error||`HTTP ${res.status}`);
    state.output=data;state.index=0;$("scrub").value=0;
    $("scenario-name").textContent=data.candidate.scenario_detail.label;
    showMetrics();showWarnings();draw();
  }catch(err){$("warnings").textContent="Unable to simulate: "+err.message;}
  finally{setLoading(false)}
}
function showMetrics(){
  const data=state.output;
  const fields=[
    ["peak_head_accel_g","Peak linear accel","g",2],
    ["peak_angular_accel_rad_s2","Peak angular accel","rad/s²",0],
    ["peak_neck_torque_proxy_nm","Neck torque proxy","N·m",1],
    ["peak_mount_deflection_mm","Mount displacement","mm",1]
  ];
  const node=$("metrics");node.replaceChildren();
  fields.forEach(([key,label,unit,precision])=>{
    const base=data.baseline.metrics[key],current=data.candidate.metrics[key],pct=data.relative_change_pct[key];
    const outer=document.createElement("article");outer.className="metric";
    const head=document.createElement("div");head.className="metric-name";head.textContent=label;
    const values=document.createElement("div");values.className="metric-values";
    const strong=document.createElement("strong");strong.textContent=number(current,precision);
    const small=document.createElement("small");small.textContent=unit;values.append(strong,small);
    const ref=document.createElement("div");ref.className="metric-comparison";ref.textContent="Reference: "+number(base,precision)+" "+unit;
    const delta=document.createElement("div");delta.className="metric-delta "+(Math.abs(pct)<.05?"neutral":pct<0?"better":"worse");
    delta.textContent=pct===null?"No reference":`${pct>0?"+":""}${number(pct,1)}% vs reference`;
    outer.append(head,values,ref,delta);node.append(outer);
  });
}
function showWarnings(){
  const data=state.output;const el=$("warnings");el.replaceChildren();
  const seen=[...new Set([...data.candidate.warnings,...data.baseline.warnings])];
  for(const warning of seen){const line=document.createElement("span");line.textContent=warning;el.append(line);}
}
function getContext(id){
  const canvas=$(id);if(!canvas)return null;
  const ratio=window.devicePixelRatio||1;const w=canvas.clientWidth||600,h=canvas.clientHeight||250;
  const ww=Math.round(w*ratio),hh=Math.round(h*ratio);
  if(canvas.width!==ww||canvas.height!==hh){canvas.width=ww;canvas.height=hh;}
  const ctx=canvas.getContext("2d");ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,w,h);
  return {ctx,w,h};
}
function grid(ctx,w,h,step=25){ctx.strokeStyle="#1e3142";ctx.lineWidth=.5;ctx.beginPath();for(let x=0;x<w;x+=step){ctx.moveTo(x,0);ctx.lineTo(x,h);}for(let y=0;y<h;y+=step){ctx.moveTo(0,y);ctx.lineTo(w,y);}ctx.stroke();}
function label(ctx,content,x,y,color="#8da4ba",size=10){ctx.font=`600 ${size}px ui-sans-serif,system-ui`;ctx.fillStyle=color;ctx.fillText(content,x,y);}
function circle(ctx,x,y,r,color,width=1){ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.stroke();}
function pointer(ctx,x1,y1,x2,y2,color){ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();const a=Math.atan2(y2-y1,x2-x1);ctx.beginPath();ctx.moveTo(x2,y2);ctx.lineTo(x2-12*Math.cos(a-.5),y2-12*Math.sin(a-.5));ctx.lineTo(x2-12*Math.cos(a+.5),y2-12*Math.sin(a+.5));ctx.fill();}
function current(){return state.output?.candidate;}
function val(key){const t=current()?.traces?.[key];return t?.[state.index]??0;}
function drawImpact(){
  const v=getContext("impact");if(!v)return;const {ctx,w,h}=v;grid(ctx,w,h);
  const cx=w*.48,cy=h*.50,sc=Math.min(w/430,h/250);ctx.save();ctx.translate(cx,cy);ctx.scale(sc,sc);
  // Hand-authored helmet silhouette, diagram only.
  ctx.shadowColor="#4c9dff45";ctx.shadowBlur=20;
  ctx.fillStyle="#203951";ctx.strokeStyle="#89b8d9";ctx.lineWidth=3;
  ctx.beginPath();ctx.moveTo(-95,22);ctx.bezierCurveTo(-105,-69,-44,-106,32,-97);
  ctx.bezierCurveTo(100,-82,112,-26,89,4);ctx.lineTo(70,18);ctx.lineTo(51,3);
  ctx.lineTo(27,15);ctx.lineTo(8,70);ctx.lineTo(-63,69);ctx.bezierCurveTo(-80,61,-99,37,-95,22);ctx.closePath();ctx.fill();ctx.stroke();ctx.shadowBlur=0;
  ctx.strokeStyle="#3a7296";ctx.lineWidth=5;ctx.beginPath();ctx.arc(-3,-11,64,Math.PI*.82,Math.PI*1.92);ctx.stroke();
  ctx.strokeStyle="#8fe1e4";ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(51,6);ctx.quadraticCurveTo(130,-25,133,24);
  ctx.lineTo(113,64);ctx.lineTo(30,64);ctx.moveTo(43,31);ctx.lineTo(128,31);ctx.moveTo(85,8);ctx.lineTo(85,62);ctx.stroke();
  ctx.fillStyle="#61d4cd";ctx.beginPath();ctx.arc(-10,12,7,0,Math.PI*2);ctx.fill();
  ctx.restore();
  const s=current()?.scenario_detail||{contact:"facemask",angle_deg:48};const contact=s.contact==="facemask";
  const ix=cx+(contact?126:-45)*sc,iy=cy+(contact?12:-90)*sc;
  const amp=clamp(Math.abs(val("external_force_n"))/s.force_n,0,1);
  circle(ctx,ix,iy,14+12*amp,`rgba(255,170,108,${0.4+amp*.6})`,1.5);
  if(amp>.04)circle(ctx,ix,iy,25+38*amp,"#ef955764",2);
  pointer(ctx,ix+(contact?86:20),iy-(contact?39:60),ix+5,iy-5,"#ffb77a");
  label(ctx,contact?"FACEMASK IMPACT":"SHELL IMPACT",17,24,"#ffc087",10);
  label(ctx,`${number(s.angle_deg,0)}° CONTACT ORIENTATION`,17,h-17,"#8ca5bb",9);
}
function drawNeck(){
  const v=getContext("neck");if(!v)return;const {ctx,w,h}=v;grid(ctx,w,h);
  const x=w*.52,y=h*.76,angle=clamp(val("head_relative_torso_deg"),-30,30)*Math.PI/180;
  ctx.fillStyle="#233a55";ctx.strokeStyle="#719abf";ctx.lineWidth=2;
  ctx.beginPath();ctx.moveTo(x-95,h+3);ctx.lineTo(x-78,y-6);ctx.quadraticCurveTo(x-20,y-35,x-18,y-53);
  ctx.lineTo(x+18,y-53);ctx.quadraticCurveTo(x+20,y-35,x+78,y-6);ctx.lineTo(x+95,h+3);ctx.closePath();ctx.fill();ctx.stroke();
  ctx.save();ctx.translate(x,y-57);ctx.rotate(angle);
  ctx.fillStyle="#4b7c97";ctx.fillRect(-15,-45,30,47);
  ctx.beginPath();ctx.ellipse(0,-84,40,51,0,0,Math.PI*2);ctx.fillStyle="#a7bed0";ctx.fill();ctx.strokeStyle="#e9f5ff";ctx.stroke();
  ctx.beginPath();ctx.moveTo(35,-100);ctx.lineTo(47,-92);ctx.lineTo(34,-86);ctx.stroke();
  ctx.fillStyle="#1d3550";ctx.beginPath();ctx.arc(18,-91,3.5,0,Math.PI*2);ctx.fill();
  ctx.restore();
  ctx.strokeStyle="#516d88";ctx.setLineDash([5,5]);ctx.beginPath();ctx.moveTo(x,22);ctx.lineTo(x,h-10);ctx.stroke();ctx.setLineDash([]);
  label(ctx,"FIXED TORSO",18,h-17,"#8bacc5",10);
  label(ctx,"MODEL NECK ROTATION",18,23,"#b7a8ff",10);
  ctx.strokeStyle=theme.purple;ctx.beginPath();ctx.arc(x,y-57,69,-Math.PI*.70,-Math.PI*.70+angle,false);ctx.stroke();
}
function drawBrain(){
  const v=getContext("brain");if(!v)return;const {ctx,w,h}=v;grid(ctx,w,h);
  const magnitude=clamp(val("mechanical_response_proxy"),0,1.5),x=w*.52,y=h*.48;
  const scale=Math.min(1.35,w/400,h/240);ctx.save();ctx.translate(x,y);ctx.scale(scale,scale);
  const heat=ctx.createRadialGradient(-17,-6,5,5,0,135);
  heat.addColorStop(0,magnitude>.28?"#c47b56":"#4d8394");
  heat.addColorStop(.5,magnitude>.7?"#a86b4c":"#356878");heat.addColorStop(1,"#152f45");
  ctx.fillStyle=heat;ctx.strokeStyle="#b4c9d9";ctx.lineWidth=2;
  ctx.beginPath();ctx.moveTo(-114,4);ctx.bezierCurveTo(-138,-42,-93,-80,-60,-75);ctx.bezierCurveTo(-43,-109,3,-91,15,-77);
  ctx.bezierCurveTo(59,-107,100,-66,97,-36);ctx.bezierCurveTo(135,-13,122,24,99,35);
  ctx.bezierCurveTo(90,74,43,75,23,60);ctx.bezierCurveTo(3,88,-42,69,-54,63);ctx.bezierCurveTo(-93,71,-126,37,-114,4);ctx.closePath();ctx.fill();ctx.stroke();
  ctx.strokeStyle="#91bdca";ctx.lineWidth=1.4;ctx.globalAlpha=.7;
  const factor=clamp(magnitude,0,1)*9;
  for(let k=0;k<6;k++){ctx.beginPath();const baseY=-57+k*21;ctx.moveTo(-89,baseY);ctx.bezierCurveTo(-47,baseY-26+factor, -29,baseY+35-factor,5,baseY-8);ctx.bezierCurveTo(37,baseY-33+factor,63,baseY+30-factor,97,baseY-7);ctx.stroke();}
  ctx.globalAlpha=1;ctx.restore();
  label(ctx,"ILLUSTRATIVE RESPONSE FIELD",17,24,"#ffb18f",10);
  label(ctx,"NO BRAIN-STRAIN PREDICTION",17,h-17,"#e1b3a6",9);
  if(magnitude>.18){circle(ctx,x,y,65+magnitude*25,"#ff956247",1.5);}
}
function drawSignals(){
  const v=getContext("signals");if(!v)return;const {ctx,w,h}=v;grid(ctx,w,h);
  const cand=current();if(!cand)return;
  const sig=cand.signals,axes=[["eeg_uV",theme.cyan,"EEG",120],["emg_left_a_uV",theme.blue,"EMG L",85],["emg_right_a_uV",theme.purple,"EMG R",85]];
  const left=63,right=w-12,band=h/3,ns=sig.eeg_uV.length;
  // Unsafe EEG sections must be visible, not silently interpolated away.
  ctx.fillStyle="#e6745528";for(let j=0;j<ns-1;j++){if(sig.eeg_signal_quality[j]<.5){let x=left+j/(ns-1)*(right-left);ctx.fillRect(x,0,(right-left)/(ns-1)+1.5,band);}}
  axes.forEach(([key,color,name,range],row)=>{
    const center=(row+.50)*band;
    ctx.strokeStyle="#385169";ctx.setLineDash([3,6]);ctx.beginPath();ctx.moveTo(left,center);ctx.lineTo(right,center);ctx.stroke();ctx.setLineDash([]);
    label(ctx,name,11,center-3,color,9);
    ctx.strokeStyle=color;ctx.lineWidth=1.4;ctx.beginPath();
    for(let i=0;i<ns;i++){
      const x=left+i/(ns-1)*(right-left),y=center-sig[key][i]/range*band*.35;
      if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }ctx.stroke();
  });
  const mx=left+state.index/(ns-1)*(right-left);
  ctx.strokeStyle="#ecf6ffbb";ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(mx,0);ctx.lineTo(mx,h);ctx.stroke();
  label(ctx,"LOW-QUALITY INTERVALS SHADED",Math.max(70,w-220),15,"#d99b89",9);
}
function drawTimeChart(id,key){
  const v=getContext(id);if(!v)return;const {ctx,w,h}=v;const data=state.output;if(!data)return;
  const a=trace(data.baseline,key),b=trace(data.candidate,key),left=34,right=w-10,top=15,bottom=h-20;
  let bound=Math.max(1,...a.map(Math.abs),...b.map(Math.abs))*1.09;
  grid(ctx,w,h,32);const zero=top+(bottom-top)/2;
  ctx.strokeStyle="#52657a";ctx.beginPath();ctx.moveTo(left,zero);ctx.lineTo(right,zero);ctx.stroke();
  label(ctx,number(bound,0),3,top+6,"#718fa5",9);label(ctx,number(-bound,0),3,bottom,"#718fa5",9);
  [[a,theme.subtle],[b,theme.cyan]].forEach(([arr,color])=>{
    ctx.lineWidth=1.8;ctx.strokeStyle=color;ctx.beginPath();
    const skip=Math.max(1,Math.floor(arr.length/1000));
    for(let i=0;i<arr.length;i+=skip){const x=left+i/(arr.length-1)*(right-left),y=zero-arr[i]/bound*(bottom-top)*.5;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.stroke();
  });
  const mx=left+state.index/(a.length-1)*(right-left);ctx.strokeStyle="#ecf4ff9c";ctx.beginPath();ctx.moveTo(mx,top);ctx.lineTo(mx,bottom);ctx.stroke();
  label(ctx,"0",left,bottom+14,"#728da2",9);label(ctx,"250 ms",Math.max(0,right-39),bottom+14,"#728da2",9);
}
function draw(){
  if(!state.output)return;
  const out=current(),i=state.index,ms=out.traces.time_ms[i];
  $("time-display").textContent=number(ms,1)+" ms";
  $("force-val").textContent=number(val("external_force_n"),0)+" N";
  $("neck-val").textContent=number(val("head_relative_torso_deg"),2)+"°";
  $("brain-val").textContent=number(val("mechanical_response_proxy"),3);
  const q=out.signals.eeg_signal_quality[i];$("quality-val").textContent=q<.5?"LOW / EXCLUDE":q<.8?"LIMITED":"SYNTHETIC / OK";
  drawImpact();drawNeck();drawBrain();drawSignals();drawTimeChart("chart-g","head_linear_g");drawTimeChart("chart-a","head_angular_accel_rad_s2");
}
function setIndex(i){if(!current())return;state.index=clamp(i,0,current().traces.time_ms.length-1);$("scrub").value=Math.round(500*state.index/(current().traces.time_ms.length-1));draw();}
function playFrame(timestamp){
  if(!state.playing||!current())return;
  if(state.lastFrame!==null){
    const now=current().traces.time_ms[state.index];const next=now+Math.min(50,timestamp-state.lastFrame)/14;
    const dt=current().sample_interval_ms;setIndex(Math.floor(next/dt));
    if(state.index>=current().traces.time_ms.length-1){state.playing=false;$("play").textContent="↻ Replay";return;}
  }
  state.lastFrame=timestamp;requestAnimationFrame(playFrame);
}
function togglePlay(){
  if(!current())return;state.playing=!state.playing;state.lastFrame=null;
  if(state.playing){if(state.index>=current().traces.time_ms.length-1)setIndex(0);$("play").textContent="Ⅱ Pause";requestAnimationFrame(playFrame);}
  else $("play").textContent="▶ Play";
}
function exportJSON(){
  if(!state.output)return;
  const blob=new Blob([JSON.stringify(state.output,null,2)],{type:"application/json"});
  const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=`neuroshield-${current().scenario}-SYNTHETIC.json`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);
}
async function qualify(){
  const btn=$("qualify");const result=$("qualification-output");
  if(btn.disabled)return;
  btn.disabled=true;result.textContent="Comparing time steps...";
  try{
    const response=await fetch("/api/qualify",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({scenario:$("scenario").value,parameters:params()})});
    const report=await response.json();if(!response.ok)throw new Error(report.error||"Unable to qualify");
    result.replaceChildren();
    const top=document.createElement("p");top.textContent=report.status+" · tolerance " +
      number(report.tolerance_fraction*100,1)+"% · S0 / synthetic only";result.append(top);
    report.metrics.forEach(metric=>{
      const line=document.createElement("div");
      line.textContent=metric.metric+": "+number(metric.medium_to_fine_change*100,2)+"% step sensitivity";
      line.className=metric.within_tolerance?"qual-ok":"qual-fail";result.append(line);
    });
    const note=document.createElement("p");note.textContent="Step refinement is NOT physical or clinical validation. No headform measurements or independent integrator.";result.append(note);
  }catch(err){result.textContent="Numerical qualification failed: "+err.message}
  finally{btn.disabled=false}
}
async function init(){
  try{
    const response=await fetch("/api/config");if(!response.ok)throw new Error(`HTTP ${response.status}`);
    state.config=await response.json();const menu=$("scenario");
    Object.entries(state.config.scenarios).forEach(([key,value])=>{const option=document.createElement("option");option.value=key;option.textContent=value.label;menu.append(option);});
    menu.value="oblique";setParams(state.config.suggested);
    paramKeys.forEach(k=>$(k).addEventListener("input",showParams));
    menu.addEventListener("change",run);$("simulate").addEventListener("click",run);
    $("reset").addEventListener("click",()=>{setParams(state.config.suggested);run();});
    $("qualify").addEventListener("click",qualify);
    $("scrub").addEventListener("input",()=>{state.playing=false;$("play").textContent="▶ Play";setIndex(Math.round(Number($("scrub").value)/500*(current()?.traces.time_ms.length-1||0)));});
    $("play").addEventListener("click",togglePlay);$("export").addEventListener("click",exportJSON);
    window.addEventListener("resize",draw);
    document.addEventListener("keydown",(e)=>{if(["INPUT","SELECT","BUTTON"].includes(document.activeElement?.tagName))return;if(e.key==="ArrowRight")setIndex(state.index+5);if(e.key==="ArrowLeft")setIndex(state.index-5);if(e.key===" "){e.preventDefault();togglePlay();}});
    await run();
  }catch(err){$("warnings").textContent="Initialization failed: "+err.message;}
}
init();

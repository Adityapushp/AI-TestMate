const $ = (id) => document.getElementById(id);
async function api(path, options={}) {
  const response = await fetch(path, {headers:{"Content-Type":"application/json"}, ...options});
  if (!response.ok) throw new Error((await response.json()).detail || "Request failed");
  return response.json();
}
async function health(){
  try { const h=await api("/api/health"); $("health").textContent=`API online · ${h.chat_provider} mode`; }
  catch(e){ $("health").textContent="API unavailable"; }
}
function render(data){
  $("runid").textContent=data.run_id; $("passed").textContent=data.passed;
  $("failed").textContent=data.failed; $("total").textContent=data.total;
  $("message").textContent=`${data.workflow} workflow`;
  $("results").className="results";
  $("results").innerHTML=data.results.map(r=>`
    <article class="case"><div class="case-top"><strong>${r.case_id}</strong>
    <span class="pill ${r.passed?'ok':'bad'}">${r.passed?'PASS':'FAIL'}</span></div>
    <p>${escapeHtml(r.question)}</p><p><b>Answer:</b> ${escapeHtml(r.answer)}</p>
    <div class="muted">Score: ${r.score} · Relevance: ${r.relevance} · Groundedness proxy: ${r.groundedness_proxy}</div>
    <div class="muted">${escapeHtml((r.feedback||[]).join(" "))}</div></article>`).join("");
}
function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
$("run").addEventListener("click",async()=>{
  $("run").disabled=true; $("message").textContent="Running tests…";
  try {render(await api("/api/run-tests",{method:"POST"}));}
  catch(e){$("message").textContent=e.message;}
  finally{$("run").disabled=false;}
});
$("ask").addEventListener("click",async()=>{
  const message=$("question").value.trim(); if(!message)return;
  $("answer").textContent="Thinking…";
  try {const result=await api("/api/chat",{method:"POST",body:JSON.stringify({message})});
    $("answer").textContent=result.answer+"  [Sources: "+result.sources.join(", ")+"]";}
  catch(e){$("answer").textContent=e.message;}
});
health();

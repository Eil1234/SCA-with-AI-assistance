// ── Show result ───────────────────────────────────────────────────────────────
function showResult(data, atkItems, elapsed) {
  document.getElementById('r-dot').style.display='none';
  document.getElementById('r-dot-static').style.display='block';
  document.getElementById('r-status').textContent='分析完成';

  const isAI=data.ai_attack===true;
  const aiByteIndex=Number(data.target_byte_index??0);
  const keyHex=(data.key_hex||'').toUpperCase();
  const byteArr=keyHex.match(/.{1,2}/g)||[];
  const knownKey=getKnownKey();
  const backendAIKey=isAI&&/^[0-9a-fA-F]{2}$/.test(data.correct_key_byte_hex||'')?parseInt(data.correct_key_byte_hex,16):null;
  const expectedAIByte=isAI?(knownKey&&knownKey.length>aiByteIndex?knownKey[aiByteIndex]:backendAIKey):null;
  const comparable=isAI?(byteArr.length===1&&expectedAIByte!==null):(knownKey&&knownKey.length===byteArr.length);
  const correct=comparable?(isAI?(parseInt(byteArr[0],16)===expectedAIByte?1:0):byteArr.filter((hex,i)=>parseInt(hex,16)===knownKey[i]).length):0;
  const comparisonTotal=isAI?1:(knownKey?.length||0);
  const isKeyResult=isAI||byteArr.length===16||byteArr.length===32;
  const aesBits=selectedAesBits||(atkItems.some(a=>isAes256Id(a.id))?256:128);
  const aesLabel='AES-'+aesBits;

  document.getElementById('r-key').textContent=isAI
    ? `AES-128 Byte ${aiByteIndex} 猜測：${keyHex||'—'}；資料集正確值：${backendAIKey===null?'未提供':data.correct_key_byte_hex.toUpperCase()}；最終 rank：${data.final_correct_key_rank??'—'}`
    : (keyHex||(data.note||'此分析不回復金鑰'));

  // ── 處理傳統攻擊的 byte plots（從 extra.plots_by_byte 取得）──────────
  const plotsByByte = !isAI && data.extra && data.extra.plots_by_byte ? data.extra.plots_by_byte : [];

  const kbRow=document.getElementById('r-key-bytes');
  kbRow.innerHTML='';
  byteArr.forEach((hex,i)=>{
    const d=document.createElement('div');
    d.className='kb';
    d.textContent=hex;
    if(comparable){
      const expected=isAI?expectedAIByte:knownKey[i];
      d.classList.add(parseInt(hex,16)===expected?'correct':'wrong');
    }else d.classList.add('found');
    if(isAI)d.title=`AES-128 Byte ${aiByteIndex}`;
    
    // ── 為傳統攻擊的 byte 加上點擊事件 ────────────────────────
    if(!isAI && plotsByByte.length > 0){
      d.style.cursor='pointer';
      d.style.position='relative';
      
      // 查找該 byte 對應的 plot
      const plotData = plotsByByte.find(p => p.byte_index === i);
      
      if(plotData && plotData.plot_base64){
        d.addEventListener('click', (e) => {
          e.stopPropagation();
          toggleByteImagePopup(hex, i, plotData.plot_base64);
        });
      }
    }
    
    kbRow.appendChild(d);
  });

  const scoreBar=document.getElementById('r-score-bar');
  if(comparable){
    scoreBar.classList.add('vis');
    if(isAI){
      scoreBar.className='score-bar vis '+(correct?'perfect':'zero');
      scoreBar.innerHTML=correct
        ? `✓ AI 猜中 AES-128 第 <strong>${aiByteIndex}</strong> 個 key byte；正確金鑰最終排名 <strong>${data.final_correct_key_rank}</strong>`
        : `AI 未猜中 AES-128 Byte ${aiByteIndex}；正確值最終排名 <strong>${data.final_correct_key_rank}</strong>`;
    }else if(correct===comparisonTotal){
      scoreBar.className='score-bar vis perfect';scoreBar.innerHTML='🎉 完美攻擊！猜中全部 <strong>'+correct+'/'+comparisonTotal+'</strong> 個 byte';
    }else if(correct>=Math.ceil(comparisonTotal/2)){
      scoreBar.className='score-bar vis partial';scoreBar.innerHTML='猜中 <strong>'+correct+'/'+comparisonTotal+'</strong> 個 byte　— 失誤 '+(comparisonTotal-correct)+' 個';
    }else{
      scoreBar.className='score-bar vis zero';scoreBar.innerHTML='猜中 <strong>'+correct+'/'+comparisonTotal+'</strong> 個 byte　— 建議增加 trace 數量或換演算法';
    }
  }else scoreBar.className='score-bar';

  document.getElementById('rN').textContent=Number(data.num_traces||traceN||0).toLocaleString();
  document.getElementById('rL').textContent=Number(data.trace_length||traceL||0).toLocaleString();
  document.getElementById('rAlgo').textContent=isAI?`${String(data.model_type||'AI').toUpperCase()} / ${String(data.leakage_model||'').toUpperCase()} / ${String(data.dataset_type||'')}`:atkItems.map(a=>a.id.toUpperCase()).join('+');
  document.getElementById('rTime').textContent=elapsed+'s';

  const accuracy=comparable?Math.round(correct/comparisonTotal*100):null;
  document.getElementById('conf-fg').style.width=(accuracy===null?0:accuracy)+'%';
  document.getElementById('conf-lbl').textContent=isAI
    ? `AI 僅驗證 AES-128 Byte ${aiByteIndex}：${accuracy===null?'無正確值可比對':accuracy+'%'}`
    : (accuracy!==null?'已知金鑰比對準確率：'+accuracy+'%':(isKeyResult?'未提供相同長度的已知金鑰，無法計算準確率':'SNR 洩漏點分析完成'));

  // ── AI 模式時顯示總圖，傳統攻擊時隱藏（圖表已嵌入 byte 上）──
  const plot=document.getElementById('r-plot');
  if(isAI && data.plot_base64){
    document.getElementById('r-img').src='data:image/png;base64,'+data.plot_base64;
    plot.style.display='block';
  }else{
    plot.style.display='none';
  }

  const hasTemplate=atkItems.some(a=>isTemplateId(a.id));
  const hasMIA=atkItems.some(a=>a.id==='mia'||a.id==='mia256');
  let advice='建議採用 Masking，並搭配隨機延遲等 Hiding 防護降低功耗洩漏。';
  if(isAI)advice='AI 模型能辨識資料相依功耗特徵時，建議採用 First-Order Masking、隨機延遲與量測對齊擾動，並以不同裝置資料重新驗證模型泛化能力。';
  else if(hasTemplate)advice='Template Attack 偵測到 HW 洩漏時，建議導入 First-Order Masking，並在 POI 附近加入隨機延遲 jitter。';
  else if(hasMIA)advice='MIA 可偵測非線性洩漏，建議採用均勻電流消耗設計、WDDL 或資料遮罩。';
  if(pipeItems.some(p=>p.id==='_report')){document.getElementById('r-advice-txt').textContent=advice;document.getElementById('r-advice').style.display='block';}
  else document.getElementById('r-advice').style.display='none';

  const verified=isAI?(data.key_byte_verified===true):(comparable&&correct===comparisonTotal);
  const risk=isAI?(verified?'高風險證據（High，單一 byte）':'待驗證（Unverified）'):(verified?'高危險（Critical）':(isKeyResult?'待驗證（Unverified）':'洩漏分析（Diagnostic）'));
  const restoreStatus=isAI
    ? `只評估 AES-128 Byte ${aiByteIndex}：${verified?'猜測正確':'猜測未命中'}；不代表完整 16-byte 金鑰已還原`
    : (isKeyResult?(comparable?(verified?'成功':'部分／失敗'):'已產生猜測，未提供正確長度金鑰驗證'):'不適用（SNR 不回復金鑰）');
  currentReportPayload={
    product_name:document.getElementById('report-product-name')?.value.trim()||'',
    target_name:document.getElementById('report-target-name')?.value.trim()||'',
    test_organization:document.getElementById('report-org-name')?.value.trim()||'',
    aes_version:aesLabel,
    attack_methods:atkItems.map(a=>a.id.toUpperCase()),
    num_traces:Number(data.num_traces||traceN||0),
    trace_length:Number(data.trace_length||traceL||0),
    elapsed_seconds:Number(elapsed||0),
    key_hex:keyHex||null,
    key_restore_status:restoreStatus,
    key_verified:verified,
    known_key_correct_bytes:comparable?correct:null,
    known_key_total_bytes:comparable?comparisonTotal:null,
    risk_level:risk
  };
  currentReportPlot=data.plot_base64||'';currentSecurityReport=null;
  const reportEl=document.getElementById('security-report');if(reportEl)reportEl.innerHTML='<div class="report-empty">正在建立符合標準條文映射的報告…</div>';
  document.getElementById('report-generate-btn').disabled=false;document.getElementById('report-download-btn').disabled=true;
  document.getElementById('r-out').style.display='block';generateAiReport();
}

// ── 點擊 byte 展開/收起圖表的浮動視窗 ────────────────────────────────────
function toggleByteImagePopup(hexValue, byteIndex, plotBase64){
  const existingPopup = document.getElementById(`byte-popup-${byteIndex}`);
  
  if(existingPopup){
    // 已存在則移除（收起）
    existingPopup.remove();
    return;
  }
  
  // 先關閉其他已開啟的 popup
  document.querySelectorAll('[id^="byte-popup-"]').forEach(p => p.remove());
  
  // 建立新 popup
  const popup = document.createElement('div');
  popup.id = `byte-popup-${byteIndex}`;
  popup.className = 'byte-image-popup';
  popup.innerHTML = `
    <div class="byte-popup-content">
      <div class="byte-popup-header">
        <span class="byte-popup-title">Byte ${byteIndex} (${hexValue})</span>
        <button class="byte-popup-close" onclick="document.getElementById('byte-popup-${byteIndex}').remove()">✕</button>
      </div>
      <div class="byte-popup-body">
        <img src="data:image/png;base64,${plotBase64}" alt="Byte ${byteIndex} Plot" />
      </div>
    </div>
  `;
  
  document.body.appendChild(popup);
  popup.style.display = 'block';
  
  // 點擊背景關閉
  popup.addEventListener('click', (e) => {
    if(e.target === popup){
      popup.remove();
    }
  });
}

(function(){(function(){let e=document.currentScript;function t(){let t=e||[...document.querySelectorAll(`script[src*="widget.iife.js"]`)].pop();if(!t)return;let n=t.getAttribute(`data-api-url`)||new URL(t.src).origin,r=t.getAttribute(`data-campaign-id`)||``,i=t.getAttribute(`data-api-key`)||``;if(!r||!i)return;let a=null,o=!1,s=!1;function c(){let e=document.createElement(`style`);e.textContent=`
      #iq-widget-btn {
        position: fixed; bottom: 24px; right: 24px; z-index: 9999;
        width: 56px; height: 56px; border-radius: 50%;
        background: #4f46e5; color: #fff; border: none; cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,.25); font-size: 24px;
        display: flex; align-items: center; justify-content: center;
        transition: background .2s;
      }
      #iq-widget-btn:hover { background: #4338ca; }
      #iq-widget-popup {
        position: fixed; bottom: 92px; right: 24px; z-index: 9999;
        width: 340px; max-height: 520px; border-radius: 12px;
        background: #fff; box-shadow: 0 8px 32px rgba(0,0,0,.18);
        display: flex; flex-direction: column; overflow: hidden;
        font-family: system-ui, sans-serif; font-size: 14px;
      }
      #iq-widget-popup.iq-hidden { display: none; }
      #iq-widget-header {
        background: #4f46e5; color: #fff; padding: 14px 16px;
        font-weight: 600; font-size: 15px;
      }
      #iq-widget-messages {
        flex: 1; overflow-y: auto; padding: 16px;
        display: flex; flex-direction: column; gap: 10px;
      }
      .iq-msg { max-width: 85%; padding: 10px 12px; border-radius: 10px; line-height: 1.45; }
      .iq-msg-bot { background: #f1f0fe; color: #1e1b4b; align-self: flex-start; border-bottom-left-radius: 2px; }
      .iq-msg-user { background: #4f46e5; color: #fff; align-self: flex-end; border-bottom-right-radius: 2px; }
      #iq-widget-footer {
        display: flex; border-top: 1px solid #e5e7eb; padding: 10px;
      }
      #iq-widget-input {
        flex: 1; border: 1px solid #d1d5db; border-radius: 8px;
        padding: 8px 10px; font-size: 14px; outline: none;
      }
      #iq-widget-input:focus { border-color: #4f46e5; }
      #iq-widget-send {
        margin-left: 8px; background: #4f46e5; color: #fff;
        border: none; border-radius: 8px; padding: 8px 14px;
        cursor: pointer; font-size: 14px;
      }
      #iq-widget-send:disabled { opacity: .5; cursor: default; }
    `,document.head.appendChild(e)}function l(){let e=document.createElement(`button`);e.id=`iq-widget-btn`,e.innerHTML=`💬`,e.setAttribute(`aria-label`,`Open survey`);let t=document.createElement(`div`);t.id=`iq-widget-popup`,t.classList.add(`iq-hidden`),t.innerHTML=`
        <div id="iq-widget-header">Survey</div>
        <div id="iq-widget-messages"></div>
        <div id="iq-widget-footer">
          <input id="iq-widget-input" type="text" placeholder="Type your answer…" />
          <button id="iq-widget-send">Send</button>
        </div>
      `,document.body.appendChild(e),document.body.appendChild(t),e.addEventListener(`click`,()=>{!t.classList.toggle(`iq-hidden`)&&!a&&!o&&!s&&p()}),document.getElementById(`iq-widget-send`).addEventListener(`click`,m),document.getElementById(`iq-widget-input`).addEventListener(`keydown`,e=>{e.key===`Enter`&&m()})}function u(e,t){let n=document.getElementById(`iq-widget-messages`),r=document.createElement(`div`);r.className=`iq-msg iq-msg-${t}`,r.textContent=e,n.appendChild(r),n.scrollTop=n.scrollHeight}function d(e){let t=document.getElementById(`iq-widget-send`),n=document.getElementById(`iq-widget-input`);t.disabled=e,n.disabled=e}async function f(e){let t={campaign_id:r,session_id:a,answer:e||null,user_id:`anonymous`},o=await fetch(`${n}/public/survey`,{method:`POST`,headers:{"Content-Type":`application/json`,"X-API-Key":i},body:JSON.stringify(t)});if(!o.ok)throw Error(`Server error ${o.status}`);return o.json()}async function p(){if(!(s||a)){s=!0,d(!0);try{let e=await f(null);a=e.session_id,u(e.question,`bot`),e.survey_ended&&h()}catch{u(`Failed to start survey. Please try again.`,`bot`)}finally{s=!1,d(!1)}}}async function m(){if(o||!a)return;let e=document.getElementById(`iq-widget-input`),t=e.value.trim();if(t){e.value=``,u(t,`user`),d(!0);try{let e=await f(t);u(e.question,`bot`),e.survey_ended&&h()}catch{u(`Something went wrong. Please try again.`,`bot`)}finally{d(!1)}}}function h(){o=!0;let e=document.getElementById(`iq-widget-footer`);e.innerHTML=`<p style='padding:10px;color:#6b7280;margin:0'>Thank you for completing the survey!</p>`}c(),l()}document.readyState===`loading`?document.addEventListener(`DOMContentLoaded`,t):t()})()})();

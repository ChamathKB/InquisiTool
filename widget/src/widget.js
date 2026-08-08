(function () {
  const script = document.currentScript;
  const API_URL = script.getAttribute("data-api-url") || "";
  const CAMPAIGN_ID = script.getAttribute("data-campaign-id") || "";
  const API_KEY = script.getAttribute("data-api-key") || "";

  const STYLES = `
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
  `;

  let sessionId = null;
  let surveyEnded = false;

  function injectStyles() {
    const el = document.createElement("style");
    el.textContent = STYLES;
    document.head.appendChild(el);
  }

  function buildUI() {
    const btn = document.createElement("button");
    btn.id = "iq-widget-btn";
    btn.innerHTML = "💬";
    btn.setAttribute("aria-label", "Open survey");

    const popup = document.createElement("div");
    popup.id = "iq-widget-popup";
    popup.classList.add("iq-hidden");
    popup.innerHTML = `
      <div id="iq-widget-header">Survey</div>
      <div id="iq-widget-messages"></div>
      <div id="iq-widget-footer">
        <input id="iq-widget-input" type="text" placeholder="Type your answer…" />
        <button id="iq-widget-send">Send</button>
      </div>
    `;

    document.body.appendChild(btn);
    document.body.appendChild(popup);

    btn.addEventListener("click", () => {
      const hidden = popup.classList.toggle("iq-hidden");
      if (!hidden && !sessionId && !surveyEnded) startSurvey();
    });

    document.getElementById("iq-widget-send").addEventListener("click", sendAnswer);
    document.getElementById("iq-widget-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter") sendAnswer();
    });
  }

  function appendMessage(text, role) {
    const msgs = document.getElementById("iq-widget-messages");
    const div = document.createElement("div");
    div.className = `iq-msg iq-msg-${role}`;
    div.textContent = text;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function setLoading(loading) {
    const send = document.getElementById("iq-widget-send");
    const input = document.getElementById("iq-widget-input");
    send.disabled = loading;
    input.disabled = loading;
  }

  async function callSurvey(answer) {
    const body = { campaign_id: CAMPAIGN_ID, session_id: sessionId, answer: answer || null, user_id: "anonymous" };
    const res = await fetch(`${API_URL}/public/survey`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    return res.json();
  }

  async function startSurvey() {
    setLoading(true);
    try {
      const data = await callSurvey(null);
      sessionId = data.session_id;
      appendMessage(data.question, "bot");
      if (data.survey_ended) endSurvey();
    } catch (e) {
      appendMessage("Failed to start survey. Please try again.", "bot");
    } finally {
      setLoading(false);
    }
  }

  async function sendAnswer() {
    if (surveyEnded) return;
    const input = document.getElementById("iq-widget-input");
    const answer = input.value.trim();
    if (!answer) return;
    input.value = "";
    appendMessage(answer, "user");
    setLoading(true);
    try {
      const data = await callSurvey(answer);
      appendMessage(data.question, "bot");
      if (data.survey_ended) endSurvey();
    } catch (e) {
      appendMessage("Something went wrong. Please try again.", "bot");
    } finally {
      setLoading(false);
    }
  }

  function endSurvey() {
    surveyEnded = true;
    const footer = document.getElementById("iq-widget-footer");
    footer.innerHTML = "<p style='padding:10px;color:#6b7280;margin:0'>Thank you for completing the survey!</p>";
  }

  injectStyles();
  buildUI();
})();

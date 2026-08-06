/* ==========================================================================
   Three Rooms: The Walk — Buzz Executive Audio Huddle
   Dependency-free timeline engine. Media clock (audio element when present,
   else a setInterval-driven silent clock) drives everything else.
   Two skins (Desktop Huddle window / iPhone) share one data source: cues.json.
   ========================================================================== */

(function () {
  "use strict";

  /* ---- Fallback cue data (mirrors assets/cues.json) -----------------------
     fetch() of a local JSON file is blocked by some browsers under file://.
     We try fetch first (so editing cues.json alone updates the demo on any
     static host); if that fails, we fall back to this embedded copy so the
     demo still works when opened directly as a file. */
  var CUES_FALLBACK = [
    {"id":"n1","speaker":"NARRATOR","text":"Sunday, 9:40 p.m. Daniel Mercer has a board meeting Thursday. The board wants his AI strategy. His tenure may depend on it. His top officers cannot meet for three weeks. He needs their judgment tonight.","start":0.00,"dur":15.81},
    {"id":"buzz_activation","speaker":"BUZZ","text":"Executive Huddle live. Five role twins present. CFO. CTO. CRO. CMO. Chief Legal Officer. On-premise. Zero external calls. Audit trail active. Room One: Dream.","start":16.11,"dur":9.98},
    {"id":"ceo_dream_a","speaker":"CEO","text":"Morning. I know this is abrupt. My board packet locks tomorrow, and I am not walking in there with another vague AI strategy. Frankly, if I get this wrong, my job may be on the line.","start":26.39,"dur":11.67},
    {"id":"ceo_dream_b","speaker":"CEO","text":"I need the judgment of my best people now, not three weeks from now.","start":38.36,"dur":3.72},
    {"id":"ceo_dream_c","speaker":"CEO","text":"Here is the idea. We have twenty years of prior-authorization decisions. What if we cut authorization time from fourteen days to one, then sell that speed to every payer we serve?","start":42.38,"dur":12.41},
    {"id":"cro_dream","speaker":"CRO TWIN","text":"Your CRO's twin. Across five years of renewal calls and loss reviews, speed-to-decision is the top frustration in eight of our ten largest accounts. Commercially, this could become a nine-figure line over three years.","start":55.09,"dur":12.70},
    {"id":"cmo_dream","speaker":"CMO TWIN","text":"Your CMO's twin. This is not a feature story. It is a category story. Nobody in our market owns judgment-speed. If we move first, we define the market.","start":68.09,"dur":10.02},
    {"id":"ceo_good_kill","speaker":"CEO","text":"Good. Now kill it.","start":78.40,"dur":0.83},
    {"id":"ceo_hole","speaker":"CEO","text":"Biggest hole?","start":79.53,"dur":0.56},
    {"id":"legal_volley","speaker":"LEGAL TWIN","text":"Public cloud.","start":80.39,"dur":0.51},
    {"id":"cfo_volley","speaker":"CFO TWIN","text":"Budget.","start":80.94,"dur":0.21},
    {"id":"cto_volley","speaker":"CTO TWIN","text":"Scale.","start":81.39,"dur":0.33},
    {"id":"ceo_legalfirst","speaker":"CEO","text":"Legal first.","start":82.02,"dur":0.39},
    {"id":"legal_stress","speaker":"LEGAL TWIN","text":"Your Chief Legal Officer's twin. Patient data cannot touch a public cloud model. Material revenue disclosure becomes a securities issue. Four state regimes require named-human sign-off on every denial. Automation alone is not compliant.","start":82.71,"dur":16.55},
    {"id":"cfo_stress","speaker":"CFO TWIN","text":"Your CFO's twin. The board capped new-program spending at eleven million dollars. That vote passed seven to two in March. I preserved the dissent. Anything above the cap needs approval Thursday, not later.","start":99.56,"dur":12.14},
    {"id":"cto_stress_a","speaker":"CTO TWIN","text":"Your CTO's twin. Ninety-one percent of 12,400 historical decisions follow six policy gates. The remaining nine percent are where clinical judgment changed the outcome.","start":111.99,"dur":10.35},
    {"id":"cto_stress_b","speaker":"CTO TWIN","text":"One warning. I found no reliable precedent for peak-load throughput. Confidence is below governance threshold. I am declining to answer.","start":122.64,"dur":7.48},
    {"id":"cto_stress_c","speaker":"CTO TWIN","text":"Escalating to the Vice President of Clinical Operations. Estimated review time: thirty-eight minutes.","start":130.42,"dur":5.11},
    {"id":"ceo_stopus","speaker":"CEO","text":"So that could stop us.","start":137.53,"dur":0.89},
    {"id":"cto_architecture","speaker":"CTO TWIN","text":"It could. But it does not kill the strategy. It changes the architecture.","start":138.72,"dur":3.85},
    {"id":"buzz_blockers","speaker":"BUZZ","text":"Blocker register created. Five items. Each includes policy, precedent, owner, and required decision.","start":142.87,"dur":5.36},
    {"id":"ceo_buildit","speaker":"CEO","text":"Okay. Build it.","start":148.53,"dur":0.53},
    {"id":"legal_build","speaker":"LEGAL TWIN","text":"Private deployment removes the cloud gate. Route the nine percent to named clinicians. That is not a workaround. That is the compliant product.","start":149.37,"dur":8.61},
    {"id":"cfo_build","speaker":"CFO TWIN","text":"Phase one fits under the March cap at seven point four million dollars. Thursday becomes a governed launch plan, not a request for an undefined transformation budget.","start":158.28,"dur":8.91},
    {"id":"cto_build","speaker":"CTO TWIN","text":"Start with low-complexity authorizations. Keep inference and policy evaluation inside the enterprise. Escalate below-threshold cases automatically. Measure throughput for ninety days before expanding.","start":167.49,"dur":11.51},
    {"id":"cro_build","speaker":"CRO TWIN","text":"Do not sell automation. Sell faster, defensible decisions.","start":179.30,"dur":3.04},
    {"id":"cmo_build","speaker":"CMO TWIN","text":"And lead the board with risk reduction before efficiency.","start":182.64,"dur":2.51},
    {"id":"ceo_whyrisk","speaker":"CEO","text":"Why risk first?","start":185.45,"dur":0.45},
    {"id":"buzz_pattern_setup","speaker":"BUZZ","text":"New institutional pattern detected. In six years of board minutes, directors rejected every comparable initiative above eleven million dollars except cybersecurity. It passed because regulatory exposure was quantified before financial upside.","start":186.20,"dur":12.86},
    {"id":"ceo_sequence","speaker":"CEO","text":"So what is the sequence?","start":199.35,"dur":1.06},
    {"id":"buzz_pattern_reveal","speaker":"BUZZ","text":"Risk. Governance. Human control. Then revenue. Estimated board approval confidence increases from sixty-two to ninety-one percent.","start":200.71,"dur":7.27},
    {"id":"ceo_presentation","speaker":"CEO","text":"That is the presentation.","start":208.28,"dur":1.35},
    {"id":"buzz_package","speaker":"BUZZ","text":"Board package complete. Slide fourteen updated. Financial appendix regenerated. Legal citations attached. Dissent preserved. Three anticipated objections identified. Responses and speaking notes prepared. Consensus confidence: ninety-four percent.","start":211.44,"dur":16.45},
    {"id":"ceo_breathe","speaker":"CEO","text":"I can actually breathe again. Thank you.","start":228.18,"dur":1.75},
    {"id":"buzz_ended","speaker":"BUZZ","text":"Executive Huddle ended. Duration: eight minutes, forty-two seconds. Equivalent scheduling delay avoided: nineteen days.","start":230.23,"dur":6.91},
    {"id":"end1","speaker":"","text":"Search finds documents.","start":237.14,"dur":1.30},
    {"id":"end2","speaker":"","text":"Digital twins preserve people.","start":238.44,"dur":1.30},
    {"id":"end3","speaker":"","text":"WisdomTwin preserves decisions.","start":239.74,"dur":1.50},
    {"id":"end4","speaker":"","text":"WISDOMTWIN.AI — The Institutional Judgment Layer","start":241.24,"dur":1.50},
    {"id":"end5","speaker":"","text":"On-premise. Air-gapped. Human-governed.","start":242.74,"dur":1.20},
    {"id":"end6","speaker":"","text":"All organizations, people, records, policies, financial figures, and operating data depicted are synthetic.","start":243.94,"dur":2.40}
  ];

  /* ---- Participants (huddle roster) --------------------------------------- */
  var PARTICIPANTS = [
    { role: "ceo",   label: "DM",  name: "Daniel Mercer", color: "#4a5568" },
    { role: "cfo",   label: "CFO", name: "CFO Twin",       color: "#2f8f7a" },
    { role: "cto",   label: "CTO", name: "CTO Twin",       color: "#3b6fa0" },
    { role: "cro",   label: "CRO", name: "CRO Twin",       color: "#c07a3a" },
    { role: "cmo",   label: "CMO", name: "CMO Twin",       color: "#8a5fb0" },
    { role: "legal", label: "LGL", name: "Legal Twin",     color: "#a04a55" }
  ];
  var PARTICIPANTS_BY_ROLE = {};
  PARTICIPANTS.forEach(function (p) { PARTICIPANTS_BY_ROLE[p.role] = p; });

  var SPEAKER_ROLE = {
    "CEO": "ceo", "CFO TWIN": "cfo", "CTO TWIN": "cto", "CRO TWIN": "cro", "CMO TWIN": "cmo", "LEGAL TWIN": "legal"
  };

  /* ---- DOM refs ------------------------------------------------------- */
  var $ = function (sel) { return document.querySelector(sel); };
  var $all = function (sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); };

  var audioEl = $("#audioEl");
  var dimOverlay = $("#dimOverlay");
  var endCard = $("#endCard");
  var endcardDisclosure = $("#endcardDisclosure");
  var replayBtn = $("#replayBtn");
  var stageSide = $("#stageSide");
  var mobilePanelSlot = $("#mobilePanelSlot");

  var playPauseBtn = $("#playPauseBtn");
  var restartBtn = $("#restartBtn");
  var seekBar = $("#seekBar");
  var timeLabel = $("#timeLabel");
  var muteBtn = $("#muteBtn");
  var captionsBtn = $("#captionsBtn");
  var pendingChip = $("#pendingChip");

  var transcriptBtn = $("#transcriptBtn");
  var drawer = $("#drawer");
  var drawerBackdrop = $("#drawerBackdrop");
  var drawerClose = $("#drawerClose");
  var drawerTitle = $("#drawerTitle");
  var drawerBody = $("#drawerBody");

  var transcriptEls = $all("[data-transcript]");
  var roomChipEls = $all("[data-room-chip]");
  var participantMountEls = $all("[data-participants]");
  var startBtns = $all("[data-start]");

  /* ---- Participant strip (built once, into both skins) -------------------- */
  function esc(s) { return String(s).replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }

  function participantsHTML() {
    return PARTICIPANTS.map(function (p) {
      return (
        '<div class="p-item" data-role="' + p.role + '">' +
        '<div class="p-avatar" style="background:' + p.color + '">' + esc(p.label) + "</div>" +
        '<div class="p-name">' + esc(p.role === "ceo" ? "Daniel" : p.name.replace(" Twin", "")) + "</div>" +
        "</div>"
      );
    }).join("");
  }
  participantMountEls.forEach(function (el) { el.innerHTML = participantsHTML(); });

  var pItemsByRole = {}; // role -> [el, el]
  PARTICIPANTS.forEach(function (p) { pItemsByRole[p.role] = $all('[data-role="' + p.role + '"].p-item'); });

  /* ---- State ------------------------------------------------------------ */
  var cues = CUES_FALLBACK.slice().sort(function (a, b) { return a.start - b.start; });
  var totalDuration = 0;
  var usingAudio = true;
  var started = false;
  var captionsOn = true; // toggles transcript message-text visibility
  var appendedIds = {}; // cue id -> true, once its transcript row has been rendered
  var isScrubbing = false;
  var summaryAppended = false;

  var silentClock = { t: 0, playing: false, lastTs: null };

  function estimatedTotal() {
    var last = cues[cues.length - 1];
    return last.start + last.dur;
  }
  totalDuration = estimatedTotal();

  function fmtTime(s) {
    if (!isFinite(s) || s < 0) s = 0;
    var m = Math.floor(s / 60);
    var sec = Math.floor(s % 60);
    return m + ":" + (sec < 10 ? "0" : "") + sec;
  }

  function getTime() { return usingAudio ? (audioEl.currentTime || 0) : silentClock.t; }
  function getDuration() {
    if (usingAudio && isFinite(audioEl.duration) && audioEl.duration > 0) return audioEl.duration;
    return totalDuration;
  }
  function isPlaying() { return usingAudio ? (!audioEl.paused && !audioEl.ended) : silentClock.playing; }

  /* ---- Audio / silent-clock wiring --------------------------------------- */
  function setupAudio() {
    var testSrc = audioEl.currentSrc || (audioEl.querySelector("source") || {}).src;
    if (!testSrc) { fallbackToSilent(); return; }
    var settled = false;
    function onReady() {
      if (settled) return;
      settled = true;
      usingAudio = true;
      if (isFinite(audioEl.duration) && audioEl.duration > 0) totalDuration = audioEl.duration;
      pendingChip.classList.remove("show");
    }
    function onError() { if (settled) return; settled = true; fallbackToSilent(); }
    audioEl.addEventListener("loadedmetadata", onReady);
    audioEl.addEventListener("canplaythrough", onReady, { once: true });
    audioEl.addEventListener("error", onError, true);
    // preload="auto" can finish loading (and fire its events) before this script
    // attaches listeners — e.g. while boot() is awaiting the cues.json fetch.
    // If metadata is already available, don't wait for an event that already happened.
    if (audioEl.readyState >= 1 /* HAVE_METADATA */) onReady();
    window.setTimeout(function () { if (!settled) onError(); }, 4000);
  }
  function fallbackToSilent() { usingAudio = false; pendingChip.classList.add("show"); }

  function play() {
    if (usingAudio) {
      var p = audioEl.play();
      if (p && p.catch) p.catch(function () { fallbackToSilent(); startSilentClock(); });
    } else {
      startSilentClock();
    }
    setPlayIcon(true);
  }
  function pause() { if (usingAudio) audioEl.pause(); silentClock.playing = false; setPlayIcon(false); }
  function togglePlay() { if (isPlaying()) pause(); else play(); }

  function seekTo(t) {
    t = Math.max(0, Math.min(getDuration(), t));
    if (usingAudio) audioEl.currentTime = t; else silentClock.t = t;
    render(t);
  }

  function startSilentClock() {
    silentClock.playing = true;
    silentClock.lastTs = null;
    requestAnimationFrame(silentTick);
  }
  function silentTick(ts) {
    if (!silentClock.playing) return;
    if (silentClock.lastTs != null) silentClock.t += (ts - silentClock.lastTs) / 1000;
    silentClock.lastTs = ts;
    if (silentClock.t >= totalDuration) { silentClock.t = totalDuration; silentClock.playing = false; setPlayIcon(false); return; }
    requestAnimationFrame(silentTick);
  }

  function setPlayIcon(playing) {
    playPauseBtn.textContent = playing ? "❚❚" : "▶";
    playPauseBtn.setAttribute("aria-label", playing ? "Pause" : "Play");
  }

  /* ---- Start lifecycle ---------------------------------------------------- */
  function beginHuddle() {
    if (started) return;
    started = true;
    transcriptEls.forEach(function (el) {
      var empty = el.querySelector(".dw-empty");
      if (empty) empty.remove();
    });
    play();
  }
  startBtns.forEach(function (b) { b.addEventListener("click", beginHuddle); });

  function cueById(id) { for (var i = 0; i < cues.length; i++) if (cues[i].id === id) return cues[i]; return null; }
  var buzzEndedStart = cueById("buzz_ended").start;
  var buzzEndedFinish = buzzEndedStart + cueById("buzz_ended").dur;
  var end1Start = cueById("end1").start;

  /* ---- Room chip ------------------------------------------------------------ */
  var ROOM_BOUNDS = [
    { room: "", from: 0, to: 26.39 },
    { room: "DREAM", from: 26.39, to: 79.53 },
    { room: "STRESS-TEST", from: 79.53, to: 148.53 },
    { room: "BUILD", from: 148.53, to: Infinity }
  ];
  function updateRoomChip(t) {
    var room = "";
    if (started) {
      for (var i = 0; i < ROOM_BOUNDS.length; i++) {
        if (t >= ROOM_BOUNDS[i].from && t < ROOM_BOUNDS[i].to) { room = ROOM_BOUNDS[i].room; break; }
      }
    }
    roomChipEls.forEach(function (el) { el.textContent = room || " "; });
  }

  /* ---- Speaking indicator on participant avatars --------------------------- */
  function updateSpeaking(cue) {
    var activeRole = cue ? SPEAKER_ROLE[cue.speaker] : null;
    Object.keys(pItemsByRole).forEach(function (role) {
      var on = started && role === activeRole;
      pItemsByRole[role].forEach(function (el) { el.classList.toggle("speaking", on); });
    });
  }

  /* ---- Transcript rendering -------------------------------------------------- */
  function speakerMeta(cue) {
    if (cue.speaker === "NARRATOR") return { type: "narr" };
    if (cue.speaker === "BUZZ") return { type: "sys", label: "Buzz", avatar: "🐝", color: "#8a7f60" };
    var role = SPEAKER_ROLE[cue.speaker];
    var p = PARTICIPANTS_BY_ROLE[role];
    if (p) return { type: "chat", label: p.name, avatar: p.label, color: p.color };
    return { type: "chat", label: cue.speaker || "Unknown", avatar: "?", color: "#666" };
  }

  function transcriptRowHTML(cue) {
    var meta = speakerMeta(cue);
    var t = fmtTime(cue.start);
    if (meta.type === "narr") {
      return '<div class="tr-narr">' + esc(cue.text) + "</div>";
    }
    var cls = meta.type === "sys" ? "tr-row sys" : "tr-row";
    return (
      '<div class="' + cls + '">' +
      '<div class="tr-avatar" style="background:' + meta.color + '">' + meta.avatar + "</div>" +
      '<div class="tr-body"><div class="tr-name">' + esc(meta.label) + '<span class="tr-time">' + t + "</span></div>" +
      '<div class="tr-text">' + esc(cue.text) + "</div></div>" +
      "</div>"
    );
  }

  function appendTranscript(html) {
    transcriptEls.forEach(function (el) {
      el.insertAdjacentHTML("beforeend", html);
      el.scrollTop = el.scrollHeight;
    });
  }

  // Idempotent: appends every cue whose start has been reached and that has not
  // already been rendered. Backfills any cues skipped by a forward seek, and is
  // safe to call many times per second (e.g. while the seek bar fires 'input'
  // repeatedly) without ever producing a duplicate row.
  function syncTranscript(t) {
    if (!started) return;
    for (var i = 0; i < cues.length; i++) {
      var c = cues[i];
      if (c.start > t) break;
      if (appendedIds[c.id]) continue;
      appendedIds[c.id] = true;
      if (c.speaker) appendTranscript(transcriptRowHTML(c));
    }
  }

  function clearTranscript(showEmpty) {
    appendedIds = {};
    transcriptEls.forEach(function (el) {
      el.innerHTML = showEmpty
        ? '<div class="dw-empty"><button type="button" class="start-pill" data-start>Start Executive Huddle</button><p>Private enterprise environment</p></div>'
        : "";
    });
    if (showEmpty) {
      startBtns = $all("[data-start]");
      startBtns.forEach(function (b) { b.addEventListener("click", beginHuddle); });
    }
  }

  function summaryCardHTML() {
    function row(k, v) { return '<div class="tr-card-row"><span class="k">' + esc(k) + '</span><span class="v">' + esc(v) + "</span></div>"; }
    return (
      '<div class="tr-card"><div class="tr-card-title">Huddle complete</div><div class="tr-card-rows">' +
      row("Duration", "8:42") + row("Blockers resolved", "4 of 5") + row("Human escalation created", "1") +
      row("Board memo", "Ready") + row("Citations", "Attached") + row("Dissent", "Preserved") + row("Audit record", "Complete") +
      "</div></div>"
    );
  }

  function maybeAppendSummary(t) {
    if (summaryAppended || !started) return;
    if (t >= buzzEndedFinish) { summaryAppended = true; appendTranscript(summaryCardHTML()); }
  }

  captionsBtn.addEventListener("click", function () {
    captionsOn = !captionsOn;
    document.body.classList.toggle("transcript-compact", !captionsOn);
    captionsBtn.setAttribute("aria-pressed", String(captionsOn));
  });

  /* ---- Evidence / blocker / consensus / board-pattern panels -------------- */
  function rowsHtml(rows) {
    return rows.map(function (r) {
      return '<div class="panel-row"><span class="k">' + esc(r[0]) + '</span><span class="v">' + esc(r[1]) + "</span></div>";
    }).join("");
  }

  var PANEL_DEFS = {
    evidence_cro: {
      from: 55.09, to: 68.09,
      cls: "", kicker: "EVIDENCE &middot; CRO TWIN", title: "Renewal-call analysis",
      rows: [["Renewal calls reviewed", "1,842"], ["Account plans", "327"], ["Loss reviews", "94"], ["Period", "5 years"]],
      foot: "Speed-to-decision is the top frustration in 8 of our 10 largest accounts."
    },
    evidence_legal: {
      from: 82.71, to: 99.56,
      cls: "", kicker: "EVIDENCE &middot; LEGAL TWIN", title: "Three governance gates",
      rows: [["Public-cloud PHI processing", "Prohibited"], ["Material revenue disclosure", "Securities issue"], ["Sign-off on denials", "Required, 4 states"]],
      foot: "Automation alone is not compliant. Governance memos and rejection rationale on file."
    },
    evidence_cfo: {
      from: 99.56, to: 111.99,
      cls: "", kicker: "EVIDENCE &middot; CFO TWIN", title: "Board spending authority",
      rows: [["New-program cap", "$11,000,000"], ["Board vote", "7–2, March"], ["Dissent preserved", "Yes"]],
      foot: "Anything above the cap needs approval Thursday — not later."
    },
    evidence_cto: {
      from: 111.99, to: 122.64,
      cls: "", kicker: "EVIDENCE &middot; CTO TWIN", title: "Historical decision analysis",
      rows: [["Decisions reviewed", "12,400"], ["Aligned to 6 policy gates", "91%"], ["Required clinical judgment", "9%"]],
      foot: "The 9% is exactly where clinical judgment changed the outcome."
    },
    safe_decline: {
      from: 122.64, to: 138.72,
      cls: "safe-decline", kicker: "SAFE DECLINE &middot; CTO TWIN", title: "Confidence below governance threshold",
      rows: [["Precedent found", "None — peak-load throughput"], ["Answer", "Withheld"], ["Escalated to", "VP, Clinical Operations"], ["Est. review time", "38 minutes"]],
      foot: "The system does not guess. It declines, and names a human."
    },
    blockers_panel: {
      from: 142.87, to: 149.37,
      cls: "", kicker: "BLOCKER REGISTER", title: "5 items",
      rows: [
        ["1. Public-cloud PHI gate", "Legal — approve private deployment"],
        ["2. Spending cap $11M", "CFO — confirm phase-one budget"],
        ["3. Peak-load precedent", "VP Clin. Ops — escalation review"],
        ["4. Disclosure timing", "Legal — align with board vote"],
        ["5. 4-state sign-off", "Legal/CTO — route 9% to clinicians"]
      ],
      foot: "Each item includes policy, precedent, owner, and required decision."
    },
    board_pattern: {
      from: 186.20, to: 208.28,
      cls: "climax", kicker: "BOARD-PATTERN DISCOVERY", title: "A six-year pattern",
      rows: [["Initiatives above $11M", "Rejected"], ["Exception", "Cybersecurity"], ["Why it passed", "Risk quantified before upside"], ["Sequence", "Risk → Governance → Human control → Revenue"]],
      foot: "Estimated board approval confidence: 62% → 91%."
    }
  };

  var CONSENSUS_WINDOW = { from: 211.44, to: 230.23 };

  var lastPanelKey = undefined;
  function currentPanelKey(t) {
    if (!started) return null;
    var keys = Object.keys(PANEL_DEFS);
    for (var i = 0; i < keys.length; i++) {
      var d = PANEL_DEFS[keys[i]];
      if (t >= d.from && t < d.to) return keys[i];
    }
    if (t >= CONSENSUS_WINDOW.from && t < CONSENSUS_WINDOW.to) return "consensus_panel";
    return null;
  }

  function consensusValue(t) {
    var revealFrom = 200.71, revealTo = 207.98;
    var pkgFrom = 211.44, pkgTo = 224.0;
    if (t < revealFrom) return 62;
    if (t < revealTo) { var p = (t - revealFrom) / (revealTo - revealFrom); return Math.round(62 + p * (91 - 62)); }
    if (t < pkgFrom) return 91;
    if (t < pkgTo) { var p2 = (t - pkgFrom) / (pkgTo - pkgFrom); return Math.round(91 + p2 * (94 - 91)); }
    return 94;
  }

  function panelHtml(key, t) {
    if (key === "consensus_panel") {
      var v = consensusValue(t);
      return (
        '<div class="panel-card consensus in">' +
        '<div class="panel-kicker">CONSENSUS CONFIDENCE</div>' +
        '<div class="bar-value">' + v + '<span class="pct">%</span></div>' +
        '<div class="bar-track"><div class="bar-fill" style="width:' + v + '%"></div></div>' +
        '<div class="panel-foot">Based on available precedent and policy.</div>' +
        "</div>"
      );
    }
    var d = PANEL_DEFS[key];
    if (!d) return "";
    return (
      '<div class="panel-card ' + d.cls + ' in">' +
      '<div class="panel-kicker">' + d.kicker + "</div>" +
      '<div class="panel-title">' + esc(d.title) + "</div>" +
      '<div class="panel-rows">' + rowsHtml(d.rows) + "</div>" +
      '<div class="panel-foot">' + esc(d.foot) + "</div>" +
      "</div>"
    );
  }

  function updatePanels(t) {
    var key = currentPanelKey(t);
    if (key === lastPanelKey) {
      if (key === "consensus_panel") {
        var html = panelHtml(key, t);
        stageSide.innerHTML = html;
        mobilePanelSlot.innerHTML = html;
      }
      return;
    }
    lastPanelKey = key;
    if (!key) { stageSide.innerHTML = ""; mobilePanelSlot.innerHTML = ""; return; }
    var html2 = panelHtml(key, t);
    stageSide.innerHTML = html2;
    mobilePanelSlot.innerHTML = html2;
  }
  function resetPanels() { lastPanelKey = undefined; stageSide.innerHTML = ""; mobilePanelSlot.innerHTML = ""; }

  /* ---- Dim overlay for the protected safe-decline silence ------------------ */
  var DIM_WINDOW = { from: 135.53, to: 137.53 };
  function updateDim(t) { dimOverlay.classList.toggle("on", started && t >= DIM_WINDOW.from && t < DIM_WINDOW.to); }

  /* ---- End card --------------------------------------------------------------
     The audio clock cannot advance past its own duration, so once the huddle's
     closing line finishes there is no more media time left to stage the end
     card's reveals against. Instead, after a short breathing gap post-huddle,
     the end card runs on its own timer sequence — generously paced for reading,
     independent of the (now-exhausted) media clock. */
  var END_IDS = ["end1", "end2", "end3", "end4", "end5"];
  var END_TRIGGER_GAP = 3.0; // seconds after Buzz's closing line before the end card begins
  var endCardStarted = false;
  var endCardTimers = [];

  function clearEndCardTimers() { endCardTimers.forEach(function (id) { window.clearTimeout(id); }); endCardTimers = []; }

  function resetEndCard() {
    clearEndCardTimers();
    endCardStarted = false;
    endCard.classList.remove("on");
    endCard.setAttribute("aria-hidden", "true");
    document.querySelectorAll(".endcard-line, .endcard-lockup").forEach(function (el) { el.classList.remove("show"); });
    endcardDisclosure.classList.remove("show");
    replayBtn.classList.remove("show");
  }

  function scheduleEndCard() {
    if (endCardStarted) return;
    endCardStarted = true;
    endCard.classList.add("on");
    endCard.setAttribute("aria-hidden", "false");
    var STEP = 2200; // ms between each end-card line
    var t = 0;
    END_IDS.forEach(function (id) {
      endCardTimers.push(window.setTimeout(function () {
        var el = document.querySelector('[data-card="' + id + '"]');
        if (el) el.classList.add("show");
      }, t));
      t += STEP;
    });
    endCardTimers.push(window.setTimeout(function () { endcardDisclosure.classList.add("show"); }, t + 500));
    endCardTimers.push(window.setTimeout(function () { replayBtn.classList.add("show"); }, t + 1400));
  }

  function updateEndCard(t) {
    var triggerAt = buzzEndedFinish + END_TRIGGER_GAP;
    if (t < triggerAt) { if (endCardStarted) resetEndCard(); return; }
    scheduleEndCard();
  }

  replayBtn.addEventListener("click", function () {
    started = false;
    summaryAppended = false;
    resetPanels();
    resetEndCard();
    clearTranscript(true);
    seekTo(0);
    pause();
  });

  /* ---- Main render loop -------------------------------------------------- */
  function render(t) {
    var cue = findActiveCue(t);
    syncTranscript(t);
    updateSpeaking(started ? cue : null);
    updateRoomChip(t);
    updatePanels(t);
    updateDim(t);
    updateEndCard(t);
    maybeAppendSummary(t);
    updateTransport(t);
  }

  function findActiveCue(t) {
    var active = null;
    for (var i = 0; i < cues.length; i++) {
      var c = cues[i];
      if (t >= c.start && t < c.start + c.dur) { active = c; break; }
      if (t < c.start) break;
    }
    return active;
  }

  function updateTransport(t) {
    var dur = getDuration();
    if (!isScrubbing) {
      var pct = dur > 0 ? (t / dur) * 1000 : 0;
      seekBar.value = String(pct);
      seekBar.style.setProperty("--progress", (dur > 0 ? (t / dur) * 100 : 0) + "%");
    }
    timeLabel.textContent = fmtTime(t) + " / " + fmtTime(dur);
    setPlayIcon(isPlaying());
  }

  function loop() { render(getTime()); requestAnimationFrame(loop); }

  /* ---- Transport controls -------------------------------------------------- */
  playPauseBtn.addEventListener("click", function () { if (!started) { beginHuddle(); return; } togglePlay(); });
  restartBtn.addEventListener("click", function () {
    if (!started) { beginHuddle(); return; }
    clearTranscript(false);
    summaryAppended = false;
    seekTo(0);
  });

  function setMuted(m) {
    audioEl.muted = m;
    muteBtn.setAttribute("aria-pressed", String(m));
    muteBtn.textContent = m ? "🔇" : "🔊";
    $all('[data-action="mute"]').forEach(function (b) { b.setAttribute("aria-pressed", String(m)); });
  }
  muteBtn.addEventListener("click", function () { setMuted(!audioEl.muted); });

  seekBar.addEventListener("mousedown", function () { isScrubbing = true; });
  seekBar.addEventListener("touchstart", function () { isScrubbing = true; }, { passive: true });
  seekBar.addEventListener("input", function () {
    if (!started) beginHuddle();
    var dur = getDuration();
    var t = (parseFloat(seekBar.value) / 1000) * dur;
    seekBar.style.setProperty("--progress", (dur > 0 ? (t / dur) * 100 : 0) + "%");
    seekTo(t);
  });
  function endScrub() { isScrubbing = false; }
  seekBar.addEventListener("mouseup", endScrub);
  seekBar.addEventListener("touchend", endScrub);
  seekBar.addEventListener("change", endScrub);

  document.addEventListener("keydown", function (e) {
    var tag = (e.target && e.target.tagName) || "";
    if (tag === "INPUT" && e.target !== seekBar) return;
    if (drawer && !drawer.hidden && e.key === "Escape") { closeDrawer(); return; }
    switch (e.key) {
      case " ":
        e.preventDefault();
        if (!started) beginHuddle(); else togglePlay();
        break;
      case "r": case "R":
        if (!started) { beginHuddle(); break; }
        clearTranscript(false);
        summaryAppended = false;
        seekTo(0);
        break;
      case "m": case "M":
        setMuted(!audioEl.muted);
        break;
      case "c": case "C":
        captionsBtn.click();
        break;
      default: break;
    }
  });

  /* ---- Reduced motion ------------------------------------------------------- */
  var mql = window.matchMedia("(prefers-reduced-motion: reduce)");
  function applyMotionPref() { document.body.classList.toggle("reduced-motion", mql.matches); }
  applyMotionPref();
  if (mql.addEventListener) mql.addEventListener("change", applyMotionPref);

  /* ---- Desktop / iPhone surface toggle -------------------------------------- */
  var toggleDesktop = $("#toggleDesktop");
  var toggleIphone = $("#toggleIphone");
  function setSurface(name) {
    document.body.classList.toggle("force-desktop", name === "desktop");
    document.body.classList.toggle("force-iphone", name === "iphone");
    toggleDesktop.setAttribute("aria-pressed", String(name === "desktop"));
    toggleIphone.setAttribute("aria-pressed", String(name === "iphone"));
  }
  toggleDesktop.addEventListener("click", function () { setSurface("desktop"); });
  toggleIphone.addEventListener("click", function () { setSurface("iphone"); });
  setSurface(window.matchMedia("(max-width:860px)").matches ? "iphone" : "desktop");

  /* ---- Manual drawers (Evidence / Blockers / Escalations / Transcript) ------ */
  var TRANSCRIPT_ROWS = cues.filter(function (c) { return c.speaker; }).map(function (c) {
    return '<div class="tr-line"><span class="who">' + esc(c.speaker) + '</span><span class="what">' + esc(c.text) + "</span></div>";
  }).join("");

  var EVIDENCE_ALL = ["evidence_cro", "evidence_legal", "evidence_cfo", "evidence_cto"].map(function (k) {
    return panelHtml(k, 0).replace(' in"', '"');
  }).join("");
  var BLOCKERS_ALL = panelHtml("blockers_panel", 0).replace(' in"', '"');
  var ESCALATIONS_ALL = panelHtml("safe_decline", 0).replace(' in"', '"');

  var lastFocused = null;
  function openDrawer(title, html) {
    drawerTitle.textContent = title;
    drawerBody.innerHTML = html || '<p class="drawer-empty">Nothing here yet.</p>';
    drawer.hidden = false;
    drawerBackdrop.hidden = false;
    requestAnimationFrame(function () { drawer.classList.add("on"); drawerBackdrop.classList.add("on"); });
    lastFocused = document.activeElement;
    drawerClose.focus();
  }
  function closeDrawer() {
    drawer.classList.remove("on");
    drawerBackdrop.classList.remove("on");
    window.setTimeout(function () { drawer.hidden = true; drawerBackdrop.hidden = true; }, 320);
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  }
  drawerClose.addEventListener("click", closeDrawer);
  drawerBackdrop.addEventListener("click", closeDrawer);
  transcriptBtn.addEventListener("click", function () { openDrawer("Full transcript", TRANSCRIPT_ROWS); });

  $all('[data-action]').forEach(function (btn) {
    btn.addEventListener("click", function () {
      var action = btn.getAttribute("data-action");
      if (action === "mute") { setMuted(!audioEl.muted); return; }
      if (action === "end") { pause(); seekTo(buzzEndedStart); return; }
      if (action === "evidence") openDrawer("Evidence reviewed this huddle", EVIDENCE_ALL);
      if (action === "blockers") openDrawer("Blocker register", BLOCKERS_ALL);
      if (action === "escalations") openDrawer("Escalations", ESCALATIONS_ALL);
    });
  });

  /* ---- Boot ------------------------------------------------------------------ */
  function boot(loadedCues) {
    if (loadedCues && loadedCues.length) {
      cues = loadedCues.slice().sort(function (a, b) { return a.start - b.start; });
      totalDuration = estimatedTotal();
    }
    buzzEndedStart = cueById("buzz_ended").start;
    buzzEndedFinish = buzzEndedStart + cueById("buzz_ended").dur;
    end1Start = cueById("end1").start;
    setupAudio();
    updateTransport(0);
    render(0);
    requestAnimationFrame(loop);
  }

  fetch("assets/cues.json")
    .then(function (r) { if (!r.ok) throw new Error("cues.json not ok"); return r.json(); })
    .then(function (json) { boot(json); })
    .catch(function () { boot(null); });
})();

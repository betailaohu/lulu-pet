/* 水豚噜噜 · 网页版
 * 表现配置来自 assets/manifest.json，数值配置来自 assets/state.json，
 * 与 Android / iOS 共用同一份共享层定义（改 shared/ 后跑 sync_assets.py 即可）。
 * 存档走 WorkBuddy 云数据库 pet_state，按登录账号隔离。
 */
(function () {
  'use strict';

  var PUBLIC_CONFIG = {
    endpoint: 'https://wbapp-gbyys9j25fx0srxlke1txs.app.workbuddy.host',
    publishableKey: 'wbpk_gbYYS9J25Fx0srxlke1tXS_xrORdlPmzZoqbsxgzdTtvKuPMLXuvZwG',
    oauthRelayBaseUrl: 'https://www.workbuddy.cn/v2/as/genie-baas/oauth'
  };

  var $ = function (s) { return document.querySelector(s); };
  var pet = $('#pet');
  var petWrap = $('#petWrap');
  var stage = $('#stage');
  var bubble = $('#bubble');
  var effects = $('#effects');
  var toastEl = $('#toast');

  var cloud = null;
  var session = null;
  var rowId = null;
  var syncing = false;
  var saveTimer = null;

  var MANIFEST = null;
  var CFG = null;

  var S = {
    satiety: 70, mood: 75, affinity: 10,
    lastTickAt: Date.now(), affinityDay: '', affinityGainToday: 0
  };

  var opts = { freeWalk: true, spicy: true, intensity: 1 };

  /* ---------------- 工具 ---------------- */

  function toast(text, ms) {
    toastEl.textContent = text;
    toastEl.classList.add('show');
    clearTimeout(toastEl._t);
    toastEl._t = setTimeout(function () { toastEl.classList.remove('show'); }, ms || 2200);
  }

  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }
  function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }
  function dayKey(d) {
    d = d || new Date();
    return '' + d.getFullYear() + String(d.getMonth() + 1).padStart(2, '0') + String(d.getDate()).padStart(2, '0');
  }
  function stripHints(text) {
    return String(text || '').replace(/[（(][^）)]*[）)]/g, '').replace(/\s{2,}/g, ' ').trim();
  }

  /* ---------------- 数值（对应 PetState.kt） ---------------- */

  function statCfg(key) { return CFG.stats[key]; }

  function decay() {
    var now = Date.now();
    var hours = Math.max(0, (now - S.lastTickAt) / 3600000);
    if (hours <= 0) return;
    S.satiety = clamp(S.satiety - statCfg('satiety').decayPerHour * hours, 0, statCfg('satiety').max);
    S.mood = clamp(S.mood - statCfg('mood').decayPerHour * hours, 0, statCfg('mood').max);
    S.lastTickAt = now;
  }

  function addAffinity(gain) {
    var day = dayKey();
    if (S.affinityDay !== day) { S.affinityDay = day; S.affinityGainToday = 0; }
    var cap = statCfg('affinity').maxGainPerDay;
    var allowed = Math.min(gain, Math.max(0, cap - S.affinityGainToday));
    S.affinityGainToday += allowed;
    S.affinity = clamp(S.affinity + allowed, 0, statCfg('affinity').max);
  }

  function onPatStat() {
    decay();
    S.mood = clamp(S.mood + 2, 0, statCfg('mood').max);
    addAffinity(statCfg('affinity').gainPerPat);
    changed();
  }

  function onFeedStat() {
    decay();
    S.satiety = clamp(S.satiety + 20, 0, statCfg('satiety').max);
    S.mood = clamp(S.mood + 3, 0, statCfg('mood').max);
    addAffinity(statCfg('affinity').gainPerFeed);
    changed();
  }

  function urgentBehavior() {
    decay();
    var sa = statCfg('satiety'), mo = statCfg('mood');
    if (S.satiety < sa.lowThreshold) return sa.lowBehavior;
    if (S.mood < mo.lowThreshold) return mo.lowBehavior;
    return null;
  }

  function statusText(isSleep) {
    decay();
    var list = CFG.statusText.map(function (x) { return x.text; });
    var sa = statCfg('satiety'), mo = statCfg('mood');
    var idx = S.satiety < sa.lowThreshold ? 0
      : isSleep ? 1
      : S.mood < mo.lowThreshold ? 2
      : S.mood >= 70 ? 3 : 4;
    return list[idx] || list[list.length - 1];
  }

  function renderStats() {
    decay();
    [['satiety', S.satiety], ['mood', S.mood], ['affinity', S.affinity]].forEach(function (pair) {
      var el = document.querySelector('.bar[data-stat="' + pair[0] + '"]');
      if (!el) return;
      var max = statCfg(pair[0]).max;
      el.querySelector('i').style.width = Math.round(clamp(pair[1] / max, 0, 1) * 100) + '%';
      el.querySelector('span').textContent = Math.round(pair[1]);
    });
  }

  /* ---------------- 时段（对应 BodyClock.kt） ---------------- */

  function phase() {
    var h = new Date().getHours();
    var list = CFG.bodyClock;
    for (var i = 0; i < list.length; i++) {
      if (h >= list[i].from && h < list[i].to) return list[i];
    }
    return list[0];
  }

  function isSleepPhase() { return phase().id === 'sleep'; }

  /* ---------------- 帧与姿势 ---------------- */

  function alias(name) {
    var a = MANIFEST.frameAliases || {};
    return a[name] || name;
  }

  function frameUrl(id) { return 'assets/frames/frame-' + id + '.png'; }

  function restingFrame() {
    var map = MANIFEST.restingFrame || {};
    return (isSleepPhase() && map.sleep) ? map.sleep : (map.default || 'neutral');
  }

  function poseScaleOf(frameId) {
    var ps = MANIFEST.poseScale || {};
    var groups = ps.groups || [];
    for (var i = 0; i < groups.length; i++) {
      if (groups[i].ids.indexOf(frameId) >= 0) return groups[i].value;
    }
    return ps['default'] == null ? 1 : ps['default'];
  }

  var wrapX = 0;
  var wrapScale = 1;

  function applyWrap() {
    petWrap.style.transform = 'translate3d(' + wrapX.toFixed(1) + 'px,0,0) scale(' + wrapScale + ')';
  }

  var currentFrame = 'neutral';

  function setFrame(name) {
    var resolved = alias(name);
    currentFrame = resolved;
    var src = frameUrl(resolved);
    if (pet.getAttribute('src') !== src) pet.setAttribute('src', src);
    wrapScale = poseScaleOf(resolved);
    applyWrap();
  }

  /* ---------------- 动画（对应 playSequence / startShakeLoop 等） ---------------- */

  var anims = [];
  var breatheAnim = null;

  function stopAnims() {
    anims.forEach(function (a) { try { a.cancel(); } catch (e) {} });
    anims = [];
    pet.style.transform = '';
  }

  function stopBreathing() {
    if (breatheAnim) { try { breatheAnim.cancel(); } catch (e) {} breatheAnim = null; }
  }

  function startBreathing() {
    stopBreathing();
    var s = isSleepPhase() ? 0.88 : 1;
    breatheAnim = pet.animate([
      { transform: 'translateY(0) scale(' + (s) + ')' },
      { transform: 'translateY(-3px) scale(' + (s * 1.008) + ')' },
      { transform: 'translateY(0) scale(' + (s) + ')' }
    ], { duration: 3600, iterations: Infinity, easing: 'ease-in-out' });
  }

  function playSeq(targets) {
    stopAnims();
    stopBreathing();
    var total = targets.reduce(function (a, t) { return a + t.ms; }, 0);
    var kf = [{ transform: 'translate3d(0,0,0) rotate(0deg) scale(1)' }];
    var acc = 0;
    targets.forEach(function (t) {
      acc += t.ms;
      kf.push({
        transform: 'translate3d(' + (t.x || 0) + 'px,' + (t.y || 0) + 'px,0) rotate(' + (t.rot || 0) + 'deg) scale(' + (t.s || 1) + ')',
        offset: Math.min(1, acc / total)
      });
    });
    var a = pet.animate(kf, { duration: total, easing: 'ease-in-out', fill: 'none' });
    anims.push(a);
    a.finished.then(function () { releaseAnim(a); }).catch(function () {});
  }

  function releaseAnim(a) {
    var i = anims.indexOf(a);
    if (i >= 0) anims.splice(i, 1);
    if (!anims.length) startBreathing();
  }

  function loopOsc(keyframes, cycle, duration) {
    stopAnims();
    stopBreathing();
    var rounds = Math.max(1, Math.round(duration / cycle));
    var a = pet.animate(keyframes, {
      duration: cycle, iterations: rounds, easing: 'ease-in-out', fill: 'none'
    });
    anims.push(a);
    a.finished.then(function () { releaseAnim(a); }).catch(function () {});
  }

  function shakeX(amp, cycle, duration) {
    loopOsc([
      { transform: 'translateX(0)' },
      { transform: 'translateX(' + amp + 'px)' },
      { transform: 'translateX(0)' },
      { transform: 'translateX(' + (-amp) + 'px)' },
      { transform: 'translateX(0)' }
    ], cycle * 4, duration);
  }

  function sway(deg, cycle, duration) {
    loopOsc([
      { transform: 'rotate(' + deg + 'deg)' },
      { transform: 'rotate(' + (-deg) + 'deg)' }
    ], cycle * 2, duration);
  }

  function danceLoop(duration) {
    loopOsc([
      { transform: 'rotate(6deg) translateX(5px)' },
      { transform: 'rotate(-6deg) translateX(-5px)' }
    ], 600, duration);
  }

  function jumpLoop(duration) {
    loopOsc([
      { transform: 'translateY(0) scale(0.96)' },
      { transform: 'translateY(-28px) scale(1.05)' },
      { transform: 'translateY(0) scale(0.96)' }
    ], 760, duration);
  }

  function cheerLoop(duration) {
    loopOsc([
      { transform: 'rotate(3deg) translateY(-8px)' },
      { transform: 'rotate(-3deg) translateY(-3px)' }
    ], 360, duration);
  }

  function playActionAnimation(id, duration) {
    switch (id) {
      case 'pat': playSeq([{ y: -4, ms: 200 }, { y: 5, ms: 220 }, { y: 0, ms: 200 }]); break;
      case 'feed': playSeq([{ y: 2, rot: -3, ms: 225 }, { y: -2, rot: 3, ms: 225 }, { y: 0, rot: 0, ms: 225 }]); break;
      case 'stretch': playSeq([{ y: 12, ms: duration / 3 }, { y: -14, ms: duration / 3 }, { y: 0, ms: duration / 3 }]); break;
      case 'startle': playSeq([{ y: -22, rot: -4, ms: duration / 3 }, { y: 0, rot: 4, ms: duration / 3 }, { y: 0, rot: 0, ms: duration / 3 }]); break;
      case 'think': playSeq([{ rot: -4, ms: duration / 3 }, { rot: 3, ms: duration / 3 }, { rot: 0, ms: duration / 3 }]); break;
      case 'wash': sway(3, 500, duration); break;
      case 'work': sway(2, 850, duration); break;
      case 'coffee': sway(4, 700, duration); break;
      case 'toy': sway(2, 650, duration); break;
      case 'sit': playSeq([{ y: 28, ms: duration }]); break;
      case 'trip':
      case 'stranded': playSeq([{ y: 0, rot: 0, ms: duration / 3 }, { y: 8, rot: 14, ms: duration / 3 }, { y: 38, rot: 82, ms: duration / 3 }]); break;
      case 'cry': playSeq([{ y: 10, ms: 300 }, { y: 12, ms: 300 }, { y: 10, ms: 300 }]); break;
      case 'shock':
      case 'panic': shakeX(4, 180, duration); break;
      case 'angry':
      case 'rival': shakeX(3, 300, duration); break;
      case 'dizzy': shakeX(7, 460, duration); break;
      case 'dance': danceLoop(duration); break;
      case 'jump': jumpLoop(duration); break;
      case 'cheer': cheerLoop(duration); break;
      case 'wonder': playSeq([{ rot: 8, ms: duration / 3 }, { rot: -8, ms: duration / 3 }, { rot: 0, ms: duration / 3 }]); break;
      case 'fly': playSeq([{ y: -45, rot: 8, ms: duration / 2 }, { y: 0, rot: 0, ms: duration / 2 }]); break;
      case 'ciallo': sway(8, 450, duration); break;
      case 'sleep': playSeq([{ y: 7, rot: 5, ms: duration }]); break;
      default: break;
    }
  }

  /* ---------------- 帧播放 ---------------- */

  var frameTimer = null;
  var loopTimer = null;

  function stopFramePlayback(reset) {
    clearTimeout(frameTimer); frameTimer = null;
    clearInterval(loopTimer); loopTimer = null;
    if (reset !== false) setFrame(restingFrame());
  }

  function playFrame(name, duration) {
    stopFramePlayback(false);
    setFrame(name);
    frameTimer = setTimeout(function () { frameTimer = null; setFrame(restingFrame()); }, duration);
  }

  function startFrameLoop(names, intervals) {
    stopFramePlayback(false);
    var i = 0;
    var step = function () {
      setFrame(names[i]);
      var d = intervals ? intervals[i % intervals.length] : 220;
      i = (i + 1) % names.length;
      loopTimer = setTimeout(step, d);
    };
    step();
  }

  function playBehaviorFrames(id, duration) {
    var loop = (MANIFEST.multiFrameActions || {})[id];
    if (loop) {
      startFrameLoop(loop.frames, loop.intervals);
      frameTimer = setTimeout(function () { stopFramePlayback(); }, duration);
      return;
    }
    playFrame(id === 'jump' ? 'fly' : id, duration);
  }

  /* ---------------- 气泡 ---------------- */

  var speechTimer = null;

  function say(text, ms) {
    bubble.textContent = stripHints(text);
    bubble.classList.add('show');
    clearTimeout(speechTimer);
    speechTimer = setTimeout(function () { bubble.classList.remove('show'); }, ms || 4200);
  }

  /* ---------------- 粒子 ---------------- */

  function particles(icon, count) {
    count = count || 3;
    for (var i = 0; i < count; i++) {
      (function (i) {
        var el = document.createElement('span');
        el.className = 'fx';
        el.textContent = icon;
        var rect = stage.getBoundingClientRect();
        el.style.left = '50%';
        el.style.top = (rect.height * 0.42) + 'px';
        effects.appendChild(el);
        var drift = Math.random() * 160 - 80;
        var turn = Math.random() * 160 - 80;
        var anim = el.animate([
          { transform: 'translate3d(0,0,0) rotate(0deg)', opacity: 0 },
          { opacity: 1, offset: 0.25 },
          { transform: 'translate3d(' + drift + 'px,-90px,0) rotate(' + turn + 'deg)', opacity: 0 }
        ], { duration: 1000, delay: i * 60, easing: 'ease-out', fill: 'forwards' });
        anim.finished.then(function () { el.remove(); }).catch(function () { el.remove(); });
      })(i);
    }
  }

  /* ---------------- 走动 ---------------- */

  var walkDir = -1;
  var walkTimer = null;
  var walkStopTimer = null;

  function maxWalk() {
    var stageW = stage.clientWidth;
    var petW = petWrap.offsetWidth * wrapScale;
    return Math.max(0, (stageW - petW) / 2 - 8);
  }

  function startWalk(duration, announce) {
    stopWalk(false);
    walkDir = Math.random() < 0.5 ? 1 : -1;
    if (announce !== false) say(MANIFEST.behaviors.walk.line, 3400);
    startFrameLoop(['walk', 'walk-b', 'walk-b', 'walk'], [165, 235, 305, 190]);

    walkTimer = setInterval(function () {
      var limit = maxWalk();
      wrapX += walkDir * 3;
      if (wrapX > limit) { wrapX = limit; walkDir = -1; }
      if (wrapX < -limit) { wrapX = -limit; walkDir = 1; }
      applyWrap();
    }, 48);

    walkStopTimer = setTimeout(function () { stopWalk(); }, duration);
  }

  function stopWalk(clearScene) {
    clearInterval(walkTimer); walkTimer = null;
    clearTimeout(walkStopTimer); walkStopTimer = null;
    if (clearScene !== false) {
      stopFramePlayback();
      stopAnims();
      startBreathing();
      setFrame(restingFrame());
    }
  }

  /* ---------------- 行为 ---------------- */

  function behavior(id) {
    return MANIFEST.behaviors[id] || MANIFEST.behaviors.think;
  }

  function runBehavior(id, opts2) {
    opts2 = opts2 || {};
    var b = behavior(id);
    if (id === 'walk') {
      if (opts.freeWalk) startWalk(b.duration, opts2.say);
      return;
    }
    stopWalk(false);
    playActionAnimation(id, b.duration);
    playBehaviorFrames(id, b.duration);
    particles(b.icon, (id === 'cry' || id === 'shock' || id === 'rival') ? 6 : 3);
    if (opts2.say !== false) say(b.line);
  }

  var SIGNATURE = ['ciallo', 'smug', 'pressure', 'shock', 'fly', 'price', 'rival', 'goAway', 'stranded', 'dance', 'jump', 'cheer', 'wonder'];

  function nextIdleBehavior() {
    var urgent = urgentBehavior();
    if (urgent && Math.random() < 0.4) return urgent;
    var p = phase();
    var plans = MANIFEST.scenePlans;
    var pool = (plans[p.id] || plans['default']).slice();
    if (p.id !== 'sleep' && Math.random() < 0.38) pool = pool.concat(SIGNATURE);
    if (!opts.freeWalk) pool = pool.filter(function (x) { return x !== 'walk'; });
    if (!opts.spicy) pool = pool.filter(function (x) { return ['angry', 'rival', 'goAway'].indexOf(x) < 0; });
    return pool.length ? pick(pool) : 'think';
  }

  var idleTimer = null;

  function scheduleIdle() {
    clearTimeout(idleTimer);
    var p = phase();
    var intensity = clamp(opts.intensity, 0.5, 1.8);
    var delay = (15 + Math.random() * 25) * 1000 / Math.max(p.energy * intensity, 0.3);
    idleTimer = setTimeout(function () {
      if (!dragging) runBehavior(nextIdleBehavior());
      scheduleIdle();
    }, delay);
  }

  /* ---------------- 眨眼 ---------------- */

  var blinkTimer = null;

  function scheduleBlink() {
    clearTimeout(blinkTimer);
    blinkTimer = setTimeout(function () {
      var busy = dragging || frameTimer || loopTimer || walkTimer;
      if (!busy) {
        var prev = currentFrame;
        setFrame('blink');
        setTimeout(function () { if (currentFrame === 'blink') setFrame(prev); }, 135);
      }
      scheduleBlink();
    }, 2800 + Math.random() * 4200);
  }

  /* ---------------- 手势（对应 onTouchEvent + SpinTracker.kt） ---------------- */

  var dragging = false;
  var drag = null;
  var lastClickAt = 0;
  var longPressTimer = null;

  function SpinTracker(x, y) {
    this.x = x; this.y = y; this.startedAt = Date.now();
    this.path = 0; this.turn = 0; this.absTurn = 0; this.lastAngle = null; this.dizzy = false;
  }
  SpinTracker.prototype.track = function (x, y) {
    if (this.dizzy) return true;
    var now = Date.now();
    if (now - this.startedAt > 1800) {
      this.x = x; this.y = y; this.startedAt = now;
      this.path = 0; this.turn = 0; this.absTurn = 0; this.lastAngle = null; this.dizzy = false;
    }
    var dx = x - this.x, dy = y - this.y;
    var dist = Math.hypot(dx, dy);
    if (dist < 4) return false;
    var angle = Math.atan2(dy, dx);
    if (this.lastAngle !== null) {
      var d = angle - this.lastAngle;
      while (d > Math.PI) d -= Math.PI * 2;
      while (d < -Math.PI) d += Math.PI * 2;
      this.turn += d;
      this.absTurn += Math.abs(d);
    }
    this.lastAngle = angle;
    this.path += dist;
    this.x = x; this.y = y;
    var elapsed = Math.max(1, now - this.startedAt);
    var speed = this.path / elapsed * 1000;
    var consistency = Math.abs(this.turn) / Math.max(this.absTurn, 0.001);
    this.dizzy = this.path >= 360 && Math.abs(this.turn) >= Math.PI * 2.4 && speed >= 260 && consistency >= 0.68;
    return this.dizzy;
  };

  function onDown(e) {
    if (!session) { say('先登录，才能摸到我哦。', 2600); return; }
    stopWalk();
    stopFramePlayback();
    dragging = true;
    drag = { x: e.clientX, y: e.clientY, total: 0, spin: new SpinTracker(e.clientX, e.clientY) };
    longPressTimer = setTimeout(function () {
      if (drag && drag.total < 8) { drag = null; dragging = false; openSettings(); }
    }, 620);
    stage.setPointerCapture && e.pointerId != null && stage.setPointerCapture(e.pointerId);
  }

  function onMove(e) {
    if (!drag) return;
    var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
    if (dx || dy) {
      drag.spin.track(e.clientX, e.clientY);
      drag.x = e.clientX; drag.y = e.clientY;
      drag.total += Math.abs(dx) + Math.abs(dy);
      if (drag.total > 8) { clearTimeout(longPressTimer); }
    }
  }

  function onUp() {
    clearTimeout(longPressTimer);
    var d = drag;
    drag = null;
    dragging = false;
    if (!d) return;
    if (d.spin.dizzy) { runBehavior('dizzy'); return; }
    if (d.total > 10) { runBehavior('startle'); return; }
    var now = Date.now();
    if (now - lastClickAt < 320) {
      lastClickAt = 0;
      say(statusText(isSleepPhase()), 3600);
    } else {
      lastClickAt = now;
      onPatStat();
      runBehavior('pat');
    }
  }

  /* ---------------- 云存档 ---------------- */

  function setDot(cls) { $('#syncDot').className = 'dot ' + cls; }

  async function pullState() {
    if (!cloud || !session) return;
    setDot('busy');
    try {
      var res = await cloud.database.from('pet_state').select('*').maybeSingle();
      if (res.error) throw res.error;
      if (!res.data) {
        await createRow();
        return;
      }
      var d = res.data;
      rowId = d.id;
      S.satiety = Number(d.satiety);
      S.mood = Number(d.mood);
      S.affinity = Number(d.affinity);
      S.lastTickAt = Date.parse(d.last_tick_at) || Date.now();
      S.affinityDay = d.affinity_day || '';
      S.affinityGainToday = d.affinity_gain_today || 0;
      decay();
      renderStats();
      setDot('on');
    } catch (err) {
      setDot('off');
      toast('读取存档失败：' + (err.message || err), 3200);
    }
  }

  async function createRow() {
    var payload = {
      satiety: S.satiety, mood: S.mood, affinity: S.affinity,
      last_tick_at: new Date().toISOString(),
      affinity_day: dayKey(), affinity_gain_today: 0,
      owner_name: (session.user && session.user.name) || null
    };
    var res = await cloud.database.from('pet_state').insert(payload).select();
    if (res.error) {
      if (res.error.code === '23505') { await pullState(); return; }
      setDot('off');
      toast('建档失败：' + res.error.message, 3200);
      return;
    }
    rowId = res.data && res.data[0] && res.data[0].id;
    setDot('on');
  }

  function changed() {
    renderStats();
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function () { pushState(); }, 1200);
  }

  async function pushState() {
    if (!cloud || !session || !rowId) return;
    setDot('busy');
    try {
      decay();
      var res = await cloud.database.from('pet_state').update({
        satiety: Math.round(S.satiety * 100) / 100,
        mood: Math.round(S.mood * 100) / 100,
        affinity: Math.round(S.affinity * 100) / 100,
        last_tick_at: new Date(S.lastTickAt).toISOString(),
        affinity_day: S.affinityDay,
        affinity_gain_today: S.affinityGainToday,
        updated_at: new Date().toISOString()
      }).eq('id', rowId).select();
      if (res.error) throw res.error;
      if (!res.data || !res.data.length) {
        setDot('off');
        toast('存档没有写入成功（可能不属于当前账号）', 3000);
        return;
      }
      setDot('on');
    } catch (err) {
      setDot('off');
      toast('同步失败：' + (err.message || err), 3000);
    }
  }

  /* ---------------- 登录 ---------------- */

  async function restoreAuth() {
    var url = new URL(location.href);
    if (!url.searchParams.has('code') && !url.searchParams.has('error')) return null;
    var provider = url.searchParams.get('provider');
    if (provider !== 'wechat' && provider !== 'workbuddy') return null;
    var handler = provider === 'wechat' ? cloud.auth.handleWechatWebCallback : cloud.auth.handleWorkBuddyCallback;
    if (typeof handler !== 'function') {
      showLoginError('当前 SDK 缺少该登录方式的回调处理。');
      return null;
    }
    var res = await handler.call(cloud.auth);
    if (res.error) { showLoginError(res.error.message); return null; }
    if (res.data) {
      ['code', 'state', 'provider'].forEach(function (k) { url.searchParams.delete(k); });
      history.replaceState(null, '', url.pathname + (url.search ? url.search : '') + url.hash);
      return res.data;
    }
    return null;
  }

  function showLoginError(msg) { $('#loginErr').textContent = msg || ''; }

  async function signIn(provider) {
    showLoginError('');
    var res = await cloud.auth.signInWithOAuth({ provider: provider, redirectTo: location.origin });
    if (res.error) { showLoginError(res.error.message); return; }
    location.assign(res.data.url);
  }

  function showLogin(show) {
    $('#login').classList.toggle('hidden', !show);
    document.body.classList.toggle('logged-out', show);
  }

  function enterApp(s) {
    session = s;
    showLogin(false);
    $('#hud').style.visibility = 'visible';
    pullState();
  }

  /* ---------------- 设置面板 ---------------- */

  function openSettings() {
    if (!session) return;
    $('#settings').classList.remove('hidden');
  }
  function closeSettings() { $('#settings').classList.add('hidden'); }

  /* ---------------- 启动 ---------------- */

  async function loadConfig() {
    var mRes = await fetch('assets/manifest.json', { cache: 'no-cache' });
    if (!mRes.ok) throw new Error('manifest.json 读取失败');
    MANIFEST = await mRes.json();
    var sRes = await fetch('assets/state.json', { cache: 'no-cache' });
    if (!sRes.ok) throw new Error('state.json 读取失败');
    CFG = await sRes.json();
  }

  function preloadFrames() {
    var ids = MANIFEST.frameFiles || [];
    return Promise.all(ids.map(function (id) {
      return new Promise(function (resolve) {
        var img = new Image();
        img.onload = img.onerror = function () { resolve(); };
        img.src = frameUrl(id);
      });
    }));
  }

  function wireUi() {
    $('#btnWechat').addEventListener('click', function () { signIn('wechat'); });
    $('#btnWorkbuddy').addEventListener('click', function () { signIn('workbuddy'); });
    $('#btnSettings').addEventListener('click', openSettings);
    $('#btnCloseSettings').addEventListener('click', closeSettings);
    $('#btnSync').addEventListener('click', async function () {
      if (!syncing) { syncing = true; await pushState(); syncing = false; }
      toast('已同步');
    });
    $('#btnLogout').addEventListener('click', async function () {
      try { await cloud.auth.signOut(); } catch (e) {}
      session = null; rowId = null;
      closeSettings(); showLogin(true); setDot('');
    });
    $('#optWalk').addEventListener('change', function (e) { opts.freeWalk = e.target.checked; });
    $('#optSpicy').addEventListener('change', function (e) { opts.spicy = e.target.checked; });
    $('#optIntensity').addEventListener('input', function (e) { opts.intensity = parseFloat(e.target.value) || 1; });

    document.querySelectorAll('.act').forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (!session) { say('先登录，才能摸到我哦。', 2600); return; }
        var act = btn.dataset.act;
        if (act === 'pat') { onPatStat(); runBehavior('pat'); }
        else if (act === 'feed') { onFeedStat(); runBehavior('feed'); }
        else { onPatStat(); runBehavior(nextIdleBehavior()); }
      });
    });

    stage.addEventListener('pointerdown', onDown);
    stage.addEventListener('pointermove', onMove);
    stage.addEventListener('pointerup', onUp);
    stage.addEventListener('pointercancel', onUp);

    window.addEventListener('pagehide', function () { if (rowId) pushState(); });
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'hidden' && rowId) pushState();
      if (document.visibilityState === 'visible') renderStats();
    });

    setInterval(renderStats, 60000);
    setInterval(function () { $('#phaseLabel').textContent = phase().label; }, 60000);
  }

  function ensureSdk() {
    return new Promise(function (resolve, reject) {
      if (window.WorkBuddyCloud) { resolve(); return; }
      var s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/@tencent-ai/workbuddy-cloud-sdk@dev/lib/index.global.js';
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error('云服务 SDK 加载失败')); };
      document.head.appendChild(s);
    });
  }

  function boot() {
    try {
      cloud = window.WorkBuddyCloud.createWorkBuddyCloud(PUBLIC_CONFIG);
    } catch (e) {
      showLoginError('云服务 SDK 未能初始化：' + (e.message || e));
    }
    wireUi();
    setFrame(restingFrame());
    startBreathing();
    scheduleBlink();
    if (new URLSearchParams(location.search).has('debug')) {
      window.__lulu = {
        run: runBehavior, frame: setFrame, pat: onPatStat, feed: onFeedStat,
        stats: function () { return { satiety: S.satiety, mood: S.mood, affinity: S.affinity }; },
        next: nextIdleBehavior
      };
    }
  }

  (async function main() {
    try {
      await loadConfig();
    } catch (e) {
      document.body.insertAdjacentHTML('beforeend',
        '<div style="position:fixed;inset:0;display:flex;align-items:center;justify-content:center;padding:24px;text-align:center;font-size:13px;color:#7A6A5C">配置读取失败，请用本地服务器或发布后的地址打开（file:// 不允许 fetch）。</div>');
      return;
    }
    $('#phaseLabel').textContent = phase().label;
    $('#hud').style.visibility = 'hidden';
    document.body.classList.add('logged-out');
    try { await ensureSdk(); } catch (e) { showLoginError(e.message); }
    boot();
    await preloadFrames();
    renderStats();

    var s = null;
    if (cloud) {
      try { s = await restoreAuth(); } catch (e) {}
      if (!s) {
        try {
          var res = await cloud.auth.getSession();
          s = res && res.data ? res.data : null;
        } catch (e) {}
      }
    }
    if (s) {
      enterApp(s);
    } else {
      setDot('');
      showLogin(true);
    }
    scheduleIdle();
  })();
})();

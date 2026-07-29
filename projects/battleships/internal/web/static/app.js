(() => {
  const $ = (id) => document.getElementById(id);
  const N = 10;
  const letters = 'ABCDEFGHIJ'.split('');

  const ui = {
    status: $('status'), tabs: $('tabs'),
    roster: $('roster'), setupBoard: $('setup-board'), opponent: $('opponent'), layout: $('layout'), opponentNote: $('opponent-note'),
    rotate: $('rotate'), scatter: $('scatter'), clear: $('clear'), start: $('start'),
    mine: $('board-mine'), theirs: $('board-theirs'), fleetMine: $('fleet-mine'), fleetTheirs: $('fleet-theirs'), turn: $('turn-label'),
    heat: $('heat'), heatToggle: $('heat-toggle'), log: $('log'), again: $('again'),
    gameOutcome: $('game-outcome'), gameReplay: $('game-replay'), gamePlayPause: $('game-playpause'), gameRewind: $('game-rewind'), gameSpeed: $('game-speed'), gameScrub: $('game-scrub'), gameStepBack: $('game-step-back'), gameStepNext: $('game-step-next'),
    banner: $('banner'), bannerTitle: $('banner-title'), bannerBody: $('banner-body'), bannerOK: $('banner-ok'),
    wa: $('watch-a'), wb: $('watch-b'), wl: $('watch-layout'), seed: $('seed'), race: $('race'),
    watchReplay: $('watch-replay'), playpause: $('playpause'), rewind: $('rewind'), speed: $('speed'), scrub: $('scrub'), stepBack: $('step-back'), stepNext: $('step-next'), watchNote: $('watch-note'),
    nameA: $('name-a'), nameB: $('name-b'), shotsA: $('shots-a'), shotsB: $('shots-b'), wba: $('watch-board-a'), wbb: $('watch-board-b')
  };

  let config, setup = [], selected = null, orient = 'horizontal', state = null, heat = null, log = [];
  let initialState = null, playEvents = [], gameReplayStep = null, gameTimer = null;
  let watch = null, watchStep = 0, timer = null, lastWatchParams = null;

  function setStatus(msg, tone='') { ui.status.textContent = msg || ''; ui.status.dataset.tone = tone; }
  function view(name) {
    document.documentElement.dataset.view = name;
    document.querySelectorAll('.tab').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.goto === name || (name === 'play' && b.dataset.goto === 'setup'))));
  }
  async function api(path, opts={}) {
    const res = await fetch(path, {headers: {'Content-Type':'application/json'}, ...opts});
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }
  function clone(x) { return JSON.parse(JSON.stringify(x)); }

  function emptyGrid(fill='empty') { return Array.from({length:N}, () => Array.from({length:N}, () => fill)); }
  function drawBoard(el, cells, opts={}) {
    el.innerHTML = ''; el.style.setProperty('--n', N);
    el.append(document.createElement('span'));
    letters.forEach(c => { const a = document.createElement('div'); a.className = 'axis axis-col'; a.dataset.col = letters.indexOf(c); a.textContent = c; el.append(a); });
    for (let r=0; r<N; r++) {
      const ax = document.createElement('div'); ax.className = 'axis axis-row'; ax.dataset.row = r; ax.textContent = r; el.append(ax);
      for (let c=0; c<N; c++) {
        const b = document.createElement('button'); b.className = 'cell'; b.type = 'button'; b.dataset.row = r; b.dataset.col = c; b.dataset.state = cells?.[r]?.[c] || 'empty'; b.ariaLabel = `${letters[c]}${r}`;
        if (opts.heat?.[r]?.[c]) b.style.setProperty('--heat-level', opts.heat[r][c]);
        b.addEventListener('mouseenter', () => rails(el, r, c, true));
        b.addEventListener('mouseleave', () => rails(el, r, c, false));
        if (opts.click) b.addEventListener('click', () => opts.click(r,c,b));
        if (opts.place) {
          b.addEventListener('mouseenter', () => ghost(el, r, c));
          b.addEventListener('mouseleave', () => clearGhost(el));
          b.addEventListener('click', () => placeAt(r,c));
          b.addEventListener('dragover', e => { e.preventDefault(); ghost(el, r, c); });
          b.addEventListener('drop', e => { e.preventDefault(); placeAt(r,c); });
        }
        el.append(b);
      }
    }
  }
  function rails(el, r, c, on) {
    el.querySelectorAll(`[data-row="${r}"], [data-col="${c}"]`).forEach(n => n.toggleAttribute('data-lit', on));
    el.querySelectorAll(`.cell[data-row="${r}"], .cell[data-col="${c}"]`).forEach(n => n.toggleAttribute('data-rail', on));
  }

  function setupCells() {
    const g = emptyGrid();
    for (const s of setup) for (const p of span(s.row, s.col, s.size, s.orientation)) if (inside(p.row,p.col)) g[p.row][p.col] = 'ship';
    return g;
  }
  function span(row, col, size, o) { return Array.from({length:size}, (_,i) => ({row: row + (o==='vertical'?i:0), col: col + (o==='horizontal'?i:0)})); }
  function inside(r,c) { return r>=0 && r<N && c>=0 && c<N; }
  function legal(ship, row, col) {
    if (!ship) return false;
    const cells = span(row,col,ship.size,orient);
    return cells.every(p => inside(p.row,p.col) && !setup.some(s => s.name!==ship.name && span(s.row,s.col,s.size,s.orientation).some(q => q.row===p.row && q.col===p.col)));
  }
  function clearGhost(el) { el.querySelectorAll('[data-ghost]').forEach(n => delete n.dataset.ghost); }
  function ghost(el, r, c) {
    clearGhost(el); const ship = config.fleet.find(f => f.name === selected); if (!ship) return;
    const ok = legal(ship,r,c);
    for (const p of span(r,c,ship.size,orient)) if (inside(p.row,p.col)) el.querySelector(`.cell[data-row="${p.row}"][data-col="${p.col}"]`)?.setAttribute('data-ghost', ok ? 'ok' : 'bad');
  }
  function placeAt(r,c) {
    const ship = config.fleet.find(f => f.name === selected); if (!ship || !legal(ship,r,c)) return setStatus('That placement is not legal.', 'bad');
    setup = setup.filter(s => s.name !== ship.name); setup.push({name: ship.name, size: ship.size, row:r, col:c, orientation:orient});
    selected = config.fleet.find(f => !setup.some(s => s.name === f.name))?.name || null;
    renderSetup(); setStatus('Fleet position updated.');
  }
  function renderSetup() {
    drawBoard(ui.setupBoard, setupCells(), {place:true});
    ui.roster.innerHTML = '';
    for (const f of config.fleet) {
      const li = document.createElement('li'), b = document.createElement('button'); b.className = 'ship'; b.draggable = true; b.dataset.name = f.name;
      if (setup.some(s => s.name === f.name)) b.dataset.placed = 'true';
      b.setAttribute('aria-pressed', String(selected === f.name));
      b.innerHTML = `<span class="ship__name">${f.name}</span><span class="ship__pips">${'<i></i>'.repeat(f.size)}</span>`;
      b.onclick = () => { selected = f.name; renderSetup(); };
      b.ondragstart = () => { selected = f.name; renderSetup(); };
      li.append(b); ui.roster.append(li);
    }
    ui.start.disabled = setup.length !== config.fleet.length;
  }
  function rotate() { orient = orient === 'horizontal' ? 'vertical' : 'horizontal'; setStatus(`Orientation: ${orient}.`); }

  function renderGame(extraEvents=[]) {
    const replaying = gameReplayStep !== null;
    const shown = replaying ? replayState(gameReplayStep) : state;
    const h = !replaying && ui.heat.checked && heat?.scorable ? heat.cells : null;
    drawBoard(ui.mine, shown.mine.cells, {heat:h});
    drawBoard(ui.theirs, shown.theirs.cells, {click: state.over ? null : fireAt});
    ui.turn.textContent = replaying ? `${shown.opponent} · replay ${gameReplayStep}/${playEvents.length}` : `${shown.opponent} · turn ${shown.turn}`;
    ui.heat.disabled = replaying || !state.scorable; ui.heatToggle.toggleAttribute('data-disabled', replaying || !state.scorable); ui.heatToggle.title = state.scorable ? '' : 'This strategy does not expose a score grid.';
    renderFleet(ui.fleetMine, shown.mine.ships, true); renderFleet(ui.fleetTheirs, shown.theirs.ships, shown.over);
    ui.log.toggleAttribute('data-empty', log.length === 0); ui.log.innerHTML = log.map(e => `<li data-by="${e.by}" ${e.hit?'data-hit':''} ${e.sunk?'data-sunk':''}><b>${e.by}</b><span>${e.at}: ${e.sunk ? `sank ${e.sunk}` : e.hit ? 'hit' : 'miss'}</span></li>`).join('');
    renderGameReplayControls();
    for (const e of extraEvents) { const board = e.by === 'you' ? ui.theirs : ui.mine; board.querySelector(`.cell[data-row="${e.row}"][data-col="${e.col}"]`)?.setAttribute('data-fx', e.sunk?'sunk':e.hit?'hit':'miss'); }
    if (state.over) endGame();
  }
  function replayState(step) {
    const shown = clone(state);
    shown.mine = baseBoard(initialState?.mine || state.mine);
    shown.theirs = baseBoard(state.theirs);
    shown.over = true;

    for (const e of playEvents.slice(0, step)) applyReplayEvent(shown, e);
    return shown;
  }
  function baseBoard(board) {
    const b = clone(board);
    b.cells = emptyGrid();
    for (const s of b.ships) {
      s.hits = 0; s.sunk = false;
      for (const p of s.cells || []) b.cells[p.row][p.col] = 'ship';
    }
    return b;
  }
  function applyReplayEvent(shown, e) {
    const board = e.by === 'you' ? shown.theirs : shown.mine;
    const ship = board.ships.find(s => (s.cells || []).some(p => p.row === e.row && p.col === e.col));
    board.cells[e.row][e.col] = e.hit ? (e.sunk ? 'sunk' : 'hit') : 'miss';
    if (!ship || !e.hit) return;
    ship.hits = Math.min(ship.size, (ship.hits || 0) + 1);
    if (e.sunk) {
      ship.sunk = true; ship.hits = ship.size;
      for (const p of ship.cells || []) board.cells[p.row][p.col] = 'sunk';
    }
  }
  function renderGameReplayControls() {
    const canReplay = state.over && playEvents.length > 0 && initialState;
    ui.gameReplay.hidden = !canReplay; ui.gameOutcome.hidden = !state.over;
    if (state.over) ui.gameOutcome.textContent = state.phase === 'won' ? 'Victory — replay the battle below or start a new game.' : 'Defeat — replay the battle below or start a new game.';
    if (!canReplay) return;
    ui.gameScrub.max = playEvents.length; ui.gameScrub.value = gameReplayStep ?? playEvents.length;
  }
  function setGameReplayStep(step) { stopGameReplay(); gameReplayStep = Math.max(0, Math.min(playEvents.length, step)); renderGame(); }
  function gameReplayTick() { gameReplayStep = Math.min(playEvents.length, (gameReplayStep ?? 0) + 1); renderGame(); if (gameReplayStep >= playEvents.length) stopGameReplay(); }
  function playGameReplay() { if (gameTimer) return stopGameReplay(); if (gameReplayStep === null || gameReplayStep >= playEvents.length) gameReplayStep = 0; gameTimer = setInterval(gameReplayTick, 1000 / Number(ui.gameSpeed.value)); ui.gamePlayPause.textContent = 'Pause'; renderGame(); }
  function stopGameReplay() { clearInterval(gameTimer); gameTimer = null; ui.gamePlayPause.textContent = 'Play'; }
  function endGame() {
    ui.banner.hidden = true;
    if (gameReplayStep === null) {
      gameReplayStep = playEvents.length;
      setStatus(state.phase === 'won' ? 'Victory — enemy fleet sunk. Use the replay controls to review the battle.' : 'Defeat — your fleet was sunk. Use the replay controls to review the battle.', state.phase === 'won' ? 'sunk' : 'bad');
    }
  }

  function renderFleet(el, ships, mine) {
    el.innerHTML = ships.map(s => `<li ${s.sunk?'data-sunk':''}><span>${mine || s.sunk ? s.name : 'Unknown'}</span><span class="bar"><i style="--dmg:${(s.hits||0)/s.size*100}%"></i></span><span>${s.hits||0}/${s.size}</span></li>`).join('');
  }
  async function refreshHeat() { if (!state?.scorable) { heat = null; return; } heat = await api('/api/game/heatmap').catch(() => null); }
  async function fireAt(row,col,cell) {
    if (state.over || cell.dataset.state === 'hit' || cell.dataset.state === 'miss' || cell.dataset.state === 'sunk') return;
    try { const res = await api('/api/game/fire', {method:'POST', body:JSON.stringify({row,col})}); state = res.state; playEvents.push(...res.events); log.unshift(...res.events); await refreshHeat(); renderGame(res.events); setStatus(res.events.map(e => `${e.by} ${e.at} ${e.hit?'hit':'miss'}`).join(' · '), res.events.some(e=>e.sunk)?'sunk':res.events.some(e=>e.hit)?'hit':''); } catch(e) { setStatus(e.message, 'bad'); }
  }
  function endBanner() { ui.banner.hidden = false; ui.banner.dataset.outcome = state.phase; ui.bannerTitle.textContent = state.phase === 'won' ? 'You won' : 'Fleet lost'; ui.bannerBody.textContent = state.phase === 'won' ? 'The enemy fleet is on the bottom.' : `${state.opponent} sank your fleet.`; }

  async function start(random=false) {
    try { const body = {opponent: ui.opponent.value, layout: ui.layout.value, random, ships: random ? setup.map(({name,row,col,orientation})=>({name,row,col,orientation})) : setup.map(({name,row,col,orientation})=>({name,row,col,orientation}))};
      const created = await api('/api/game', {method:'POST', body:JSON.stringify(body)}); state = created.state || created; initialState = clone(state); playEvents = []; gameReplayStep = null; stopGameReplay(); log = []; await refreshHeat(); ui.banner.hidden = true; view('play'); renderGame(); setStatus('Game started. Choose a target.'); } catch(e) { setStatus(e.message, 'bad'); }
  }

  function baseWatchCells(board) { return board.cells.map(row => row.map(c => (c === 'ship' || c === 'hit' || c === 'sunk') ? 'ship' : 'empty')); }
  function watchCells(i, step) { const g = baseWatchCells(watch.boards[1 - i]); for (let k=0;k<step;k++) { const s = watch.steps[k]; if (s.by === i) g[s.row][s.col] = s.sunk ? 'sunk' : s.hit ? 'hit' : 'miss'; } return g; }
  function renderWatch() {
    if (!watch) return; ui.scrub.value = watchStep; ui.shotsA.textContent = `${watch.steps.slice(0,watchStep).filter(s=>s.by===0).length} shots fired`; ui.shotsB.textContent = `${watch.steps.slice(0,watchStep).filter(s=>s.by===1).length} shots fired`;
    drawBoard(ui.wba, watchCells(0, watchStep)); drawBoard(ui.wbb, watchCells(1, watchStep));
    if (watchStep >= watch.steps.length) { stopWatch(); ui.watchNote.textContent = `${watch.names[watch.winner]} wins in ${watch.shots[watch.winner]} shots.`; }
  }
  function setWatchStep(step) { stopWatch(); if (!watch) return; watchStep = Math.max(0, Math.min(watch.steps.length, step)); renderWatch(); }
  function tickWatch() { watchStep = Math.min(watch.steps.length, watchStep+1); renderWatch(); }
  function playWatch() { if (timer) return stopWatch(); timer = setInterval(tickWatch, 1000 / Number(ui.speed.value)); ui.playpause.textContent = 'Pause'; }
  function stopWatch() { clearInterval(timer); timer = null; ui.playpause.textContent = 'Play'; }

  async function init() {
    config = await api('/api/config');
    for (const sel of [ui.opponent, ui.wa, ui.wb]) sel.innerHTML = config.opponents.map(o => `<option>${o}</option>`).join('');
    ui.opponent.value = config.opponents.includes('density') ? 'density' : config.opponents[0]; ui.wb.value = config.opponents[1] || config.opponents[0];
    for (const sel of [ui.layout, ui.wl]) sel.innerHTML = config.layouts.map(o => `<option>${o}</option>`).join('');
    selected = config.fleet[0].name; renderSetup(); drawBoard(ui.wba, emptyGrid()); drawBoard(ui.wbb, emptyGrid()); ui.watchReplay.hidden = true;
    ui.opponentNote.textContent = 'Density exposes a heatmap; other strategies keep the toggle disabled.';
    try { state = await api('/api/game'); if (state && !state.over) { await refreshHeat(); view('play'); renderGame(); } } catch {}
  }

  ui.tabs.onclick = e => { if (e.target.matches('.tab')) view(e.target.dataset.goto); };
  ui.rotate.onclick = rotate; document.addEventListener('keydown', e => { if (e.key.toLowerCase() === 'r') rotate(); });
  ui.setupBoard.oncontextmenu = e => { e.preventDefault(); rotate(); };
  ui.clear.onclick = () => { setup=[]; selected=config.fleet[0].name; renderSetup(); };
  ui.scatter.onclick = () => start(true); ui.start.onclick = () => start(false); ui.again.onclick = ui.bannerOK.onclick = () => { ui.banner.hidden = true; stopGameReplay(); setup=[]; selected=config.fleet[0].name; renderSetup(); view('setup'); };
  ui.gamePlayPause.onclick = playGameReplay;
  ui.gameRewind.onclick = () => setGameReplayStep(0);
  ui.gameStepBack.onclick = () => setGameReplayStep((gameReplayStep ?? playEvents.length) - 1);
  ui.gameStepNext.onclick = () => setGameReplayStep((gameReplayStep ?? 0) + 1);
  ui.gameScrub.oninput = () => setGameReplayStep(Number(ui.gameScrub.value));
  ui.heat.onchange = async () => { await refreshHeat(); renderGame(); };
  ui.race.onclick = async () => { try { stopWatch(); ui.race.disabled = true; ui.race.textContent = 'Running…'; let params = {a:ui.wa.value,b:ui.wb.value,layout:ui.wl.value,seed:Number(ui.seed.value)||0}; if (lastWatchParams && JSON.stringify(params) === JSON.stringify(lastWatchParams)) { params.seed++; ui.seed.value = params.seed; } watch = await api('/api/watch', {method:'POST', body:JSON.stringify(params)}); lastWatchParams = {...params}; watchStep = 0; ui.nameA.textContent = `${watch.names[0]} firing at ${watch.names[1]}`; ui.nameB.textContent = `${watch.names[1]} firing at ${watch.names[0]}`; ui.scrub.max = watch.steps.length; ui.watchReplay.hidden = false; ui.watchNote.textContent = `${watch.steps.length} shots recorded with seed ${params.seed}. Click Run simulation again for a fresh seed.`; renderWatch(); } catch(e) { setStatus(e.message, 'bad'); } finally { ui.race.disabled = false; ui.race.textContent = 'Run simulation'; } };
  ui.playpause.onclick = playWatch; ui.rewind.onclick = () => setWatchStep(0); ui.stepBack.onclick = () => setWatchStep(watchStep - 1); ui.stepNext.onclick = () => setWatchStep(watchStep + 1); ui.scrub.oninput = () => setWatchStep(Number(ui.scrub.value));

  init().catch(e => setStatus(e.message, 'bad'));
})();

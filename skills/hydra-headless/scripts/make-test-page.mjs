#!/usr/bin/env node
// Generates a self-contained Hydra test page with the headless traps pre-handled:
// error hook, first-frame flag, optional rAF gate, static-gradient fallback.
// Pair with agent-browser (screenshot) + png-lum.mjs (pixel verification).
import { writeFileSync, readFileSync, statSync, mkdirSync, rmSync } from 'fs';

const DEFAULT_ENGINE = 'https://cdn.jsdelivr.net/npm/hydra-synth@1.4.0/dist/hydra-synth.js';

const args = process.argv.slice(2);
function argOf(flag) {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : null;
}
const has = (f) => args.includes(f);

if (has('--help') || has('-h') || args.length === 0) {
  console.log(`usage: node make-test-page.mjs --patch "osc(10,0.1,1.5).out()" --out page.html
  --engine URL-or-file   hydra-synth UMD build (default: jsdelivr pinned @1.4.0; a local file is copied next to --out and referenced relatively)
  --width N              canvas width  (default 1280)
  --height N             canvas height (default 720)
  --gate                 install the rAF pause gate (window.__animGate) before the engine loads
  --fallback "#a,#b"     show a static two-color gradient if the engine errors
  --selftest             offline checks, no network`);
  process.exit(0);
}

// --- engine resolution -------------------------------------------------------
function engineSrc(outPath) {
  const e = argOf('--engine') || DEFAULT_ENGINE;
  if (/^https?:\/\//.test(e)) return { tag: e };
  const st = statSync(e);
  if (st.size < 10000) throw new Error(`engine file ${e} looks too small (${st.size} B) to be hydra-synth`);
  // copy local engine beside the page so file:// and the local server both work
  const base = 'hydra-synth.js';
  const dest = outPath.replace(/[^/]+$/, base);
  writeFileSync(dest, readFileSync(e));
  return { tag: `./${base}`, copied: dest };
}

// --- page template -----------------------------------------------------------
function buildPage({ patch, engine, width, height, gate, fallback }) {
  const fb = fallback
    ? `<style>#fb{position:fixed;inset:0;display:none;background:linear-gradient(115deg,${fallback[0]},${fallback[1]})}</style>`
    : '';
  const fbScript = fallback
    ? `if (window.__hydraError) document.getElementById('fb').style.display = 'block';`
    : '';
  const gateScript = gate
    ? `<script>
// rAF gate: install BEFORE hydra-synth loads. regl resolves rAF at call time,
// so flipping the gate off pauses the synth with no fork and no engine edit.
(function () {
  var q = [], on = true, real = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function (cb) { if (on) return real(cb); q.push(cb); return 0; };
  window.__animGate = { set: function (v) { on = v; if (v) q.splice(0).forEach(real); }, isOn: function () { return on; } };
})();
<\/script>`
    : '';
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>HYDRA-LOADING</title>
<style>
  html, body { margin: 0; height: 100%; background: #000; overflow: hidden; }
  canvas { display: block; width: 100vw; height: 100vh; }
${fallback ? '  #fb { position: fixed; inset: 0; display: none; }\n' : ''}</style>
${fb}
</head>
<body>
<canvas id="c" width="${width}" height="${height}"></canvas>
${fallback ? '<div id="fb"></div>' : ''}
<script>
// Failures are silent in hydra-synth — surface everything.
window.__hydraError = null;
window.__hydraReady = false;
window.onerror = function (msg, src, line) {
  window.__hydraError = msg + ' @' + line;
  document.title = 'HYDRA-ERROR';
  return false;
};
</script>
${gateScript}
<script src="${engine}"></script>
<script>
(function () {
  try {
    if (typeof Hydra === 'undefined') throw new Error('Hydra global missing — engine did not load');
    var h = new Hydra({ canvas: document.getElementById('c'), width: ${width}, height: ${height}, autoStart: true, detectAudio: false });
    ${patch}
    // first confirmed paint: probe for non-black pixels, reading IN a rAF
    // callback (the drawing buffer is cleared after compositing — an
    // out-of-frame read from setTimeout returns zeros even when rendering)
    var t0 = Date.now();
    (function poll() {
      window.requestAnimationFrame(function () {
        var g = document.createElement('canvas'); g.width = 8; g.height = 8;
        var c2 = g.getContext('2d');
        c2.drawImage(document.getElementById('c'), 0, 0, 8, 8);
        var d = c2.getImageData(0, 0, 8, 8).data, lit = 0;
        for (var i = 0; i < d.length; i += 4) if (d[i] + d[i + 1] + d[i + 2] > 30) lit++;
        if (lit > 4) { window.__hydraReady = true; document.title = 'HYDRA-LIVE'; return; }
        if (Date.now() - t0 > 30000) { window.__hydraError = 'no non-black pixels after 30s'; document.title = 'HYDRA-ERROR'; return; }
        setTimeout(poll, 250);
      });
    })();
  } catch (e) {
    window.__hydraError = String(e);
    document.title = 'HYDRA-ERROR';
  }
  ${fbScript}
})();
</script>
</body>
</html>
`;
}

// --- selftest ----------------------------------------------------------------
function selftest() {
  const checks = [];
  const tmp = '/tmp/hydra-headless-selftest';
  rmSync(tmp, { recursive: true, force: true });
  mkdirSync(tmp, { recursive: true });

  const p1 = `${tmp}/gated.html`;
  writeFileSync(p1, buildPage({ patch: 'osc(3,0.02,1.2).out()', engine: DEFAULT_ENGINE, width: 640, height: 360, gate: true, fallback: ['#111', '#222'] }));
  const s1 = readFileSync(p1, 'utf8');
  checks.push(['gate installed before engine script tag', s1.indexOf('__animGate') < s1.indexOf(`src="${DEFAULT_ENGINE}"`) && s1.indexOf('__animGate') > -1]);
  checks.push(['patch embedded', s1.includes('osc(3,0.02,1.2).out()')]);
  checks.push(['error hook present', s1.includes('window.onerror') && s1.includes('__hydraError')]);
  checks.push(['fallback present', s1.includes('id="fb"')]);
  checks.push(['ready poll present', s1.includes('__hydraReady')]);
  checks.push(['detectAudio off', s1.includes('detectAudio: false')]);

  const p2 = `${tmp}/plain.html`;
  writeFileSync(p2, buildPage({ patch: 'shape(4).out()', engine: DEFAULT_ENGINE, width: 320, height: 180, gate: false, fallback: null }));
  const s2 = readFileSync(p2, 'utf8');
  checks.push(['no gate when omitted', !s2.includes('__animGate')]);
  checks.push(['no fallback when omitted', !s2.includes('id="fb"')]);
  checks.push(['dimensions in canvas attrs', s2.includes('width="320" height="180"')]);

  let ok = true;
  for (const [name, pass] of checks) { console.log(`${pass ? 'OK  ' : 'FAIL'} ${name}`); if (!pass) ok = false; }
  console.log(ok ? 'selftest: PASS' : 'selftest: FAIL');
  process.exit(ok ? 0 : 1);
}

if (has('--selftest')) { selftest(); process.exit(0); }

const patch = argOf('--patch');
const out = argOf('--out');
if (!patch || !out) { console.error('error: --patch and --out are required (see --help)'); process.exit(2); }
if (!/\.out\(\)/.test(patch)) { console.error('error: patch must end with a .out() call — nothing renders otherwise'); process.exit(2); }

const width = parseInt(argOf('--width') || '1280', 10);
const height = parseInt(argOf('--height') || '720', 10);
const fbArg = argOf('--fallback');
const engine = engineSrc(out);
const html = buildPage({ patch, engine: engine.tag, width, height, gate: has('--gate'), fallback: fbArg ? fbArg.split(',').map(s => s.trim()) : null });
writeFileSync(out, html);
console.log(`wrote ${out} (${Buffer.byteLength(html)} B, engine: ${engine.tag}${engine.copied ? `, copied to ${engine.copied}` : ''})`);
console.log('next: agent-browser set viewport WIDTH HEIGHT && agent-browser open file://PAGE  (or serve the dir);');
console.log('wait for title HYDRA-LIVE (feedback patches need several seconds), then screenshot + node png-lum.mjs shot.png');

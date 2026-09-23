const { stripMd, resolveEdit } = require('./core.js'); const corpus = require('./corpus.js');
let seed = +process.argv[2] || 7; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648; const ri = n => Math.floor(rnd() * n);
const POOL = ['가', '한글', 'a', ' ', '안녕 ', '\n', '요.'];
let T=0,O=0; const byOp={}; const rows=[];
for (const [name, raw] of Object.entries(corpus)) {
  const v = stripMd(raw), S = v.out; let n = 0, ok = 0; const bad = [];
  for (let t = 0; t < 1500; t++) {
    const op = ri(3); let d0 = ri(S.length + 1), d1 = d0, ins = '';
    if (op !== 0) d1 = Math.min(S.length, d0 + 1 + ri(6));
    if (op !== 1) ins = POOL[ri(POOL.length)];
    if (d0 === d1 && !ins) continue;
    const r = resolveEdit(raw, v, d0, d1, ins); n++;
    const good = r.view.out === S.slice(0, d0) + ins + S.slice(d1);
    const k = ['입력', '지우기', '덮어쓰기'][op] + (ins.includes('\n') ? '(Enter)' : ''); byOp[k] = byOp[k] || [0,0]; byOp[k][0]++; if (good) byOp[k][1]++;
    if (good) ok++; else if (bad.length < 3) bad.push(JSON.stringify(S.slice(Math.max(0,d0-5), d0)) + ' [' + JSON.stringify(S.slice(d0, d1)) + '→' + JSON.stringify(ins) + '] ' + JSON.stringify(S.slice(d1, d1 + 5)) + ' ⇒ ' + JSON.stringify(r.view.out.slice(Math.max(0,d0-5), d0 + ins.length + 7)));
  }
  T+=n; O+=ok; rows.push([name, ok/n*100, bad]);
}
for (const [name, pct, bad] of rows) { console.log(name.padEnd(10), pct.toFixed(1) + '%'); if (process.argv[3]) for (const b of bad) console.log('    ', b); }
console.log('전체', (O/T*100).toFixed(1)+'%'); for (const [k,[n,o]] of Object.entries(byOp)) console.log('  ', k.padEnd(12), (o/n*100).toFixed(1)+'%');

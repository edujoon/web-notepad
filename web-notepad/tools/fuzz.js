const { stripMd, mapEdit, resolveEdit } = require('./core.js');
const corpus = require('./corpus.js');
let seed = 12345; const rnd = () => (seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648;
const ri = (n) => Math.floor(rnd() * n);
const POOL = ['가', '나', '다', '한', '글', 'a', 'b', 'Z', ' ', '  ', '안녕', 'test', '\n', '요.'];
const docs = Object.values(corpus);
const fails = {}; let total = 0, ok = 0;
for (let round = 0; round < 60; round++) {
  let raw = docs[round % docs.length];
  for (let step = 0; step < 120; step++) {
    const v = stripMd(raw), S = v.out;
    const op = ri(3);
    let d0 = ri(S.length + 1), d1 = d0, ins = '';
    if (op !== 0) d1 = Math.min(S.length, d0 + 1 + ri(8));
    if (op !== 1) { ins = POOL[ri(POOL.length)]; if (rnd() < .3) ins += POOL[ri(POOL.length)]; }
    if (d0 === d1 && !ins) continue;
    const R = resolveEdit(raw, v, d0, d1, ins); const rs = 0, re = 0;
    const nr = R.raw;
    const got = R.view.out, want = S.slice(0, d0) + ins + S.slice(d1);
    total++;
    if (got === want) { ok++; raw = nr; continue; }
    let i = 0; while (got[i] === want[i]) i++;
    const kind = `${op === 0 ? 'insert' : op === 1 ? 'delete' : 'replace'}${ins.includes('\n') ? '+NL' : ''}`;
    const key = kind;
    (fails[key] = fails[key] || []).push({ S: JSON.stringify(S.slice(Math.max(0, d0 - 12), d1 + 12)), del: JSON.stringify(S.slice(d0, d1)), ins: JSON.stringify(ins), rawAround: JSON.stringify(raw.slice(Math.max(0, rs - 14), re + 14)), want: JSON.stringify(want.slice(Math.max(0, i - 10), i + 14)), got: JSON.stringify(got.slice(Math.max(0, i - 10), i + 14)) });
    raw = nr;
  }
}
console.log(`총 ${total}회 편집, 화면 그대로 반영 ${ok}회 (${(ok / total * 100).toFixed(1)}%)`);
for (const [k, arr] of Object.entries(fails)) { console.log(`\n## ${k}: ${arr.length}건`); for (const f of arr.slice(0, 5)) console.log(f.del, f.ins, "| raw:", f.rawAround, "| want:", f.want, "| got:", f.got); }

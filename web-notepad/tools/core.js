function stripMd(raw) {
  const out = [], A = [], B = [], groups = [], lps = [];
  const n = raw.length;
  const emit = (ch, s, e) => { out.push(ch); A.push(s); B.push(e); };
  const emitRaw = (s, e) => { for (let i = s; i < e; i++) { out.push(raw[i]); A.push(i); B.push(i + 1); } };
  const PUNCT = /[!-\/:-@\[-`{-~]/;
  const WORD = /[\p{L}\p{N}]/u;
  const WS = /\s/;
  const TAG = /^<\/?(br|hr|b|strong|i|em|u|s|strike|del|ins|mark|sup|sub|span|small|big|kbd|code|a|font|center|p|div|img|abbr|cite|q|samp|var|tt)(?:\s[^<>]*)?\/?>/i;
  const DEF = /^ {0,3}\[((?:[^\]\\]|\\.)+)\]:[ \t]*(?:<[^>\n]*>|[^\s<>]\S*)(?:[ \t]+(?:"[^"]*"|'[^']*'|\([^)]*\)))?[ \t]*$/;
  const FENCE = /^ {0,3}(`{3,}|~{3,})(.*)$/;
  const norm = (l) => l.trim().replace(/\s+/g, ' ').toLowerCase();
  const defs = new Set(), defLines = new Set();
  let inCell = false;

  function codeEnd(i, e) {
    let k = i; while (k < e && raw[k] === '`') k++;
    const len = k - i; let j = k;
    while (j < e) {
      if (raw[j] === '`') { let t = j; while (t < e && raw[t] === '`') t++; if (t - j === len) return { open: k, close: j, end: t }; j = t; }
      else j++;
    }
    return null;
  }
  function bracketEnd(i, e) {
    let depth = 0;
    for (let j = i; j < e; j++) {
      const c = raw[j];
      if (c === '\\') { j++; continue; }
      if (c === '`') { const r = codeEnd(j, e); if (r) { j = r.end - 1; continue; } }
      if (c === '[') depth++;
      else if (c === ']') { depth--; if (depth === 0) return j; }
    }
    return -1;
  }
  function parseLink(i, e) {
    const j = bracketEnd(i, e);
    if (j < 0 || j === i + 1) return null;
    if (raw[j + 1] === '(') {
      let k = j + 2, pd = 1;
      for (; k < e; k++) {
        const c = raw[k];
        if (c === '\\') { k++; continue; }
        if (c === '(') pd++;
        else if (c === ')') { pd--; if (pd === 0) break; }
      }
      return k < e ? { textEnd: j, end: k + 1 } : null;
    }
    if (!defs.size) return null;
    if (raw[j + 1] === '[') {
      const k = raw.indexOf(']', j + 2);
      if (k !== -1 && k < e) {
        const label = raw.slice(j + 2, k) || raw.slice(i + 1, j);
        if (defs.has(norm(label))) return { textEnd: j, end: k + 1 };
      }
    }
    if (defs.has(norm(raw.slice(i + 1, j)))) return { textEnd: j, end: j + 1 };
    return null;
  }
  function tryEmph(i, s, e) {
    const c = raw[i];
    let k = i; while (k < e && raw[k] === c) k++;
    const L = k - i;
    if (L > 3 || (c === '~' && L !== 2)) return null;
    if (k >= e || WS.test(raw[k])) return null;
    if (c === '_' && i > s && WORD.test(raw[i - 1])) return null;
    let j = k;
    while (j < e) {
      const ch = raw[j];
      if (ch === '\\') { j += 2; continue; }
      if (ch === '`') { const r = codeEnd(j, e); if (r) { j = r.end; continue; } }
      if (ch === c) {
        let t = j; while (t < e && raw[t] === c) t++;
        if (t - j === L && j > k && !WS.test(raw[j - 1])) {
          if (!(c === '_' && t < e && WORD.test(raw[t]))) return { cs: k, ce: j, end: t, L };
        }
        j = t; continue;
      }
      j++;
    }
    return null;
  }
  const TAGS = { 1: ['<em>', '</em>'], 2: ['<strong>', '</strong>'], 3: ['<strong><em>', '</em></strong>'] };
  function inline(s, e) {
    if (e - s > 20000) { emitRaw(s, e); return; }
    let i = s;
    while (i < e) {
      const c = raw[i];
      if (c === '\\' && i + 1 < e && PUNCT.test(raw[i + 1])) { emit(raw[i + 1], i, i + 2); i += 2; continue; }
      if (c === '`') {
        const r = codeEnd(i, e);
        if (r) { const cs = out.length; emitRaw(r.open, r.close); groups.push({ kind: 'code', gs: i, ge: r.end, cs, ce: out.length, rcs: r.open, rce: r.close, split: true }); i = r.end; continue; }
        let k = i; while (k < e && raw[k] === '`') k++; emitRaw(i, k); i = k; continue;
      }
      if ((c === '!' && raw[i + 1] === '[') || c === '[') {
        const o = c === '!' ? i + 1 : i;
        const r = parseLink(o, e);
        if (r) { const cs = out.length; inline(o + 1, r.textEnd); groups.push({ kind: 'link', gs: i, ge: r.end, cs, ce: out.length, rcs: o + 1, rce: r.textEnd, split: true }); i = r.end; continue; }
      }
      if (c === '<') {
        const seg = raw.slice(i, Math.min(e, i + 2048));
        const m = /^<((?:https?|mailto|ftp):[^\s<>]+|[^\s<>@]+@[^\s<>@]+\.[^\s<>@]+)>/i.exec(seg);
        if (m) { const cs = out.length; emitRaw(i + 1, i + 1 + m[1].length); groups.push({ kind: 'link', gs: i, ge: i + m[0].length, cs, ce: out.length, rcs: i + 1, rce: i + 1 + m[1].length, split: false }); i += m[0].length; continue; }
        const t = TAG.exec(seg);
        if (t) { if (t[1].toLowerCase() === 'br') emit(inCell ? ' ' : '\n', i, i + t[0].length); i += t[0].length; continue; }
      }
      if (c === '*' || c === '_' || c === '~') {
        const r = tryEmph(i, s, e);
        if (r) {
          const cs = out.length; inline(r.cs, r.ce);
          groups.push({ kind: 'emph', gs: i, ge: r.end, cs, ce: out.length, rcs: r.cs, rce: r.ce, split: true, tag: c === '~' ? ['<del>', '</del>'] : TAGS[r.L] });
          i = r.end; continue;
        }
        let k = i; while (k < e && raw[k] === c) k++; emitRaw(i, k); i = k; continue;
      }
      out.push(c); A.push(i); B.push(i + 1); i++;
    }
  }
  const isSep = (t) => t.includes('|') && t.includes('-') && /^[ \t]*\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$/.test(t);
  function tableRow(s, e) {
    const pipes = []; let inCode = false;
    for (let i = s; i < e; i++) {
      const c = raw[i];
      if (c === '\\') { i++; continue; }
      if (c === '`') { inCode = !inCode; continue; }
      if (c === '|' && !inCode) pipes.push(i);
    }
    let i0 = s; while (i0 < e && (raw[i0] === ' ' || raw[i0] === '\t')) i0++;
    let te = e; while (te > s && (raw[te - 1] === ' ' || raw[te - 1] === '\t')) te--;
    let cs0 = s, ce0 = e;
    if (pipes.length && pipes[0] === i0) cs0 = pipes.shift() + 1;
    if (pipes.length && pipes[pipes.length - 1] === te - 1) ce0 = pipes.pop();
    const cells = [];
    let a0 = cs0;
    for (let k = 0; k <= pipes.length; k++) {
      const b0 = k < pipes.length ? pipes[k] : ce0;
      let a = a0, b = b0;
      while (a < b && (raw[a] === ' ' || raw[a] === '\t')) a++;
      while (b > a && (raw[b - 1] === ' ' || raw[b - 1] === '\t')) b--;
      cells.push([a, b]);
      a0 = b0 + 1;
    }
    inCell = true;
    for (let k = 0; k < cells.length; k++) {
      inline(cells[k][0], cells[k][1]);
      if (k < cells.length - 1) emit('\t', cells[k][1], cells[k + 1][0]);
    }
    inCell = false;
  }

  const lines = [];
  { let ls = 0; for (;;) { let nl = raw.indexOf('\n', ls); if (nl === -1) nl = n; lines.push([ls, nl]); if (nl === n) break; ls = nl + 1; } }
  // reference definitions: "[label]: url" lines (not inside fences, not continuing a paragraph)
  if (raw.includes(']:')) {
    let f = null, open = true;
    for (let li = 0; li < lines.length; li++) {
      const L = raw.slice(lines[li][0], lines[li][1]);
      if (f) { const m = /^ {0,3}(`{3,}|~{3,})[ \t]*$/.exec(L); if (m && m[1][0] === f.ch && m[1].length >= f.len) f = null; open = true; continue; }
      const mf = FENCE.exec(L);
      if (mf && !(mf[1][0] === '`' && mf[2].includes('`'))) { f = { ch: mf[1][0], len: mf[1].length }; open = false; continue; }
      const md = DEF.exec(L);
      if (md && open) { defs.add(norm(md[1])); defLines.add(li); continue; }
      open = L.trim() === '' || /^ {0,3}#{1,6}(?:[ \t]|$)/.test(L);
    }
  }
  let fence = null, table = false, prevBlank = true, prevOdd = false;
  for (let li = 0; li < lines.length; li++) {
    const [s, e] = lines[li];
    const hasNL = e < n;
    const L = raw.slice(s, e);
    const hide = () => {
      if (!hasNL) { const k = out.length - 1; if (k >= 0 && out[k] === '\n' && A[k] === s - 1) { out.pop(); A.pop(); B.pop(); } }
    };
    const nl = () => { if (hasNL) { out.push('\n'); A.push(e); B.push(e + 1); } };
    const blank = L.trim() === '';
    if (fence) {
      const m = /^ {0,3}(`{3,}|~{3,})[ \t]*$/.exec(L);
      if (m && m[1][0] === fence.ch && m[1].length >= fence.len) { fence = null; hide(); prevBlank = false; continue; }
      emitRaw(s, e); nl(); continue;
    }
    const mf = FENCE.exec(L);
    if (mf && !(mf[1][0] === '`' && mf[2].includes('`'))) { fence = { ch: mf[1][0], len: mf[1].length }; hide(); prevBlank = false; table = false; continue; }
    if (defLines.has(li)) { hide(); prevBlank = true; continue; }
    if (!table && L.includes('|') && li + 1 < lines.length && isSep(raw.slice(lines[li + 1][0], lines[li + 1][1]))) table = true;
    if (table) {
      if (blank || !L.includes('|')) table = false;
      else if (isSep(L)) { hide(); continue; }
      else { tableRow(s, e); nl(); prevBlank = false; prevOdd = true; continue; }
    }
    if (/^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$/.test(L) || (!prevBlank && !prevOdd && /^ {0,3}=+[ \t]*$/.test(L))) { hide(); prevBlank = false; continue; }
    prevOdd = /^ {0,3}>/.test(L);
    // a backslash at the end of a line is a hard line break, not text
    let le = e;
    if (hasNL && raw[e - 1] === '\\') { let k = e - 1; while (k > s && raw[k - 1] === '\\') k--; if ((e - k) % 2 === 1) le = e - 1; }
    let i = s, mq;
    while ((mq = /^ {0,3}> ?/.exec(raw.slice(i, e)))) i += mq[0].length;
    let hiddenEnd = i;
    const rest = raw.slice(i, e);
    const mh = /^ {0,3}(#{1,6})(?:[ \t]+|$)/.exec(rest);
    if (mh) {
      i += mh[0].length; hiddenEnd = i;
      let ce = e;
      const mc = /(^|[ \t]+)#+[ \t]*$/.exec(raw.slice(i, e));
      if (mc) ce = i + mc.index;
      const cs = out.length;
      inline(i, ce);
      lps.push({ ls: s, pe: hiddenEnd, cs, ce: out.length, le: e });
      nl(); prevBlank = blank; continue;
    }
    const cs = out.length;
    const ml = /^([ \t]*)([-*+])([ \t]+)/.exec(rest);
    if (ml) {
      const mk = i + ml[1].length;
      emitRaw(i, mk);
      const after = mk + 1 + ml[3].length;
      const mt = /^\[([ xX])\](?=[ \t]|$)/.exec(raw.slice(after, e));
      if (mt) { emit(mt[1] === ' ' ? '☐' : '☑', mk, after + 3); inline(after + 3, le); }
      else { emit('•', mk, mk + 1); emitRaw(mk + 1, after); inline(after, le); }
    } else {
      inline(i, le);
    }
    if (hiddenEnd > s) lps.push({ ls: s, pe: hiddenEnd, cs, ce: out.length, le: e });
    nl(); prevBlank = blank;
  }
  return { out: out.join(''), A, B, groups, lps };
}

/* Source for the "마크다운 적용" view: emphasis the stripper found is turned into
   HTML tags, so Korean text like **'강조'**를 renders bold instead of showing ** */
function renderSource(raw) {
  if (!/[*_~]/.test(raw)) return raw;
  const v = stripMd(raw);
  const edits = [];
  for (const g of v.groups) if (g.tag) { edits.push([g.gs, g.rcs, g.tag[0]], [g.rce, g.ge, g.tag[1]]); }
  if (!edits.length) return raw;
  edits.sort((a, b) => a[0] - b[0]);
  const parts = []; let last = 0;
  for (const [a, b, t] of edits) { parts.push(raw.slice(last, a), t); last = b; }
  parts.push(raw.slice(last));
  return parts.join('');
}

/* Line breaks typed inside **bold**, `code` or [link text] close the markup before the
   break and reopen it after, so every line keeps its formatting. */
function wrapBreaks(raw, groups, ins) {
  if (!groups.length || !ins.includes('\n')) return ins;
  groups = groups.slice().sort((a, b) => a.gs - b.gs);
  const opens = groups.map(g => raw.slice(g.gs, g.rcs)).join('');
  const closes = groups.map(g => raw.slice(g.rce, g.ge)).reverse().join('');
  // markup must hug the text: ** goes before trailing spaces and after leading spaces
  const head = (x) => /^[ \t]*/.exec(x)[0], tail = (x) => /[ \t]*$/.exec(x)[0];
  const segs = ins.split('\n');
  const t0 = tail(segs[0]);
  let r = segs[0].slice(0, segs[0].length - t0.length) + closes + t0;
  for (let k = 1; k < segs.length; k++) {
    const seg = segs[k], h = head(seg);
    r += '\n';
    if (k === segs.length - 1) { r += h + opens + seg.slice(h.length); continue; }
    const body = seg.slice(h.length), t = tail(body), core = body.slice(0, body.length - t.length);
    r += core ? h + opens + core + closes + t : seg;
  }
  return r;
}
/* Map an edit in the stripped text [d0, d1) -> ins onto the source.
   Returns [rawStart, rawEnd, rawInsert, caretOffsetInInsert]. */
function mapEdit(raw, v, d0, d1, ins, alt = 0) {
  const S = v.out;
  if (d1 > d0 && d0 === 0 && d1 === S.length) return [0, raw.length, ins, ins.length];
  if (d1 > d0 && alt === 10) {
    // spaces typed at the edge of **bold** go outside it ("** 굵게**" would not be bold)
    let a = v.A[d0], b = v.B[d1 - 1], body = ins, pre = '', post = '';
    const lead = /^[ \t]*/.exec(ins)[0], trail = /[ \t]*$/.exec(ins)[0];
    const gs = v.groups.find(g => g.kind === 'emph' && g.rcs === a), ge = v.groups.find(g => g.kind === 'emph' && g.rce === b);
    if (ge && trail) { body = body.slice(0, body.length - trail.length); post = raw.slice(ge.rce, ge.ge) + trail; b = ge.ge; }
    if (gs && lead && body.length >= lead.length) { body = body.slice(lead.length); pre = lead + raw.slice(gs.gs, gs.rcs); a = gs.gs; }
    const insRaw = pre + body + post;
    return [a, b, insRaw, insRaw.length];
  }
  if (d1 > d0) {
    let rs = v.A[d0], re = v.B[d1 - 1];
    if (alt === 9) {
      // also take the hidden markup on both sides (a hard-break backslash, closing ##, …)
      rs = d0 > 0 ? v.B[d0 - 1] : 0; re = d1 < S.length ? v.A[d1] : raw.length;
    } else {
      // deleting everything inside **bold**, `code`, a heading… removes its markup too;
      // typing over it keeps the markup (like a word processor keeps the style)
      const wipe = ins === '' || alt === 1;
      if (wipe) for (const g of v.groups) if (g.ce > g.cs && d0 <= g.cs && g.ce <= d1) { if (g.gs < rs) rs = g.gs; if (g.ge > re) re = g.ge; }
      for (const lp of v.lps) {
        if (wipe && lp.ce > lp.cs && d0 <= lp.cs && lp.ce <= d1) { if (lp.ls < rs) rs = lp.ls; if (lp.le > re) re = lp.le; }
        if (S[d1 - 1] === '\n' && lp.cs === d1 && lp.pe > re) re = lp.pe;
      }
    }
    // a deletion that swallows only one half of a pair (the closing ** or the opening [)
    // puts that half back, so the rest of the text keeps its formatting
    const closers = [], openers = [];
    for (const g of v.groups) {
      const openIn = rs <= g.gs && g.rcs <= re, closeIn = rs <= g.rce && g.ge <= re;
      if (closeIn && !openIn) closers.push(g);
      else if (openIn && !closeIn) openers.push(g);
    }
    closers.sort((a, b) => a.rce - b.rce);
    openers.sort((a, b) => a.gs - b.gs);
    const cl = closers.map(g => raw.slice(g.rce, g.ge)).join(''), op = openers.map(g => raw.slice(g.gs, g.rcs)).join('');
    ins = wrapBreaks(raw, v.groups.filter(g => g.split && g.rcs < rs && re < g.rce), ins);
    if (alt === 2) return [rs, re, cl + ins + op, cl.length + ins.length];
    if (alt === 5) {
      // keep spaces outside the markup: "**굵은 **" is not bold, "**굵은** " is
      let a = rs, b = re, pre = '', post = '';
      if (closers.length) { let k = rs; while (k > 0 && (raw[k - 1] === ' ' || raw[k - 1] === '\t')) k--; if (k < rs && closers.every(g => k > g.rcs)) { pre = raw.slice(k, rs); a = k; } }
      if (openers.length) { let k = re; while (k < raw.length && (raw[k] === ' ' || raw[k] === '\t')) k++; if (k > re && openers.every(g => k < g.rce)) { post = raw.slice(re, k); b = k; } }
      return [a, b, cl + pre + ins + post + op, cl.length + pre.length + ins.length];
    }
    if (alt === 3) return [rs, re, cl + op + ins, cl.length + op.length + ins.length];
    return [rs, re, ins + cl + op, ins.length];
  }
  const p = d0;
  let rs;
  if (S.length === 0) rs = raw.length;
  else if (p === 0 || S[p - 1] === '\n') {
    const lineStart = p === 0 ? 0 : v.B[p - 1];
    const content = p < S.length ? v.A[p] : raw.length;
    rs = ins.endsWith('\n') ? lineStart : content;
  } else rs = v.B[p - 1];
  // text typed right after a link or `code` goes after it, not inside it
  for (let moved = true; moved;) {
    moved = false;
    for (const g of v.groups) if (g.kind !== 'emph' && g.rce === rs && g.ge > rs) { rs = g.ge; moved = true; }
  }
  const inside = v.groups.filter(g => g.split && g.rcs < rs && rs < g.rce);
  if (inside.length && ins.includes('\n')) {
    const lo = Math.max(...inside.map(g => g.rcs)), hi = Math.min(...inside.map(g => g.rce));
    let a = rs, b = rs;
    while (a > lo + 1 && (raw[a - 1] === ' ' || raw[a - 1] === '\t')) a--;
    while (b < hi - 1 && (raw[b] === ' ' || raw[b] === '\t')) b++;
    const w = wrapBreaks(raw, inside, raw.slice(a, rs) + ins + raw.slice(rs, b));
    return [a, b, w, w.length];
  }
  return [rs, rs, ins, ins.length];
}
/* Apply a stripped-view edit to the source so the result looks exactly like what was typed.
   Several placements are tried (inside or outside hidden markup); the first one whose
   stripped text matches wins. Returns {raw, view, viewCaret}. */
function resolveEdit(raw, v, d0, d1, ins) {
  const S = v.out, want = S.slice(0, d0) + ins + S.slice(d1);
  const cands = [];
  if (d1 > d0) {
    for (const alt of [0, 1, 2, 3, 5, 10, 9]) if ((alt !== 1 && alt !== 10) || ins) cands.push(mapEdit(raw, v, d0, d1, ins, alt));
  } else {
    const base = mapEdit(raw, v, d0, d1, ins, 0);
    cands.push(base);
    const lo = d0 > 0 ? v.B[d0 - 1] : 0, hi = d0 < S.length ? v.A[d0] : raw.length;
    const pts = new Set([lo, hi]);
    for (const g of v.groups) for (const x of [g.gs, g.rcs, g.rce, g.ge]) if (x >= lo && x <= hi) pts.add(x);
    for (const lp of v.lps) for (const x of [lp.ls, lp.pe]) if (x >= lo && x <= hi) pts.add(x);
    for (const x of [...pts].sort((a, b) => a - b)) if (x !== base[0] || x !== base[1]) cands.push([x, x, ins, ins.length]);
  }
  const list = raw.length > 50000 ? cands.slice(0, 3) : cands;
  const attempt = (nr, caretRaw) => ({ raw: nr, view: stripMd(nr), caretRaw });
  let first = null;
  for (const [rs, re, insRaw, off] of list) {
    const r = attempt(raw.slice(0, rs) + insRaw + raw.slice(re), rs + off);
    if (r.view.out === want) return { raw: r.raw, view: r.view, viewCaret: d0 + ins.length };
    if (!first) first = r;
  }
  // last resort: list bullets on the edited lines become plain • characters
  if (raw.length <= 50000) {
    let a = d0; while (a > 0 && S[a - 1] !== '\n') a--;
    let b = d1; while (b < S.length && S[b] !== '\n') b++;
    for (const [rs, re, insRaw, off] of list.slice(0, 3)) {
      const edits = [[rs, re, insRaw]];
      for (let i = a; i < b; i++) if ('•☐☑'.includes(S[i]) && raw.slice(v.A[i], v.B[i]) !== S[i] && (v.B[i] <= rs || v.A[i] >= re)) edits.push([v.A[i], v.B[i], S[i]]);
      if (edits.length === 1) continue;
      edits.sort((x, y) => (y[0] - x[0]) || (y[1] - x[1]));
      let nr = raw, shift = 0;
      for (const [s0, e0, t] of edits) { nr = nr.slice(0, s0) + t + nr.slice(e0); if (s0 < rs) shift += t.length - (e0 - s0); }
      const r = attempt(nr, rs + off + shift);
      if (r.view.out === want) return { raw: r.raw, view: r.view, viewCaret: d0 + ins.length };
    }
  }
  return { raw: first.raw, view: first.view, viewCaret: rawToView(first.view, first.caretRaw) };
}
function rawToView(v, pos) {
  const B = v.B; let lo = 0, hi = B.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (B[mid] > pos) hi = mid; else lo = mid + 1; }
  return lo;
}

module.exports={stripMd,mapEdit,rawToView,renderSource,resolveEdit};

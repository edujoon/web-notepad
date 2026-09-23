const { stripMd, renderSource } = require('./core.js');
const { marked } = require('/tmp/package/lib/marked.cjs');
const corpus = require('./corpus.js');
corpus.refs = "참조 링크 [참조 텍스트][ref1] 와 [ref2] 단축형 그리고 [빈][]\n\n[ref1]: https://ref.example.com\n[ref2]: https://ref2.example.com \"제목\"\n[빈]: https://e.com";
marked.use({ gfm: true, breaks: true, tokenizer: { del(src) {
  if (src[0] !== '~') return false;
  if (src[1] !== '~') return { type: 'text', raw: '~', text: '~' };
  const m = /^~~(?=[^\s~])((?:\\[\s\S]|[^\\])*?(?:\\[\s\S]|[^\s~\\]))~~(?=[^~]|$)/.exec(src);
  if (m) return { type: 'del', raw: m[0], text: m[1], tokens: this.lexer.inlineTokens(m[1]) };
  return false; } } });
// crude html -> visible text
const text = (h) => h.replace(/<br\s*\/?>/g, '\n').replace(/<img[^>]*alt="([^"]*)"[^>]*>/g, '$1').replace(/<[^>]+>/g, ' ')
  .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
const normP = (s) => s.replace(/^[ \t]*(\d+[.)])[ \t]/gm, '').replace(/[•☐☑]/g, ' ').replace(/\s+/g, '');
const normR = (s) => s.replace(/\s+/g, '');
let bad = 0;
for (const [k, raw] of Object.entries(corpus)) {
  const plain = stripMd(raw).out;
  const html = marked.parse(renderSource(raw));
  const a = normP(plain), b = normR(text(html));
  const leftover = /\*\*|__|~~|(^|[^\\])`|\]\(|<\/?(b|br|strong)>/.test(text(html).replace(/<어린 왕자>/,'')) ;
  if (a !== b) { bad++; let i = 0; while (a[i] === b[i]) i++; console.log(`[${k}] 불일치 @${i}\n  제거: …${a.slice(Math.max(0,i-15), i+25)}\n  적용: …${b.slice(Math.max(0,i-15), i+25)}`); }
  else console.log(`[${k}] 일치`);
  if (/\*\*/.test(text(html))) console.log(`  !! 적용 보기에 ** 남음`);
}
console.log('\n--- emphasis html ---\n' + marked.parse(renderSource(corpus.emphasis)));
console.log('--- misc plain ---\n' + stripMd(corpus.misc).out);
console.log('--- refs plain ---\n' + stripMd(corpus.refs).out);

const { stripMd, resolveEdit } = require('./core.js');
function edit(raw, find, ins, opts = {}) { // select `find` in the stripped view (or caret at index) and type ins
  const v = stripMd(raw); let d0, d1;
  if (typeof find === 'number') { d0 = d1 = find; } else { d0 = v.out.indexOf(find); d1 = d0 + find.length; if (opts.at === 'end') d0 = d1; if (opts.at === 'start') d1 = d0; }
  if (d0 < 0) throw new Error('not found ' + find);
  const r = resolveEdit(raw, v, d0, d1, ins);
  const want = v.out.slice(0, d0) + ins + v.out.slice(d1);
  return { raw: r.raw, view: r.view.out, ok: r.view.out === want };
}
const cases = [
  ['굵은 글자 끝에 이어 쓰기', '**중요**', '중요', '한', { at: 'end' }],
  ['굵은 글자 덮어쓰기', '앞 **중요** 뒤', '중요', '핵심'],
  ['굵은 글자 통째로 지우기', '앞 **중요** 뒤', '중요', ''],
  ['굵은 글자 중간 Enter', '**굵은 글씨**', '굵은 ', '\n', { at: 'end' }],
  ['링크 끝에 이어 쓰기(링크 밖으로)', '[문서](https://a.com)를', '문서', '들', { at: 'end' }],
  ['코드 끝에 이어 쓰기(코드 밖으로)', '`npm`으로', 'npm', ' 명령', { at: 'end' }],
  ['제목 줄 앞에서 Enter', '앞\n## 제목', '제목', '\n', { at: 'start' }],
  ['제목 줄 합치기(Backspace)', '앞\n## 제목', '\n', ''],
  ['제목 내용 모두 지우기', '## 제목\n본문', '제목\n', ''],
  ['목록 글머리 앞에 입력', '- 항목', 0, '앗'],
  ['목록 줄 합치기', '문단\n- 항목', '\n', ''],
  ['표 칸 사이 탭 지우기', '| a | b |\n|---|---|\n| 1 | 2 |', '1\t', '1'],
  ['표 칸 내용 바꾸기', '| a | b |\n|---|---|\n| 1 | 2 |', '2', '둘'],
  ['마크다운 섞인 글 붙여넣기', '앞 뒤', '앞 ', '**굵게** 와 `코드`', { at: 'end' }],
  ['인용문 안에 쓰기', '> 인용', '인용', '문', { at: 'end' }],
  ['<br> 지우기', '줄1<br>줄2', '\n', ''],
  ['취소선 안에서 Enter', '~~취소 선~~', '취소', '\n', { at: 'end' }],
  ['굵게 일부+뒤 지우기', '**굵은 글씨** 그리고', '글씨 그리', ''],
];
for (const [name, raw, find, ins, opts] of cases) {
  const r = edit(raw, find, ins, opts);
  console.log(`${r.ok ? '✅' : '❌'} ${name}\n     원본 ${JSON.stringify(raw)} → ${JSON.stringify(r.raw)}\n     화면 ${JSON.stringify(r.view)}`);
}

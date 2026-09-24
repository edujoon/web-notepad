# 웹 메모장

마크다운이 섞인 글을 세 가지 방식으로 보고 편집하고 복사할 수 있는 정적 웹 메모장입니다. 이 앱을 체험한 사람이 실제 소스와 제작 요청문을 ChatGPT로 가져가, 별도 배포 전에 Canvas 또는 HTML·React 미리보기에서 같은 기능의 앱을 바로 실행하도록 구성했습니다. 원본 단일 HTML 앱은 일반 브라우저와 Vercel에서도 계속 독립적으로 실행됩니다.

- 배포 주소: [https://web-notepad-psi.vercel.app](https://web-notepad-psi.vercel.app)
- 사용자 안내: [웹 메모장 사용 가이드](web-notepad/USAGE.md)

## 주요 기능

- 탭으로 여러 메모 작성·이름 변경·삭제
- 입력 후 자동 저장과 새로고침 복원
- **서식 제거 텍스트**, **마크다운 원본**, **서식 적용 화면**의 세 가지 보기
- 보기 방식에 맞춘 전체 복사
- `.txt`, `.md`, `.markdown` 파일 열기
- 서식 제거 텍스트 `.txt` 및 마크다운 원본 `.md` 저장
- 실행 취소·다시 실행, 찾기·바꾸기, 줄 이동
- 자동 줄 바꿈, 기본/고정폭 글꼴, 50–300% 확대·축소
- 시스템 설정을 따르는 라이트·다크 테마와 모바일 반응형 화면
- 마지막 메모 탭 바로 뒤에서 함께 스크롤되는 **+** 새 메모 버튼
- HTML 안에 포함된 📋 SVG data URL 파비콘
- **앱 복제**에서 ChatGPT 미리보기용 자체 포함 HTML과 제작 요청문 복사·다운로드

## 앱 복제

화면 오른쪽 위의 **앱 복제**를 누르면 별도 배포 없이 ChatGPT 안에서 조작할 수 있는 앱 미리보기를 요청할 수 있습니다.

1. **코드와 프롬프트 복사**를 누르거나 **복제 파일 다운로드**로 UTF-8 텍스트 파일을 받습니다.
2. ChatGPT에 내용을 붙여 넣거나 다운로드한 파일을 첨부합니다.
3. 추가 설정 질문 없이 원본 설정을 유지한 **앱 미리보기 생성**을 요청합니다.

**ChatGPT 열기**는 [chatgpt.com](https://chatgpt.com)을 새 탭으로 엽니다. 복제 자료에는 정적 앱 소스, 기본 `USAGE.md`, `marked`와 `DOMPurify`가 함께 들어갑니다. Google Fonts는 시스템 글꼴 스택으로 바뀌며, 원본 사이트나 CDN을 다시 요청하지 않아도 실행됩니다. 화면 DOM을 캡처하거나 `localStorage`를 읽지 않으므로 사용자가 작성한 메모, 제목, 화면 설정은 포함되지 않습니다.

복제본도 같은 정적 템플릿을 내부에 보관하므로 현재 주소에서 HTML을 다시 가져오지 않고 재복제할 수 있습니다. 브라우저 저장소가 차단된 미리보기에서는 메모를 현재 세션의 메모리에만 유지하고, 상태 표시줄에 창을 닫으면 사라진다고 표시합니다. 클립보드나 다운로드가 차단되면 해당 동작만 실패 안내를 보여 주고 편집·탭·미리보기는 계속 작동합니다.

## 프로젝트 구조

```text
.
├── README.md                 GitHub 프로젝트 설명
├── vercel.json               Vercel 진입 경로 설정
└── web-notepad/
    ├── notepad.html          웹앱 본체
    ├── USAGE.md              첫 사용 시 생성되는 안내 메모 원본
    ├── LICENSE               MIT 라이선스 전문
    ├── vendor/               복제본에 포함할 라이브러리와 라이선스
    ├── demo/
    │   └── notepad-demo.html Claude 체험판용 생성 결과
    ├── docs/
    │   └── HANDOVER.md       유지보수 인수인계 문서
    └── tools/                배포용·체험판 생성 및 테스트 도구
```

앱 본체는 HTML·CSS·JavaScript가 한 파일에 들어 있는 정적 페이지입니다. React나 Vite는 필요하지 않습니다. 소스 또는 `USAGE.md`를 수정한 뒤에는 다음 명령으로 안내문과 자체 포함 복제 템플릿을 배포용 HTML에 갱신합니다.

```bash
python web-notepad/tools/build_app.py
python web-notepad/tools/build_demo.py
```

원본 화면은 마크다운 미리보기에 jsDelivr의 `marked` 12.0.2와 `DOMPurify` 3.2.6을 사용하고, Google Fonts를 불러옵니다. 복제본은 같은 버전의 배포 파일을 라이선스 헤더와 함께 HTML에 직접 포함하고 시스템 글꼴을 사용합니다. 전체 라이선스는 `web-notepad/vendor/`에 보존합니다.

## 로컬 실행

저장소 루트에서 정적 파일 서버를 실행합니다.

```bash
npx --yes serve .
```

터미널에 표시된 포트를 확인한 뒤 다음 주소를 엽니다.

```text
http://localhost:3000/web-notepad/notepad.html
```

Python이 설치되어 있다면 다음 방법도 사용할 수 있습니다.

```bash
python -m http.server 8000
```

```text
http://localhost:8000/web-notepad/notepad.html
```

일반적인 브라우저 동작 검증에는 `file://`보다 정적 서버를 권장합니다. 다만 빌드된 원본과 복제본은 첫 사용 가이드와 복제 템플릿을 내부에 포함하므로, 앱 복제를 위해 현재 주소나 원본 사이트의 HTML을 다시 불러오지는 않습니다.

## Vercel 배포

현재 Vercel 프로젝트는 GitHub 저장소의 `main` 브랜치와 연결되어 있습니다. `main`에 푸시하면 프로덕션 배포가 자동으로 생성됩니다.

직접 배포하려면 저장소 루트에서 실행합니다.

```bash
npx vercel --prod
```

별도의 빌드 명령, 출력 폴더, 비밀키 또는 환경변수는 필요하지 않습니다. [vercel.json](vercel.json)이 `/`를 `web-notepad/notepad.html`에 연결하고 `/USAGE.md`를 안내 문서에 연결합니다.

## 저장 방식

Vercel 배포에서는 메모와 화면 설정을 브라우저의 `localStorage`에 저장합니다.

- 메모는 해당 도메인과 브라우저 프로필 안에서만 보입니다.
- 다른 사용자, 다른 브라우저 또는 다른 기기와 공유·동기화되지 않습니다.
- 브라우저의 사이트 데이터를 지우거나 시크릿 창을 닫으면 메모가 사라집니다.
- 처음 방문했고 기존 메모 기록이 없을 때만 `USAGE.md`가 안내 메모로 생성됩니다.
- 기존 메모가 있으면 안내 메모를 추가하거나 내용을 덮어쓰지 않습니다.
- 안내 메모를 수정하거나 삭제하면 그 상태가 유지되며 다시 자동 생성되지 않습니다.
- 메모 하나는 저장 데이터 기준 약 250KB까지 지원하며, 전체 용량은 브라우저의 localStorage 한도를 따릅니다.
- 앱 복제 자료에는 `localStorage`의 메모·제목·설정이 들어가지 않습니다.
- 미리보기에서 `localStorage`가 차단되면 앱은 중단되지 않고 메모를 현재 세션 메모리에만 유지하며, 영구 저장으로 표시하지 않습니다.

Claude 아티팩트 안에서 `window.claude`의 `db`와 `downloads` 기능을 사용할 수 있으면 기존 실시간 DB 저장과 Claude 파일 저장 기능을 우선 사용합니다. 일반 브라우저에서는 localStorage와 브라우저 다운로드로 자동 전환됩니다.

## 제한 사항

- Vercel 버전은 서버 계정이나 동기화 기능이 없는 개인 브라우저용 메모장입니다.
- 원본 Vercel 화면에서 Google Fonts 또는 jsDelivr가 차단되면 기본 글꼴이나 단순 마크다운 표시로 대체될 수 있습니다. 자체 포함 복제본은 이 외부 런타임 요청을 사용하지 않습니다.
- 메뉴를 통한 붙여넣기는 브라우저 권한에 따라 제한될 수 있으며, 이때는 `Ctrl+V` 또는 `⌘V`를 사용해야 합니다.
- 표의 행·열 구조 편집은 마크다운 원본 보기에서 하는 것이 안전합니다.
- ChatGPT의 Canvas 및 HTML·React 미리보기 제공 여부와 브라우저 권한은 계정·클라이언트·실행 환경에 따라 달라질 수 있습니다. 지원되지 않는 환경에서는 프롬프트가 성공을 가장하지 않고 제한을 밝히도록 작성되어 있습니다.

## 라이선스와 출처

원본 웹앱 제작자: **JOON** · [eduedujoon@gmail.com](mailto:eduedujoon@gmail.com)<br>
원본 제작일: 2026. 9. 22.<br>
저장소: [edujoon/web-notepad](https://github.com/edujoon/web-notepad)

이 프로젝트는 [MIT License](web-notepad/LICENSE)로 공개됩니다. 소스 파일 상단의 제작자·저작권·라이선스 표기를 유지합니다. 복제 HTML에 포함되는 `marked`와 `DOMPurify`의 원 저작권 및 라이선스 고지도 함께 유지됩니다.

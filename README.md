# 웹 메모장

마크다운이 섞인 글을 세 가지 방식으로 보고 편집하고 복사할 수 있는 정적 웹 메모장입니다. 이 앱을 직접 체험한 사람이 실제 소스와 제작 요청문을 ChatGPT로 가져가, 같은 기능을 바탕으로 자신만의 웹앱을 쉽게 만들 수 있도록 구성했습니다. Claude 아티팩트에서 만든 단일 HTML 앱은 일반 브라우저와 Vercel에서도 독립적으로 실행됩니다.

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
- **앱 복제**에서 실행 가능한 전체 HTML과 ChatGPT 제작 요청문 복사·다운로드

## 앱 복제

화면 오른쪽 위의 **앱 복제**를 누르면 다음 순서로 자신만의 앱 제작을 요청할 수 있습니다.

1. **코드와 프롬프트 복사**를 누르거나 **복제 파일 다운로드**로 UTF-8 텍스트 파일을 받습니다.
2. ChatGPT에 내용을 붙여 넣거나 다운로드한 파일을 첨부합니다.
3. 추가 설정 질문 없이 원본 설정을 유지한 앱 생성을 요청합니다.

**ChatGPT 열기**는 [chatgpt.com](https://chatgpt.com)을 새 탭으로 엽니다. 복제 자료는 현재 페이지의 정적 HTML 원본과 기본 `USAGE.md`만 사용합니다. 화면 DOM을 캡처하거나 `localStorage`를 읽지 않으므로 사용자가 작성한 메모, 메모 제목, 화면 설정은 포함되지 않습니다. `USAGE.md`는 추출 HTML 안에 삽입되므로 다른 주소에 배포해도 첫 사용 안내가 상대 경로 때문에 깨지지 않으며, 추출된 앱에도 마지막 탭 뒤의 새 메모 버튼, 📋 파비콘과 앱 복제 기능이 남습니다.

## 프로젝트 구조

```text
.
├── README.md                 GitHub 프로젝트 설명
├── vercel.json               Vercel 진입 경로 설정
└── web-notepad/
    ├── notepad.html          웹앱 본체
    ├── USAGE.md              첫 사용 시 생성되는 안내 메모 원본
    ├── LICENSE               MIT 라이선스 전문
    ├── demo/
    │   └── notepad-demo.html Claude 체험판용 생성 결과
    ├── docs/
    │   └── HANDOVER.md       유지보수 인수인계 문서
    └── tools/                체험판 생성 및 테스트 도구
```

앱 본체는 HTML·CSS·JavaScript가 한 파일에 들어 있는 정적 페이지입니다. React, Vite, 별도 패키지 설치 또는 빌드 단계가 필요하지 않습니다.

마크다운 미리보기에는 jsDelivr에서 불러오는 `marked`와 `DOMPurify`를 사용하고, 글꼴은 Google Fonts의 IBM Plex Sans KR과 Nanum Gothic Coding을 사용합니다.

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

`file://`로 직접 열기보다 정적 서버를 권장합니다. 저장소 원본은 첫 안내 메모를 같은 출처의 `web-notepad/USAGE.md`에서 읽고, 앱 복제 자료를 만들 때 현재 주소의 정적 HTML 원본을 불러오기 때문입니다. 앱 복제로 추출한 단일 HTML은 안내문을 내부에 포함하지만, 다시 앱 복제하려면 그 파일도 정적 서버에서 여는 것이 안전합니다.

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

Claude 아티팩트 안에서 `window.claude`의 `db`와 `downloads` 기능을 사용할 수 있으면 기존 실시간 DB 저장과 Claude 파일 저장 기능을 우선 사용합니다. 일반 브라우저에서는 localStorage와 브라우저 다운로드로 자동 전환됩니다.

## 제한 사항

- Vercel 버전은 서버 계정이나 동기화 기능이 없는 개인 브라우저용 메모장입니다.
- Google Fonts 또는 jsDelivr가 차단되면 기본 글꼴이나 단순 마크다운 표시로 대체될 수 있습니다.
- 메뉴를 통한 붙여넣기는 브라우저 권한에 따라 제한될 수 있으며, 이때는 `Ctrl+V` 또는 `⌘V`를 사용해야 합니다.
- 표의 행·열 구조 편집은 마크다운 원본 보기에서 하는 것이 안전합니다.
- 앱 복제 후 ChatGPT가 생성한 결과는 사용자가 별도로 검토·실행·배포해야 하며, 이 저장소는 ChatGPT 계정이나 생성 결과를 자동으로 확인하지 않습니다.

## 라이선스와 출처

원본 웹앱 제작자: **JOON** · [eduedujoon@gmail.com](mailto:eduedujoon@gmail.com)<br>
원본 제작일: 2026. 9. 22.<br>
저장소: [edujoon/web-notepad](https://github.com/edujoon/web-notepad)

이 프로젝트는 [MIT License](web-notepad/LICENSE)로 공개됩니다. 소스 파일 상단의 제작자·저작권·라이선스 표기를 유지합니다.

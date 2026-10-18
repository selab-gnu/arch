# Spec Kit × Codex 가이드 (Windows) — Windows PC에서 Codex CLI로 하는 스펙 주도 개발

> 이 문서는 [GUIDE-codex.md](GUIDE-codex.md)(macOS/Linux)와 **같은 할 일 앱을 같은 순서로** 만들되, **Windows 10/11 PC** 에서 하는 방법을 안내한다.
> SDD 개념과 각 문서의 자세한 설명은 [GUIDE.md](GUIDE.md), Codex에서 달라지는 점(`$speckit-…`, 샌드박스 권한)은 [GUIDE-codex.md 개념](GUIDE-codex.md#개념--claude-code-버전과-무엇이-다른가) 과 같다. 여기서는 **Windows에서 달라지는 설치·실행·명령**을 중심으로 처음부터 끝까지 따라 할 수 있게 정리했다.
> 검증 기준: `specify-cli` **v1.1.3** · `specify init --integration codex --script ps` · Codex CLI (Windows 네이티브) · Windows 11 + PowerShell 7

---

# 개념 — macOS 버전과 무엇이 다른가

Spec Kit 단계(`$speckit-constitution` … `$speckit-converge`)와 산출물(`.specify/`, `.agents/skills/`, `specs/001-…/`)은 **macOS와 똑같다.** 달라지는 것은 다음이다.

| 항목 | macOS ([GUIDE-codex.md](GUIDE-codex.md)) | **Windows (이 문서)** |
| --- | --- | --- |
| 터미널 | 터미널 앱 (zsh) | **Windows Terminal + PowerShell 7** (권장) |
| 도구 설치 | `brew install …` | **`winget install …`** |
| 자동화 스크립트 | `--script sh` → `.specify/scripts/bash/*.sh` | **`--script ps`** → `.specify/scripts/powershell/*.ps1` |
| 스크립트 실행 허용 | 필요 없음 | **PowerShell 실행 정책** 설정 필요 (`RemoteSigned`) |
| Codex 샌드박스 | macOS 기본 샌드박스 | 처음 실행 때 **Windows 샌드박스 설정** (관리자 권한 1회) |
| 프로젝트 위치 | `~/git/my-todo-codex` | `C:\Users\<내 이름>\git\my-todo-codex` (`$HOME\git\my-todo-codex`) |
| 파이썬 실행 | `python3` | **`py`** (Python 런처) |
| 웹 서버 | `python3 -m http.server 8000` | **`py -m http.server 8000`** |
| 숨김 폴더 보기 | `ls -a`, Finder `⌘ + Shift + .` | `Get-ChildItem -Force` (`ls -Force`), 탐색기 **보기 › 표시 › 숨긴 항목** |
| 단축키 | `⌘` | `Ctrl` (개발자 도구 `F12`) |

> 💡 **WSL(리눅스)을 이미 쓰고 있다면** WSL 안의 Ubuntu에서 [GUIDE-codex.md](GUIDE-codex.md)(macOS/Linux 버전)를 그대로 따라 해도 된다. 처음이라면 이 문서의 **Windows 네이티브** 방식이 설치할 것이 적다.

## 이 가이드의 단계

| 단계 | 내용 | 사용하는 명령 |
| --- | --- | --- |
| 1 | 설치 — 준비 도구, Codex CLI, specify CLI, 프로젝트 초기화 | `winget`, `npm i -g @openai/codex`, `specify init --integration codex --script ps` |
| 2 | Codex 실행 — 샌드박스 설정, 로그인, 폴더 신뢰, 권한, 스킬 확인 | `codex`, `/permissions`, `/skills` |
| 3 | 헌법 | `$speckit-constitution` |
| 4 | 명세 | `$speckit-specify` |
| 5 | 명확화 | `$speckit-clarify` |
| 6 | 계획 (+ 체크리스트) | `$speckit-plan`, `$speckit-checklist` |
| 7 | 작업 분해와 일관성 점검 | `$speckit-tasks`, `$speckit-analyze` |
| 8 | 구현과 수렴 | `$speckit-implement`, `$speckit-converge` |
| 9 | (도전) 두 번째 기능 — 마감일 | 4~8단계 반복 |

| 표시 | 하는 곳 |
| --- | --- |
| 🖥️ **PowerShell** | Windows Terminal 의 PowerShell 탭 (Codex 밖) |
| 🛡️ **관리자 PowerShell** | 시작 메뉴에서 "Terminal" 오른쪽 클릭 → **관리자로 실행** (1단계 일부만) |
| 🤖 **Codex** | `codex` 를 실행한 화면의 입력창 |

---

# 1 단계: 설치 — 준비 도구, Codex CLI, specify CLI, 프로젝트 초기화

**목적** — Windows에 필요한 도구를 설치하고, Codex가 Spec Kit 스킬을 쓸 수 있는 프로젝트를 만든다.

### 1-1. 준비 도구 설치 (winget)

🖥️ **PowerShell** — 이미 설치된 것은 건너뛴다. 설치 중 "원본 계약 조건에 동의하십니까?" 가 나오면 `Y`.

```powershell
winget install --id Microsoft.WindowsTerminal -e     # Windows 11 은 기본 설치되어 있음
winget install --id Microsoft.PowerShell -e          # PowerShell 7 (pwsh)
winget install --id Git.Git -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Python.Python.3.12 -e
winget install --id astral-sh.uv -e
```

설치가 끝나면 **Windows Terminal 을 완전히 닫고 다시 연다**(새 PATH 반영). 위쪽 탭의 ∨ 메뉴에서 **PowerShell**(검은 아이콘, 7.x)을 고른다. 매번 쓰려면 Terminal **설정 › 시작 › 기본 프로필** 을 PowerShell 로 바꾼다.

```powershell
$PSVersionTable.PSVersion   # 7.x
git --version
node --version              # v22 이상
py --version                # Python 3.12.x
uv --version
```

### 1-2. PowerShell 스크립트 실행 허용

Spec Kit 은 Windows에서 `.ps1` 스크립트로 기능 폴더를 만들고 검사한다. Windows 기본 설정은 스크립트 실행을 막을 수 있으므로 **내 계정에만** 허용한다.

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
Get-ExecutionPolicy -List      # CurrentUser 가 RemoteSigned 면 OK
```

> `RemoteSigned` 는 "내 컴퓨터에서 만든 스크립트는 실행, 인터넷에서 받은 스크립트는 서명된 것만" 이라는 뜻이다. 관리자 권한이 필요 없다.

### 1-3. Codex CLI 설치

```powershell
# 방법 A: npm (1-1 에서 Node.js 설치함)
npm install -g @openai/codex

# 방법 B: 공식 설치 스크립트
powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"

codex --version
```

### 1-4. specify CLI 설치

```powershell
uv tool install specify-cli
uv tool update-shell            # specify 를 PATH 에 추가 (처음 한 번)
```

**Terminal 을 닫고 다시 연 뒤**:

```powershell
specify version
```

### 1-5. 프로젝트 초기화 (Codex + PowerShell 스크립트)

```powershell
New-Item -ItemType Directory -Force "$HOME\git" | Out-Null
Set-Location "$HOME\git"
specify init my-todo-codex --integration codex --script ps
Set-Location my-todo-codex
```

| 옵션 | 의미 |
| --- | --- |
| `--integration codex` | Codex용 스킬을 `.agents\skills\` 에 설치 |
| `--script ps` | 자동화 스크립트를 **PowerShell** 버전으로 (Windows 기본값이지만 명시한다) |

### 1-6. git 확장과 git 저장소

```powershell
specify extension add git

git config --global user.name  "홍길동"            # 처음 한 번 (이미 했다면 건너뜀)
git config --global user.email "me@example.com"
git init
git add -A
git commit -m "chore: init Spec Kit for Codex (Windows)"
```

> 💡 Codex 샌드박스는 `.git` 폴더 쓰기를 보호한다. 저장소는 이렇게 PowerShell에서 미리 만들어 두는 것이 편하다.

## 규칙

- 모든 명령은 **일반 PowerShell** 에서 한다. 관리자 권한은 2단계의 샌드박스 설정 때 한 번만 필요하다.
- 프로젝트는 `C:\Users\<내 이름>\git\` 아래에 둔다. **OneDrive로 동기화되는 폴더(문서, 바탕 화면)는 피한다** — 동기화가 파일을 잠가 스크립트나 git이 실패할 수 있다.
- `specify init` 은 `codex` 명령이 있는지 검사한다. `codex not found` 가 나오면 1-3 을 하고 Terminal 을 다시 연다.
- 경로를 직접 입력할 때 Windows는 `\` 를 쓴다. 다만 Codex 대화나 Spec Kit 문서 안에서는 `src/todo.js` 처럼 `/` 로 써도 된다.

## 산출물

```
C:\Users\<내 이름>\git\my-todo-codex\
├── .git\
├── .agents\
│   └── skills\
│       ├── speckit-constitution\SKILL.md   … speckit-converge\SKILL.md   (기본 10개)
│       └── speckit-git-*\SKILL.md                                       (git 확장 5개)
└── .specify\
    ├── integration.json                    ("integration": "codex")
    ├── init-options.json                   ("script": "ps")
    ├── memory\constitution.md
    ├── scripts\powershell\                 check-prerequisites.ps1, create-new-feature.ps1,
    │                                       setup-plan.ps1, setup-tasks.ps1, common.ps1 …
    ├── templates\  workflows\
    └── extensions.yml  extensions\git\scripts\powershell\*.ps1
```

## 체크리스트

- [ ] `codex --version`, `specify version`, `node --version`, `py --version` 이 모두 출력된다.
- [ ] `Get-ExecutionPolicy -Scope CurrentUser` 가 `RemoteSigned` 다.
- [ ] `Get-ChildItem -Force` 에 `.agents`, `.specify`, `.git` 이 보인다.
- [ ] `(Get-ChildItem .agents\skills).Count` 가 15 다.
- [ ] `Get-Content .specify\init-options.json` 에 `"script": "ps"` 가 있다.
- [ ] `git log --oneline` 에 첫 커밋이 있다.

---

# 2 단계: Codex 실행 — 샌드박스 설정, 로그인, 폴더 신뢰, 권한, 스킬 확인

**목적** — 프로젝트 폴더에서 Codex를 처음 열고, Windows 샌드박스를 설정한 뒤 Spec Kit 스킬이 보이는지 확인한다.

**입력** — 🖥️ **PowerShell** (`my-todo-codex` 안에서)

```powershell
Set-Location "$HOME\git\my-todo-codex"
codex
```

### 2-1. Windows 샌드박스 설정 (처음 한 번)

Windows에서 처음 실행하면 다음과 같은 안내가 나온다.

```
Set up the Codex agent sandbox to protect your files and control network access.

› Set up default sandbox (requires Administrator permissions)      ← 권장
  Use non-admin sandbox (higher risk if prompt injected)
  Quit
```

1. **Set up default sandbox** 를 고른다.
2. Windows **사용자 계정 컨트롤(UAC)** 창 "이 앱이 디바이스를 변경하도록 허용하시겠어요?" → **예**.
3. `Setting up sandbox...` 가 끝나면 다음 화면으로 넘어간다.

> 관리자 권한을 쓸 수 없는 PC(학교·회사 PC)라면 **Use non-admin sandbox** 를 고른다. 실습은 진행되지만 보호 수준이 낮다. 나중에 관리자 권한이 생기면 🤖 `/setup-default-sandbox` 로 다시 설정할 수 있다.

### 2-2. 로그인 (처음 한 번)

**Sign in with ChatGPT** → 브라우저에서 ChatGPT 계정으로 로그인하고 허용한다.

### 2-3. 폴더 신뢰

`Trust this folder?` → **Trust and continue**.

### 2-4. 권한 모드 확인

🤖 **Codex**

```text
/permissions
```

**Default** 로 둔다. (작업 폴더 안 읽기·쓰기·명령 실행은 자동, 인터넷·폴더 밖·`.git`·`.agents` 쓰기는 승인 필요)

### 2-5. 스킬 확인

🤖 **Codex**

```text
/skills
```

또는 입력창에 `$speckit` 까지 입력해 자동 완성 목록을 본다.

## 규칙

- 반드시 **프로젝트 폴더 안에서** `codex` 를 실행한다.
- Codex는 Windows에서 명령을 **PowerShell** 로 실행한다. 진행 중 `.specify\scripts\powershell\….ps1` 이 실행되는 것이 보이면 정상이다.
- git 확장이 브랜치를 만들거나 커밋하려 하면(`.git` 쓰기) 승인 질문이 나온다. `git …` 명령이면 허용한다.
- 한글 입력: Codex 입력창에 한글을 칠 때 글자가 깨지거나 조합이 어색하면, 메모장 등에서 쓴 뒤 **붙여 넣기(Ctrl + V)** 한다.

## 산출물

- Codex 설정·로그인 정보 — `C:\Users\<내 이름>\.codex\` (프로젝트 폴더가 아님)
- `/skills` 목록에 `speckit-*` 15개

## 체크리스트

- [ ] 샌드박스 설정이 끝났다 (또는 non-admin 샌드박스를 선택했다).
- [ ] `/status` 의 작업 폴더가 `C:\Users\<내 이름>\git\my-todo-codex` 다.
- [ ] `$speckit` 입력 시 Spec Kit 스킬이 자동 완성된다.
- [ ] `/permissions` 가 **Default** 다.

---

# 3 단계: 헌법 — `$speckit-constitution`

**목적** — 모든 단계가 검사 기준으로 삼을 프로젝트 원칙을 정한다. (자세한 규칙: [GUIDE.md 2단계](GUIDE.md#2-단계-헌법constitution--프로젝트-원칙-정하기))

**입력** — 🤖 Codex

```text
$speckit-constitution 이 프로젝트는 초보자 학습용 할 일 관리 웹 앱이다. 다음 원칙을 정해 줘.
1) 단순성: 빌드 도구나 프레임워크 없이 순수 HTML/CSS/JavaScript만 사용한다.
2) 테스트 우선: 핵심 로직은 순수 함수로 분리하고, Node.js 내장 테스트 러너(node --test)로 먼저 테스트를 작성한다.
3) 접근성: 모든 기능은 키보드만으로 사용할 수 있어야 한다.
4) 개인정보 보호: 데이터는 브라우저 localStorage에만 저장하고 외부로 전송하지 않는다.
5) 문서와 화면 문구는 한국어로 작성한다.
```

## 규칙

- 원칙은 "반드시 ~한다 / ~하지 않는다" 처럼 **검증 가능한 문장**으로.
- git 확장의 `speckit.git.initialize` 훅이 먼저 돌지만, 1-6 에서 저장소를 만들었으므로 건너뛴다.
- 진행 중에 Codex가 실행하는 명령(`.specify\scripts\powershell\….ps1`)이 화면에 보인다. 작업 폴더 안 명령이라 Default 모드에서는 승인 없이 실행된다.

## 산출물

- `.specify/memory/constitution.md` — 자리표시자가 모두 채워지고 맨 위에 Sync Impact Report, 아래에 `Version 1.0.0`

## 체크리스트

- [ ] `constitution.md` 에 `[PROJECT_NAME]` 같은 자리표시자가 남아 있지 않다.
- [ ] 원칙 5개가 모두 반영되었고 버전·날짜가 있다.
- [ ] 🖥️ PowerShell `git status` 로 `constitution.md` 가 바뀐 것을 확인했다. (git 확장이 커밋을 제안하면 승인)

---

# 4 단계: 명세 — `$speckit-specify`

**목적** — 만들 기능을 "무엇을·왜" 로만 설명해 기능 명세를 만든다. (자세한 규칙: [GUIDE.md 3단계](GUIDE.md#3-단계-명세specify--무엇을-왜-만드는가))

**입력** — 🤖 Codex (새 대화로 시작하면 깔끔하다)

```text
/new
```

```text
$speckit-specify 혼자 쓰는 간단한 할 일 관리 앱을 만들고 싶다. 사용자는 할 일을 입력해 목록에 추가하고, 완료 여부를 체크하거나 해제하고, 필요 없는 할 일을 삭제할 수 있다. 목록은 '전체 / 진행 중 / 완료'로 걸러 볼 수 있고, 남은 할 일 개수가 항상 보인다. 페이지를 새로 고치거나 브라우저를 다시 열어도 목록이 그대로 남아 있어야 한다. 로그인이나 여러 사용자 기능은 이번 범위가 아니다.
```

## 규칙

- 기술 스택(HTML, localStorage …)은 쓰지 않는다. 5단계(plan)에서 정한다.
- git 확장의 `speckit.git.feature` 훅이 **브랜치 `001-todo-list-app`** 을 만든다. 이때 `.git` 쓰기 **승인 질문이 나오면 허용**한다.
- `[NEEDS CLARIFICATION]` 질문이 나오면 선택지 기호(A/B/C)로 짧게 답한다.

## 산출물

```
specs/001-todo-list-app/        ← 이름은 Codex가 정하므로 조금 다를 수 있다
├── spec.md
└── checklists/requirements.md
.specify/feature.json           ← "feature_directory": "specs/001-todo-list-app"
```

## 체크리스트

- [ ] `specs/001-…/spec.md` 가 생겼고, 구현 용어(HTML, JavaScript, localStorage)가 없다.
- [ ] 사용자 스토리마다 우선순위(P1~)와 Given/When/Then 인수 조건이 있다.
- [ ] 🖥️ PowerShell `git branch` 에 `* 001-…` 이 보인다. (승인을 거절했다면 브랜치 없이 진행해도 SDD는 동작한다)

---

# 5 단계: 명확화 — `$speckit-clarify`

**목적** — 계획 전에 명세의 빈틈을 Codex가 질문하고 답을 명세에 반영한다. (자세한 규칙: [GUIDE.md 4단계](GUIDE.md#4-단계-명확화clarify--모호함-없애기))

**입력** — 🤖 Codex

```text
$speckit-clarify 할 일 입력 규칙(빈 값, 최대 길이, 중복 허용 여부)과 삭제할 때 확인 절차를 중심으로 확인해 줘.
```

질문이 하나씩(최대 5개) 나오면 짧게 답한다.

| 질문 예 | 이 실습의 답 |
| --- | --- |
| 최대 길이는? | `B` (200자) |
| 공백만 입력하면? | 추가하지 않고 안내 |
| 같은 내용 중복은? | 허용하고 안내 |
| 삭제 확인 대화상자는? | 띄우지 않는다 |

그만하려면 `done`.

## 체크리스트

- [ ] `spec.md` 에 `## Clarifications` → `### Session 날짜` 가 생겼다.
- [ ] `[NEEDS CLARIFICATION` 이 남아 있지 않다.

---

# 6 단계: 계획 — `$speckit-plan` (+ `$speckit-checklist`)

**목적** — 기술 스택과 구조를 정하고, 헌법을 어기지 않는지 검사한다. (자세한 규칙: [GUIDE.md 5단계](GUIDE.md#5-단계-계획plan--어떻게-만들-것인가))

**입력** — 🤖 Codex

```text
$speckit-plan 빌드 도구 없이 순수 HTML, CSS, JavaScript(ES 모듈)로 만든다. 화면은 index.html 하나다. 할 일 데이터를 다루는 로직은 src/todo.js 의 순수 함수로, 저장은 src/storage.js 에서 localStorage를 사용하고, 화면 그리기와 이벤트 처리는 src/app.js 가 맡는다. 테스트는 tests/todo.test.js 에 Node.js 내장 테스트 러너(node --test)로 작성하고, package.json 에는 "type": "module" 만 지정하며 외부 의존성은 두지 않는다. 로컬 실행은 py -m http.server 로 한다.
```

(선택)

```text
$speckit-checklist 사용자 경험(UX)과 데이터 보존 요구사항이 빠짐없고 명확한지 점검하는 체크리스트를 만들어 줘.
```

## 규칙

- Codex가 "최신 정보를 찾아보겠다"며 **인터넷 접근 승인**을 물을 수 있다. 이 계획은 외부 라이브러리가 없으므로 **거절해도 된다.**
- `plan.md` 의 **Constitution Check** 가 모두 PASS 인지 확인한다.

## 산출물

`specs/001-…/` 에 `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, (있으면) `contracts/`, `checklists/ux.md`

## 체크리스트

- [ ] Technical Context 에 `NEEDS CLARIFICATION` 이 없다.
- [ ] Constitution Check 가 PASS 이거나 위반 사유가 Complexity Tracking 에 있다.
- [ ] Project Structure 에 `index.html`, `src/todo.js`, `src/storage.js`, `src/app.js`, `tests/todo.test.js` 가 있다.

---

# 7 단계: 작업 분해와 일관성 점검 — `$speckit-tasks`, `$speckit-analyze`

**목적** — 설계를 실행 가능한 작업 목록으로 쪼개고, 구현 전에 문서 간 모순을 점검한다. (자세한 규칙: [GUIDE.md 6단계](GUIDE.md#6-단계-작업-분해tasks와-일관성-점검analyze))

**입력** — 🤖 Codex

```text
$speckit-tasks 헌법의 테스트 우선 원칙에 따라 테스트 작업을 포함해 줘.
```

```text
$speckit-analyze
```

## 규칙

- `$speckit-analyze` 는 **읽기 전용**이다. 보고서만 낸다. CRITICAL 이 있으면 spec/plan/tasks 를 고친 뒤 다시 실행한다.
- 고칠 때 "보고서의 C1, H2 를 반영해 tasks.md 를 고쳐 줘" 처럼 **번호로 요청**하면 정확하다.

## 체크리스트

- [ ] `tasks.md` 의 작업이 `- [ ] T001 … (파일 경로)` 형식이다.
- [ ] 테스트 작업이 구현 작업보다 앞에 있다.
- [ ] `$speckit-analyze` 에 CRITICAL 이 없다.

---

# 8 단계: 구현과 수렴 — `$speckit-implement`, `$speckit-converge`

**목적** — 작업 순서대로 코드를 만들고, 코드가 명세를 모두 만족하는지 검증한다. (자세한 규칙: [GUIDE.md 7단계](GUIDE.md#7-단계-구현implement과-수렴converge))

**입력** — 🤖 Codex

```text
/new
```

```text
$speckit-implement
```

길면 나눠서:

```text
$speckit-implement Phase 1과 Phase 2만 먼저 진행해 줘.
```

구현이 끝나면:

```text
$speckit-converge
```

**Converged** 가 나올 때까지 `$speckit-implement` → `$speckit-converge` 를 반복한다.

## 8-1. 직접 실행해 보기

🖥️ **PowerShell** — Windows Terminal 에서 **새 탭(Ctrl + Shift + T)** 을 열고 (Codex 탭은 그대로 둔다)

```powershell
Set-Location "$HOME\git\my-todo-codex"
node --test
py -m http.server 8000
```

처음 실행하면 **Windows 보안 경고(방화벽)** 창이 "Python이 네트워크에 액세스하도록 허용" 을 물을 수 있다. 내 PC에서만 접속하므로 **취소** 해도 `http://localhost:8000` 은 열린다. (허용할 경우 **개인 네트워크**만 체크)

🌐 브라우저(Edge/Chrome)에서 `http://localhost:8000` → [SAMPLE.md](SAMPLE.md) 시나리오로 확인한다. SAMPLE.md 는 macOS 기준이므로 [부록 D](#부록-d-samplemd-를-windows-에서-읽는-법) 표대로 바꿔 읽는다.

서버를 끄려면 그 탭에서 **Ctrl + C**.

**화면이 비어 있으면** — 브라우저에서 **F12** → **Console** 탭의 빨간 오류를 복사해 🤖 Codex에:

```text
http://localhost:8000 에서 화면이 비어 있어. 브라우저 콘솔 오류는 아래와 같아. 원인을 찾아 고치고, spec.md 와 어긋나지 않는지 확인한 뒤 $speckit-converge 로 다시 검증해 줘.
(오류 붙여 넣기)
```

## 규칙

- Default 모드에서 Codex는 `node --test` 같은 명령을 **승인 없이** 실행하고 결과를 보며 고친다. 인터넷이 필요한 명령(`npm install` 등)은 승인을 묻는다 — 이 앱은 외부 의존성이 없으므로 **거절**한다.
- `py -m http.server` 처럼 **끝나지 않는 명령은 Codex에게 시키지 말고** PowerShell 새 탭에서 직접 실행한다.
- 진행 중 바뀐 파일은 🤖 `/diff` 로, Codex의 자체 리뷰는 🤖 `/review` 로 볼 수 있다.
- 요구사항을 바꾸고 싶으면 코드보다 **명세를 먼저** 고친다 (`$speckit-specify` 또는 spec.md 수정 → `$speckit-plan` → `$speckit-tasks` → `$speckit-implement`).

## 산출물

```
my-todo-codex\
├── index.html  package.json ({"type": "module"})
├── src\   todo.js  storage.js  app.js  style.css
├── tests\ todo.test.js
└── specs\001-…\tasks.md     ← 모든 작업이 [X]
```

## 체크리스트

- [ ] `tasks.md` 의 모든 작업이 `[X]` 다.
- [ ] `node --test` 가 `# fail 0` 이다.
- [ ] [SAMPLE.md](SAMPLE.md) 5단계 시나리오가 모두 명세대로 동작한다.
- [ ] `$speckit-converge` 가 **Converged** 를 보고했다.
- [ ] 🖥️ `git log --oneline` 에 단계별 커밋이 있다 (git 확장 훅 승인 시).

---

# 9 단계: (도전) 두 번째 기능 — 마감일

**목적** — 변경도 명세에서 시작한다. 새 기능 폴더 `specs/002-…` 로 4~8단계를 반복한다. (자세한 규칙: [GUIDE.md 8단계](GUIDE.md#8-단계-도전-두-번째-기능-추가--명세부터-다시))

**입력** — 🤖 Codex, 순서대로 (단계 사이에 `/new` 해도 된다)

```text
$speckit-specify 기존 할 일 앱에 마감일 기능을 추가한다. 사용자는 할 일에 선택적으로 마감일을 지정할 수 있고, 마감일이 지난 미완료 할 일은 눈에 띄게 표시된다. 목록을 마감일이 가까운 순으로 정렬해 볼 수 있다. 기존에 저장된 마감일 없는 할 일도 그대로 보여야 한다.
```
```text
$speckit-clarify
```
```text
$speckit-plan 기존 구조(src/todo.js, src/storage.js, src/app.js)를 유지하고, 마감일은 HTML date 입력과 ISO 날짜 문자열(YYYY-MM-DD)로 저장한다. 기존에 저장된 마감일 없는 데이터도 그대로 읽혀야 한다.
```
```text
$speckit-tasks 헌법의 테스트 우선 원칙에 따라 테스트 작업을 포함해 줘.
```
```text
$speckit-analyze
```
```text
$speckit-implement
```
```text
$speckit-converge
```

## 체크리스트

- [ ] `specs/002-…` 가 새로 생겼고 `001-…` 은 그대로다. `.specify/feature.json` 이 002 를 가리킨다.
- [ ] `node --test` 가 통과하고 [SAMPLE.md](SAMPLE.md) 8단계(마감일)와 5단계(기존 기능)가 모두 동작한다.
- [ ] `$speckit-converge` 가 **Converged** 를 보고했다.

---

# 부록 A. AGENTS.md 규칙 조각

Codex는 프로젝트 루트의 **`AGENTS.md`** 를 매번 읽는다. 아래를 붙여 두면 Spec Kit 단계 밖에서 대화할 때도 SDD 흐름을 지킨다. (🤖 `/init` 으로 기본 `AGENTS.md` 를 만든 뒤 아래 절을 덧붙여도 된다)

```markdown
## Spec-Driven Development 규칙 (Spec Kit)

- 이 프로젝트는 GitHub Spec Kit으로 스펙 주도 개발을 한다. 원칙은 `.specify/memory/constitution.md` 를 따른다.
- 기능 문서는 `specs/NNN-기능이름/` 에 있다. 현재 기능은 `.specify/feature.json` 을 확인한다.
- Spec Kit 단계는 `$speckit-specify`, `$speckit-plan`, `$speckit-tasks`, `$speckit-implement`, `$speckit-converge` 스킬로 실행한다.
- 명세(`spec.md`)에는 기술 스택을 쓰지 않는다. 기술 결정은 `plan.md` 와 `research.md` 에만 기록한다.
- 요구사항이 바뀌면 코드부터 고치지 말고 `spec.md` → `$speckit-plan` → `$speckit-tasks` 순서로 갱신을 제안한다.
- 구현은 `tasks.md` 의 작업 순서를 따르고, 완료한 작업은 `[X]` 로 표시한다.
- 외부 npm 패키지를 설치하지 않는다. 테스트는 `node --test` 로 실행한다.
- 헌법 원칙과 충돌하는 요청을 받으면 구현하기 전에 충돌을 먼저 알린다.
- 문서와 화면 문구, 대답은 한국어로 작성한다.
```

# 부록 B. 자주 겪는 문제 (Windows)

| 증상 | 원인 / 해결 |
| --- | --- |
| `winget` 을 찾을 수 없다 | Microsoft Store 에서 **앱 설치 관리자(App Installer)** 를 설치·업데이트한다 |
| 설치했는데 `specify`/`codex`/`uv` 를 찾을 수 없다 (`is not recognized`) | PATH 미반영. **Terminal 을 완전히 닫고 다시 연다.** `specify` 는 `uv tool update-shell` 후 다시 열기 |
| `python` 을 치면 Microsoft Store 가 열린다 | Windows의 앱 실행 별칭 때문이다. **`py`** 를 쓴다 (`py -m http.server 8000`). 또는 설정 › 앱 › 고급 앱 설정 › 앱 실행 별칭에서 python 끄기 |
| `…ps1 cannot be loaded because running scripts is disabled on this system` | 실행 정책. 1-2 의 `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| `.ps1 is not digitally signed` | 압축 파일·인터넷에서 받은 스크립트에 붙는 "차단" 표시 때문. 프로젝트 폴더에서 `Get-ChildItem -Recurse .specify\*.ps1 \| Unblock-File` |
| PowerShell 스크립트가 계속 실패한다 | 최후의 방법: Python 버전 스크립트로 다시 초기화 — `specify init --here --force --integration codex --script py` (먼저 커밋) |
| `specify init` 이 `codex not found` 로 멈춘다 | 1-3 후 Terminal 다시 열기, `codex --version` 확인 |
| 샌드박스 설정 화면에서 UAC 창이 안 뜨거나 실패 | `Couldn't set up your sandbox with Administrator permissions` → **Try again** 또는 **Use Codex with non-admin sandbox**. 나중에 `/setup-default-sandbox` |
| `Windows sandbox setup was interrupted` | Codex 를 종료(`/quit`)하고 다시 `codex` |
| `$speckit-…` 자동 완성이 안 나온다 | 프로젝트 폴더 안에서 `codex` 를 실행했는지 (`Get-Location`) 확인. `Get-ChildItem .agents\skills` 확인. Codex 재시작 |
| `/speckit-specify` 가 알 수 없는 명령이라고 한다 | Codex에서는 **`$speckit-specify`** |
| 브랜치 생성·커밋 때마다 승인을 묻는다 | 샌드박스가 `.git` 을 보호하기 때문. 정상. 명령을 확인하고 허용 |
| git 커밋에서 `Please tell me who you are` | 1-6 의 `git config --global user.name / user.email` |
| `warning: LF will be replaced by CRLF` | Git for Windows 의 줄바꿈 자동 변환 안내다. 이 실습에서는 무시해도 된다 |
| 폴더가 OneDrive 안에 있어 파일 잠김·동기화 오류 | 프로젝트를 `C:\Users\<내 이름>\git\` 으로 옮긴다 |
| 사용자 이름(경로)에 한글이 있어 스크립트가 경로를 못 찾는다 | `C:\dev\my-todo-codex` 처럼 영문 경로에 프로젝트를 만든다 |
| Codex 입력창에서 한글이 깨진다 | 메모장 등에서 쓴 뒤 붙여 넣기. Windows Terminal 최신 버전 사용 |
| `py -m http.server` 실행 시 방화벽 창 | 8-1 참고 — 취소해도 `localhost` 는 동작 |
| `Address already in use` / `[WinError 10048]` | 8000 포트 사용 중. `py -m http.server 8080` → `http://localhost:8080` |
| 화면이 비어 있다 | `index.html` 을 더블클릭해 `file:///C:/…` 로 열었는지 확인. 반드시 `http://localhost:8000` |

# 부록 C. Claude Code ↔ Codex 명령 대응표

| 하고 싶은 일 | Claude Code | Codex |
| --- | --- | --- |
| 에이전트 실행 | `claude` | `codex` |
| Spec Kit 단계 실행 | `/speckit-plan …` | `$speckit-plan …` |
| 스킬 목록 | `/` 자동 완성 | `$` 자동 완성, `/skills` |
| 새 대화 | `/clear` | `/new` |
| 긴 대화 요약 | `/compact` | `/compact` |
| 권한 설정 | 질문마다 허용 / `settings.json` | `/permissions` (Read Only · Default · Full Access) |
| Windows 샌드박스 재설정 | — | `/setup-default-sandbox` |
| 모델 바꾸기 | `/model` | `/model` |
| 현재 상태 | `/status` | `/status` |
| 바뀐 내용 보기 | (`git diff`) | `/diff` |
| 프로젝트 규칙 파일 | `CLAUDE.md` | `AGENTS.md` (`/init`) |
| 종료 | `/exit` | `/quit` 또는 `/exit` |

# 부록 D. SAMPLE.md 를 Windows 에서 읽는 법

[SAMPLE.md](SAMPLE.md) 는 macOS 기준이다. 아래처럼 바꿔 읽는다. (폴더 이름은 `my-todo` → `my-todo-codex`)

| SAMPLE.md (macOS) | Windows |
| --- | --- |
| 🖥️ 터미널 | 🖥️ Windows Terminal 의 PowerShell |
| `cd ~/git/my-todo` | `Set-Location "$HOME\git\my-todo-codex"` |
| `ls -a` | `Get-ChildItem -Force` |
| `cat 파일` | `Get-Content 파일` |
| `grep -n "단어" 파일` | `Select-String -Pattern "단어" 파일` |
| `python3 -m http.server 8000` | `py -m http.server 8000` |
| `python3 -c "print('가'*201)" \| pbcopy` | `'가' * 201 \| Set-Clipboard` |
| `⌘ + V` (붙여 넣기) | `Ctrl + V` |
| `⌘ + R` (새로 고침) | `F5` 또는 `Ctrl + R` |
| `⌘ + Shift + R` (강력 새로 고침) | `Ctrl + F5` 또는 `Ctrl + Shift + R` |
| `⌘ + ⌥ + I` (개발자 도구) | `F12` 또는 `Ctrl + Shift + I` |
| `⌘ + ⌥ + J` (Console) | `Ctrl + Shift + J` |
| `⌘ + Q` (브라우저 완전 종료) | 모든 창 닫기 (`Alt + F4`). Edge·Chrome이 백그라운드에서 계속 실행되지 않는지 작업 표시줄 트레이 확인 |
| Safari 개발자 도구 안내 | 해당 없음 — Edge/Chrome 사용 |
| 🤖 Claude Code 에 `/speckit-…` | 🤖 Codex 에 `$speckit-…` (`/clear` → `/new`) |

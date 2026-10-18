# Spec Kit × Codex 가이드 — Codex CLI로 하는 스펙 주도 개발

> 이 문서는 [GUIDE.md](GUIDE.md)(Claude Code 버전)와 **같은 할 일 앱을 같은 순서로** 만들되, AI 에이전트로 **OpenAI Codex CLI** 를 쓰는 방법을 단계별로 안내한다.
> SDD 개념, 각 문서(spec·plan·tasks …)의 구성, 단계별 규칙의 자세한 설명은 [GUIDE.md](GUIDE.md) 와 같으므로 여기서는 **Codex에서 달라지는 점**과 **따라 할 입력**에 집중한다.
> 검증 기준: `specify-cli` **v1.1.3** · `specify init --integration codex` · Codex CLI · macOS/Linux
> 🪟 **Windows PC** 라면 [GUIDE-codex-windows.md](GUIDE-codex-windows.md) 를 따른다.

---

# 개념 — Claude Code 버전과 무엇이 다른가

Spec Kit의 단계(constitution → specify → clarify → plan → tasks → analyze → implement → converge)와 산출물(`.specify/`, `specs/001-…/`)은 **에이전트와 관계없이 똑같다.** 달라지는 것은 "스킬이 설치되는 곳"과 "부르는 방법", 그리고 Codex의 **권한(샌드박스)** 이다.

| 항목 | Claude Code ([GUIDE.md](GUIDE.md)) | **Codex CLI (이 문서)** |
| --- | --- | --- |
| 초기화 옵션 | `specify init … --integration claude` | `specify init … --integration codex` |
| 스킬 설치 위치 | `.claude/skills/speckit-*/SKILL.md` | **`.agents/skills/speckit-*/SKILL.md`** |
| 스킬 부르는 법 | `/speckit-specify …` (슬래시) | **`$speckit-specify …`** (달러 기호) |
| 스킬 목록 보기 | `/` 입력 후 자동 완성 | `$` 입력 후 자동 완성, 또는 `/skills` |
| 에이전트 실행 | `claude` | `codex` |
| 대화 비우기 | `/clear` | `/new` (또는 `/clear` — 화면까지 지움) |
| 프로젝트 규칙 파일 | `CLAUDE.md` | **`AGENTS.md`** (`/init` 으로 생성 가능) |
| 권한 | 명령마다 허용 여부 질문 | **샌드박스 + 권한 모드** (`/permissions`): 작업 폴더 안 읽기·쓰기·명령 실행은 자동, 인터넷·폴더 밖·**`.git` 쓰기**는 승인 필요 |

> ⚠️ **`/` 와 `$` 를 헷갈리지 말자.** Codex에서 `/` 로 시작하는 것은 Codex 자체 명령(`/new`, `/permissions`, `/skills` …)이고, Spec Kit 단계는 **`$`** 로 부른다. 인터넷 글의 `/speckit.specify`, `/prompts:speckit.specify` 는 예전 방식이다.

```
                         (프로젝트당 1회)
 터미널  specify init --integration codex ──► git init ──► codex
                                                              │
 Codex   $speckit-constitution ──► constitution.md             │
        ┌──────────────────────────────────────────────────────┘ (기능마다 반복)
        ▼
 $speckit-specify → $speckit-clarify → $speckit-plan → $speckit-checklist
 → $speckit-tasks → $speckit-analyze → $speckit-implement → $speckit-converge
```

## 이 가이드의 단계

| 단계 | 내용 | 사용하는 명령 |
| --- | --- | --- |
| 1 | 설치 — Codex CLI, specify CLI, 프로젝트 초기화 | `npm i -g @openai/codex`, `specify init --integration codex` |
| 2 | Codex 실행 — 로그인, 폴더 신뢰, 권한 모드, 스킬 확인 | `codex`, `/permissions`, `/skills` |
| 3 | 헌법 | `$speckit-constitution` |
| 4 | 명세 | `$speckit-specify` |
| 5 | 명확화 | `$speckit-clarify` |
| 6 | 계획 (+ 체크리스트) | `$speckit-plan`, `$speckit-checklist` |
| 7 | 작업 분해와 일관성 점검 | `$speckit-tasks`, `$speckit-analyze` |
| 8 | 구현과 수렴 | `$speckit-implement`, `$speckit-converge` |
| 9 | (도전) 두 번째 기능 — 마감일 | 4~8단계 반복 |

> 📌 실습 폴더는 Claude Code 버전과 겹치지 않게 **`my-todo-codex`** 로 한다. 완성된 앱의 실행·확인은 [SAMPLE.md](SAMPLE.md) 를 그대로 쓴다(폴더 이름만 바꿔 읽는다).

| 표시 | 하는 곳 |
| --- | --- |
| 🖥️ **터미널** | macOS 터미널 (Codex 밖) |
| 🤖 **Codex** | `codex` 를 실행한 화면의 입력창 |

---

# 1 단계: 설치 — Codex CLI, specify CLI, 프로젝트 초기화

**목적** — Codex CLI와 `specify` CLI를 설치하고, Codex가 Spec Kit 스킬을 쓸 수 있는 프로젝트를 만든다.

**입력** — 🖥️ 터미널

### 1-1. Codex CLI 설치

```bash
# 방법 A: npm (Node.js 가 있으면)
npm install -g @openai/codex

# 방법 B: Homebrew
brew install --cask codex

# 방법 C: 공식 설치 스크립트
curl -fsSL https://chatgpt.com/codex/install.sh | sh

codex --version          # 버전이 나오면 성공
```

### 1-2. uv 와 specify CLI 설치 (이미 했다면 건너뜀)

```bash
brew install uv                    # 또는: curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install specify-cli
specify version
```

### 1-3. 프로젝트 초기화 (Codex용)

```bash
mkdir -p ~/git && cd ~/git
specify init my-todo-codex --integration codex --script sh
cd my-todo-codex
```

| 옵션 | 의미 |
| --- | --- |
| `--integration codex` | Codex용 스킬을 `.agents/skills/` 에 설치 |
| `--script sh` | 자동화 스크립트를 bash 버전으로 |
| `--ignore-agent-tools` | `codex` 가 아직 설치되지 않았을 때 검사를 건너뜀 (권장하지 않음) |

### 1-4. git 확장과 git 저장소 (권장)

```bash
specify extension add git

git init
git add -A
git commit -m "chore: init Spec Kit for Codex"
```

> 💡 Claude Code 버전에서는 헌법 단계에서 AI가 `git init` 을 했다. Codex는 **샌드박스가 `.git` 폴더 쓰기를 막기 때문에**, 저장소는 터미널에서 미리 만들어 두는 것이 편하다. git 확장의 초기화 훅은 저장소가 이미 있으면 `Git repository already initialized; skipping` 으로 넘어간다.

## 규칙

- `specify init` 은 **`codex` 명령이 설치되어 있는지 검사**한다. 없으면 `codex not found … Codex CLI is required` 오류로 멈춘다 → 1-1 을 먼저 한다.
- `--integration` 값은 `codex` 다. 예전 글의 `--ai codex` 는 쓰지 않는다.
- 초기화 화면의 "Agent Folder Security" 안내처럼, 공개 저장소라면 `.agents/` 중 민감한 파일이 없는지 커밋 전에 확인한다. (Spec Kit 스킬 자체는 공개해도 되는 지시서다)

## 산출물

초기화 화면 마지막 (발췌):

```
Project ready.
╭─ Next Steps ─────────────────────────────────────────────────────────────╮
│  1. Go to the project folder: cd my-todo-codex                           │
│  2. Start Codex in this project directory; spec-kit skills were          │
│     installed to .agents/skills                                          │
│  3. Start using skills with your coding agent:                           │
│     3.1 $speckit-constitution - Establish project principles             │
│     3.2 $speckit-specify - Create baseline specification                 │
│     3.3 $speckit-plan - Create implementation plan                       │
│     3.4 $speckit-tasks - Generate actionable tasks                       │
│     3.5 $speckit-implement - Execute implementation                      │
│     3.6 $speckit-converge - Assess the codebase and append remaining     │
│         work as tasks                                                    │
╰──────────────────────────────────────────────────────────────────────────╯
```

```
my-todo-codex/
├── .git/                                    (1-4 에서 생성)
├── .agents/
│   └── skills/
│       ├── speckit-constitution/SKILL.md
│       ├── speckit-specify/SKILL.md
│       ├── speckit-clarify/SKILL.md
│       ├── speckit-plan/SKILL.md
│       ├── speckit-checklist/SKILL.md
│       ├── speckit-tasks/SKILL.md
│       ├── speckit-analyze/SKILL.md
│       ├── speckit-implement/SKILL.md
│       ├── speckit-converge/SKILL.md
│       ├── speckit-taskstoissues/SKILL.md   (구버전 호환용, 사용 안 함)
│       └── speckit-git-*/SKILL.md           (git 확장 5개: commit, feature, initialize, remote, validate)
└── .specify/
    ├── integration.json                     ("integration": "codex")
    ├── memory/constitution.md               (아직 빈 템플릿)
    ├── scripts/bash/  templates/  workflows/
    ├── extensions.yml  extensions/git/      (git 확장)
    └── integrations/codex.manifest.json
```

## 체크리스트

- [ ] `codex --version`, `specify version` 이 모두 출력된다.
- [ ] `ls .agents/skills` 에 `speckit-` 으로 시작하는 폴더가 15개(기본 10 + git 5) 있다.
- [ ] `cat .specify/integration.json` 에 `"integration": "codex"` 가 있다.
- [ ] `git log --oneline` 에 첫 커밋이 있다.

---

# 2 단계: Codex 실행 — 로그인, 폴더 신뢰, 권한 모드, 스킬 확인

**목적** — 프로젝트 폴더에서 Codex를 열고, Spec Kit 스킬이 보이는지 확인한다.

**입력** — 🖥️ 터미널 (`my-todo-codex` 안에서)

```bash
codex
```

### 2-1. 로그인 (처음 한 번)

화면에서 **Sign in with ChatGPT** 를 고른다. 브라우저가 열리면 ChatGPT 계정으로 로그인하고 허용한다. (ChatGPT Plus·Pro·Business·Edu·Enterprise 요금제에 Codex 사용이 포함된다. API 키로도 쓸 수 있지만 별도 설정이 필요하다)

### 2-2. 폴더 신뢰

`Trust this folder?` 처럼 이 폴더를 믿을지 묻는다. 내가 만든 실습 폴더이므로 **Trust and continue** 를 고른다. 신뢰하지 않으면 이 폴더의 설정·훅이 꺼진 제한 모드로 열린다.

### 2-3. 권한 모드 확인

🤖 **Codex**

```text
/permissions
```

| 모드 | 하는 일 | 이 실습 |
| --- | --- | --- |
| Read Only | 읽기만. 파일 수정·명령 실행 때마다 승인 | ✗ (문서를 만들 수 없음) |
| **Default** | 작업 폴더 안 읽기·쓰기·명령 실행은 자동. **인터넷, 폴더 밖, `.git`·`.agents` 쓰기는 승인 필요** | ✅ 권장 |
| Full Access | 묻지 않고 폴더 밖·인터넷까지 | ✗ (실습에서는 쓰지 않음) |

**Default** 로 둔다.

### 2-4. 스킬 확인

🤖 **Codex**

```text
/skills
```

또는 입력창에 `$speckit` 까지만 입력하면 자동 완성 목록이 나온다.

## 규칙

- 반드시 **프로젝트 폴더 안에서** `codex` 를 실행한다. Codex는 실행한 폴더(와 git 저장소 루트까지)의 `.agents/skills/` 에서 스킬을 찾는다.
- Default 모드에서 git 확장이 브랜치를 만들거나 커밋하려 하면(`.git` 쓰기) **승인 질문**이 나온다. 명령을 읽고 `git …` 이면 허용한다. 같은 명령을 계속 허용하려면 "이 명령은 다시 묻지 않기" 쪽을 고른다.
- 스킬이 안 보이면 Codex를 종료(`/quit`)했다가 프로젝트 폴더에서 다시 `codex` 를 실행한다.

## 산출물

- (처음 한 번) Codex 로그인 정보 — 홈 폴더의 `~/.codex/` 에 저장 (프로젝트 폴더가 아님)
- `/skills` 목록에 `speckit-constitution`, `speckit-specify` … `speckit-git-*`

## 체크리스트

- [ ] Codex 화면 아래쪽 상태에 작업 폴더가 `~/git/my-todo-codex` 로 보인다. (`/status` 로도 확인)
- [ ] `$speckit` 입력 시 Spec Kit 스킬 목록이 자동 완성된다.
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
- git 확장의 `speckit.git.initialize` 훅이 먼저 돌지만, 1-4 에서 저장소를 만들었으므로 건너뛴다.
- 진행 중에 Codex가 실행하는 명령(`.specify/scripts/bash/…`)이 화면에 보인다. 작업 폴더 안 명령이라 Default 모드에서는 승인 없이 실행된다.

## 산출물

- `.specify/memory/constitution.md` — 자리표시자가 모두 채워지고 맨 위에 Sync Impact Report, 아래에 `Version 1.0.0`

## 체크리스트

- [ ] `constitution.md` 에 `[PROJECT_NAME]` 같은 자리표시자가 남아 있지 않다.
- [ ] 원칙 5개가 모두 반영되었고 버전·날짜가 있다.
- [ ] 🖥️ `git status` 로 `constitution.md` 가 바뀐 것을 확인했다. (git 확장이 커밋을 제안하면 승인)

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
- [ ] 🖥️ `git branch` 에 `* 001-…` 이 보인다. (승인을 거절했다면 브랜치 없이 진행해도 SDD는 동작한다)

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
$speckit-plan 빌드 도구 없이 순수 HTML, CSS, JavaScript(ES 모듈)로 만든다. 화면은 index.html 하나다. 할 일 데이터를 다루는 로직은 src/todo.js 의 순수 함수로, 저장은 src/storage.js 에서 localStorage를 사용하고, 화면 그리기와 이벤트 처리는 src/app.js 가 맡는다. 테스트는 tests/todo.test.js 에 Node.js 내장 테스트 러너(node --test)로 작성하고, package.json 에는 "type": "module" 만 지정하며 외부 의존성은 두지 않는다. 로컬 실행은 python3 -m http.server 로 한다.
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

🖥️ **터미널** (Codex는 그대로 두고 새 탭에서)

```bash
cd ~/git/my-todo-codex
node --test
python3 -m http.server 8000
```

🌐 브라우저에서 `http://localhost:8000` → [SAMPLE.md](SAMPLE.md) 시나리오로 확인한다.

**화면이 비어 있으면** — 브라우저 Console(⌘ + ⌥ + J)의 빨간 오류를 복사해 🤖 Codex에:

```text
http://localhost:8000 에서 화면이 비어 있어. 브라우저 콘솔 오류는 아래와 같아. 원인을 찾아 고치고, spec.md 와 어긋나지 않는지 확인한 뒤 $speckit-converge 로 다시 검증해 줘.
(오류 붙여 넣기)
```

## 규칙

- Default 모드에서 Codex는 `node --test` 같은 명령을 **승인 없이** 실행하고 결과를 보며 고친다. 인터넷이 필요한 명령(`npm install` 등)은 승인을 묻는다 — 이 앱은 외부 의존성이 없으므로 **거절**한다.
- `python3 -m http.server` 처럼 **끝나지 않는 명령은 Codex에게 시키지 말고** 터미널에서 직접 실행한다.
- 진행 중 바뀐 파일은 🤖 `/diff` 로, Codex의 자체 리뷰는 🤖 `/review` 로 볼 수 있다.
- 요구사항을 바꾸고 싶으면 코드보다 **명세를 먼저** 고친다 (`$speckit-specify` 또는 spec.md 수정 → `$speckit-plan` → `$speckit-tasks` → `$speckit-implement`).

## 산출물

```
my-todo-codex/
├── index.html  package.json ({"type": "module"})
├── src/  todo.js  storage.js  app.js  style.css
├── tests/ todo.test.js
└── specs/001-…/tasks.md     ← 모든 작업이 [X]
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

# 부록 B. 자주 겪는 문제

| 증상 | 원인 / 해결 |
| --- | --- |
| `specify init` 이 `codex not found` 로 멈춘다 | Codex CLI 미설치. 1-1 후 다시 실행 (`codex --version` 확인) |
| `$speckit-…` 자동 완성이 안 나온다 | 프로젝트 폴더 **안에서** `codex` 를 실행했는지 확인. `ls .agents/skills` 확인. Codex 재시작. `/skills` 로 목록 확인 |
| `/speckit-specify` 를 입력했더니 알 수 없는 명령이라고 한다 | Codex에서 Spec Kit 단계는 **`$`** 로 부른다: `$speckit-specify` |
| 인터넷 글의 `/prompts:speckit.specify` 가 안 된다 | 예전 Codex 통합(프롬프트 파일) 방식이다. 지금은 `.agents/skills` 스킬 + `$speckit-…` |
| 브랜치 생성·커밋 때마다 승인을 묻는다 | Default 모드 샌드박스가 `.git` 쓰기를 보호하기 때문이다. 정상. 명령을 확인하고 허용하거나, "다시 묻지 않기"를 선택 |
| `git init` 이 샌드박스에서 실패했다 | 터미널에서 직접 `git init && git add -A && git commit -m "init"` (1-4) |
| Codex가 `npm install` 을 하려고 한다 | 헌법·계획 위반이다. 승인을 거절하고 "외부 의존성 없이 node:test 로 해 줘" 라고 요청 |
| `.agents/skills` 의 스킬을 Codex가 고치려 한다 | `.agents` 도 보호 폴더다. 거절한다. 스킬 수정이 필요하면 `specify integration upgrade codex` |
| 로그인이 풀렸다 / 다른 계정으로 | 🤖 `/logout` 후 `codex` 재실행 |
| 대화가 길어져 앞 내용을 헷갈린다 | 산출물은 파일에 있으므로 단계 사이에 `/new` 해도 된다. 긴 대화는 `/compact` 로 요약 |
| 화면이 비어 있다 | `file://` 대신 `python3 -m http.server 8000`. 8-1 의 프롬프트로 수정 요청 |
| Claude Code 버전과 같은 폴더에서 둘 다 쓰고 싶다 | 가능하다: `specify integration install claude` 로 `.claude/skills` 를 추가 설치. 산출물(`specs/`)은 공유된다 |

# 부록 C. Claude Code ↔ Codex 명령 대응표

| 하고 싶은 일 | Claude Code | Codex |
| --- | --- | --- |
| 에이전트 실행 | `claude` | `codex` |
| Spec Kit 단계 실행 | `/speckit-plan …` | `$speckit-plan …` |
| 스킬 목록 | `/` 자동 완성 | `$` 자동 완성, `/skills` |
| 새 대화 | `/clear` | `/new` |
| 긴 대화 요약 | `/compact` | `/compact` |
| 권한 설정 | 질문마다 허용 / `settings.json` | `/permissions` (Read Only · Default · Full Access) |
| 모델 바꾸기 | `/model` | `/model` (추론 강도도 선택) |
| 현재 상태 | `/status` | `/status` |
| 바뀐 내용 보기 | (터미널 `git diff`) | `/diff` |
| 프로젝트 규칙 파일 | `CLAUDE.md` | `AGENTS.md` (`/init`) |
| 종료 | `/exit` | `/quit` 또는 `/exit` |

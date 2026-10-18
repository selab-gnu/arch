> 🪟 **Windows PC** 라면 [GUIDE-windows.md](GUIDE-windows.md) 를, **Codex** 를 쓴다면 [GUIDE-codex.md](GUIDE-codex.md) (Windows: [GUIDE-codex-windows.md](GUIDE-codex-windows.md)) 를 따른다.

# 개념

## 스펙 주도 개발(SDD)이란?

**Spec-Driven Development(SDD, 스펙 주도 개발)** 은 코드를 바로 짜는 대신 **"무엇을 왜 만드는지"를 먼저 명세(Specification)로 쓰고, 그 명세에서 계획 → 작업 목록 → 코드를 차례로 만들어 내는** 개발 방식이다. AI 코딩 에이전트가 등장하면서 "명세만 잘 쓰면 AI가 구현한다"는 흐름이 현실이 되었고, GitHub이 이를 위해 만든 오픈소스 툴킷이 **Spec Kit** 이다.

| 구분 | 바이브 코딩 (Vibe Coding) | 스펙 주도 개발 (SDD) |
| --- | --- | --- |
| 시작점 | "할 일 앱 만들어 줘" 한 줄 | 원칙 → 명세 → 계획 → 작업 |
| 결과 | 그럴듯하지만 매번 달라짐 | 명세에 묶여 예측 가능 |
| 기록 | 채팅 기록에만 남음 | `spec.md`, `plan.md` 등 파일로 남음 |
| 변경 | 코드를 직접 고침 | **명세를 고치고** 다시 생성 |
| 리뷰 | 코드만 리뷰 | 명세·계획·코드 모두 리뷰 |

핵심 아이디어는 세 가지다.

1. **명세가 진실의 원천(Source of Truth)이다.** 코드는 명세를 표현한 결과물일 뿐이다.
2. **"무엇/왜"와 "어떻게"를 분리한다.** 명세(`spec.md`)에는 기술 스택을 쓰지 않고, 기술 선택은 계획(`plan.md`)에서 한다.
3. **단계마다 사람이 검토한다.** AI가 만든 산출물을 읽고, 고치고, 다음 단계로 넘어간다.

## Spec Kit의 구성 요소

| 구성 요소 | 위치 | 설명 |
| --- | --- | --- |
| `specify` CLI | 내 컴퓨터(터미널) | 프로젝트를 초기화하고 확장·통합을 관리하는 파이썬 도구 |
| 스킬(Skills) | `.claude/skills/speckit-*/SKILL.md` | Claude Code 안에서 `/speckit-xxx` 로 호출하는 단계별 지시서 |
| 템플릿 | `.specify/templates/*.md` | spec, plan, tasks, checklist, constitution 문서의 틀 |
| 스크립트 | `.specify/scripts/bash/*.sh` | 기능 폴더 생성, 사전 조건 확인 등 자동화 스크립트 |
| 헌법(Constitution) | `.specify/memory/constitution.md` | 모든 단계가 지켜야 하는 프로젝트 원칙 |
| 기능 폴더 | `specs/001-todo-list-app/` | 기능 하나당 명세·계획·작업 문서가 모이는 곳 |

> ⚠️ **터미널 명령 vs 에이전트 명령을 구분하자.**
> `specify ...` 는 **터미널**에서, `/speckit-...` 는 **Claude Code 채팅창**에서 입력한다.

## 전체 흐름과 산출물 지도

```
                        (프로젝트당 1회)
 터미널  specify init ──► /speckit-constitution ──► constitution.md
                                │
        ┌───────────────────────┘   (기능마다 반복)
        ▼
 /speckit-specify ──► spec.md, checklists/requirements.md      ← 무엇을·왜
 /speckit-clarify ──► spec.md 에 "## Clarifications" 추가        ← 모호함 제거 (선택)
 /speckit-plan    ──► plan.md, research.md, data-model.md,      ← 어떻게
                      contracts/, quickstart.md
 /speckit-checklist ► checklists/<주제>.md                      ← 요구사항 품질 점검 (선택)
 /speckit-tasks   ──► tasks.md                                  ← 작업 분해
 /speckit-analyze ──► (보고서만 출력, 파일 수정 없음)              ← 일관성 점검 (선택)
 /speckit-implement ► 실제 소스 코드, tasks.md 체크 표시           ← 구현
 /speckit-converge ─► "Converged" 또는 tasks.md 에 작업 추가       ← 완성도 검증 → 필요하면 implement 반복
```

## 명령(스킬) 한눈에 보기

| 스킬 | 필수 여부 | 하는 일 | 주요 산출물 |
| --- | --- | --- | --- |
| `/speckit-constitution` | 프로젝트당 1회 | 프로젝트 원칙 수립 | `.specify/memory/constitution.md` |
| `/speckit-specify` | 필수 | 자연어 설명 → 기능 명세 | `specs/001-todo-list-app/spec.md` |
| `/speckit-clarify` | 권장 | 최대 5개의 질문으로 명세의 빈틈 보완 | `spec.md` 갱신 |
| `/speckit-plan` | 필수 | 기술 스택·구조 설계 | `plan.md` 외 설계 문서 |
| `/speckit-checklist` | 선택 | 요구사항 품질 체크리스트("요구사항의 단위 테스트") | `checklists/*.md` |
| `/speckit-tasks` | 필수 | 의존 순서대로 작업 목록 생성 | `tasks.md` |
| `/speckit-analyze` | 권장 | spec·plan·tasks 사이의 충돌·누락 보고 (읽기 전용) | 콘솔 보고서 |
| `/speckit-implement` | 필수 | tasks.md 순서대로 구현 | 소스 코드 |
| `/speckit-converge` | 필수 | 코드가 명세를 다 만족하는지 검증 | `Converged` 보고 또는 추가 작업 |

- **짧은 경로**(작은 기능): constitution → specify → plan → tasks → implement → converge
- **전체 경로**(실무 기능): constitution → specify → **clarify** → plan → **checklist** → tasks → **analyze** → implement → converge

이 가이드는 **전체 경로**를 7단계로 묶어 설명하고, 8단계에서 두 번째 기능으로 한 번 더 반복한다.

| 단계 | 내용 | 사용하는 명령 |
| --- | --- | --- |
| 1 | 설치와 프로젝트 초기화 | `uv`, `specify init`, `specify extension add git` |
| 2 | 헌법: 프로젝트 원칙 정하기 | `/speckit-constitution` |
| 3 | 명세: 무엇을 왜 만드는가 | `/speckit-specify` |
| 4 | 명확화: 모호함 없애기 | `/speckit-clarify` |
| 5 | 계획: 어떻게 만들 것인가 | `/speckit-plan`, `/speckit-checklist` |
| 6 | 작업 분해와 일관성 점검 | `/speckit-tasks`, `/speckit-analyze` |
| 7 | 구현과 수렴 검증 | `/speckit-implement`, `/speckit-converge` |
| 8 | (도전) 두 번째 기능 추가 | 3~7단계 반복 |

> 📌 실습 예제: 이 가이드의 모든 입력 예시는 **"할 일 관리 웹 앱(my-todo)"** 을 기준으로 한다. 완성된 앱을 실행·사용·확인하는 방법은 [SAMPLE.md](SAMPLE.md) 에 있다.

---

# 1 단계: 설치와 프로젝트 초기화

**목적** — `specify` CLI를 설치하고, Claude Code가 Spec Kit 스킬을 쓸 수 있는 프로젝트 폴더를 만든다.

**입력** — 터미널 명령

### 1-1. uv 설치 (이미 있으면 건너뜀)

```bash
# macOS (Homebrew)
brew install uv
# 또는 macOS/Linux 공통 설치 스크립트
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1-2. specify CLI 설치

```bash
uv tool install specify-cli
specify version          # 버전 정보 박스가 출력되면 성공
```

> 특정 버전을 고정하고 싶다면: `uv tool install specify-cli==1.1.3`
> 나중에 업그레이드 확인: `specify self check`

### 1-3. 프로젝트 초기화 (Claude Code용)

```bash
specify init my-todo --integration claude --script sh
cd my-todo
```

| 옵션 | 의미 |
| --- | --- |
| `my-todo` | 새로 만들 폴더 이름. 현재 폴더에 설치하려면 `--here` |
| `--integration claude` | Claude Code용 스킬을 `.claude/skills` 에 설치 |
| `--script sh` | 자동화 스크립트를 bash 버전으로 (Windows는 `ps`) |
| `--force` | 이미 파일이 있는 폴더에 병합 설치할 때 |

### 1-4. (권장) git 확장 설치

```bash
specify extension add git
```

git 확장을 설치하면 기능마다 기능 폴더와 같은 이름(예: `001-todo-list-app`)의 **git 브랜치가 자동 생성**되고, 단계 사이에 커밋을 제안해 준다. 설치하지 않아도 SDD는 동작한다(현재 기능은 `.specify/feature.json` 으로 추적).

## 규칙

- `specify` 명령은 **터미널**에서, `/speckit-*` 명령은 **Claude Code 안**에서 실행한다.
- 기존 코드가 있는 폴더에 `--here --force` 로 설치할 때는 **반드시 먼저 커밋하거나 백업**한다.
- `.claude/` 폴더에는 인증 정보 등이 저장될 수 있으므로, 공개 저장소라면 `.gitignore` 에 민감한 부분을 추가할지 검토한다(초기화 화면의 "Agent Folder Security" 안내).
- 예전 글의 `--ai claude` 옵션은 쓰지 않는다. 현재 옵션은 `--integration claude` 이다.

## 산출물

```
my-todo/
├── .claude/
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
│       └── speckit-git-*/SKILL.md           (git 확장 설치 시 5개)
└── .specify/
    ├── memory/constitution.md               (아직 빈 템플릿)
    ├── scripts/bash/*.sh                    (create-new-feature.sh, setup-plan.sh …)
    ├── templates/{spec,plan,tasks,checklist,constitution}-template.md
    ├── workflows/speckit/workflow.yml
    ├── integrations/{claude,speckit}.manifest.json
    ├── integration.json, init-options.json  (버전·통합 정보: "integration": "claude")
    ├── extensions.yml                       (git 확장 설치 시: 단계별 hook 설정)
    └── extensions/git/                      (git 확장 설치 시: 스크립트·설정)

※ git 저장소(.git)와 specs/ 폴더는 아직 없다. .git 은 2단계(constitution) 때,
  specs/ 와 .specify/feature.json 은 3단계(specify) 때 생긴다.
```

## 체크리스트

- [ ] `specify version` 에서 CLI Version 이 출력된다.
- [ ] 확인은 숨김 폴더가 보이도록 터미널에서 `ls -a` 와 `ls .claude/skills` 로 한다. (Finder는 `⌘ + Shift + .`)
- [ ] `my-todo/.claude/skills/` 아래에 `speckit-` 으로 시작하는 폴더가 10개 이상 있다.
- [ ] `my-todo/.specify/memory/constitution.md` 파일이 존재한다(내용은 `[PROJECT_NAME]` 같은 자리표시자).
- [ ] (git 확장 사용 시) `specify extension add git` 결과에 `speckit.git.feature` 등이 나열된다.

---

# 2 단계: 헌법(Constitution) — 프로젝트 원칙 정하기

**목적** — 이후 모든 단계(명세·계획·구현)가 **검사 기준으로 삼을 원칙**을 정한다. 프로젝트당 한 번 실행하고, 필요할 때만 개정한다.

**입력** — Claude Code를 실행하고(`claude`) 채팅창에 입력

```text
/speckit-constitution 이 프로젝트는 초보자 학습용 할 일 관리 웹 앱이다. 다음 원칙을 정해 줘.
1) 단순성: 빌드 도구나 프레임워크 없이 순수 HTML/CSS/JavaScript만 사용한다.
2) 테스트 우선: 핵심 로직은 순수 함수로 분리하고, Node.js 내장 테스트 러너(node --test)로 먼저 테스트를 작성한다.
3) 접근성: 모든 기능은 키보드만으로 사용할 수 있어야 한다.
4) 개인정보 보호: 데이터는 브라우저 localStorage에만 저장하고 외부로 전송하지 않는다.
5) 문서와 화면 문구는 한국어로 작성한다.
```

## 규칙

- 원칙은 **3~7개** 정도로, "반드시 ~한다 / ~하지 않는다" 처럼 **검증 가능한 문장**으로 쓴다. ("좋은 코드를 쓴다" ✗ → "모든 핵심 로직에는 단위 테스트가 있다" ✓)
- 기능 요구사항(무엇을 만들지)은 헌법에 넣지 않는다. 그건 3단계 명세의 몫이다.
- AI는 템플릿의 `[PRINCIPLE_1_NAME]` 같은 **자리표시자를 모두 채워야** 하며, 맨 위에 **Sync Impact Report**(HTML 주석)와 **버전**(예: 1.0.0)을 기록한다.
- 나중에 원칙을 바꾸면 다시 `/speckit-constitution` 을 실행해 **버전을 올린다**(의미 변경은 MINOR/MAJOR).

## 산출물

- `.specify/memory/constitution.md` — 원칙, 추가 제약, 개발 흐름, 거버넌스(개정 절차), 버전·비준일
- (git 확장 사용 시) git 저장소 초기화 + 첫 커밋

예시(발췌, AI 출력은 매번 조금씩 다르다):

```markdown
<!-- Sync Impact Report
Version change: (template) → 1.0.0
... -->
# My-Todo Constitution

## Core Principles

### I. 단순성 (Simplicity)
빌드 도구, 번들러, 프레임워크를 사용하지 않는다. 브라우저가 바로 실행할 수 있는 HTML/CSS/JS만 사용한다.

### II. 테스트 우선 (Test-First, NON-NEGOTIABLE)
...
**Version**: 1.0.0 | **Ratified**: 2026-10-10 | **Last Amended**: 2026-10-10
```

## 체크리스트

- [ ] `constitution.md` 에 `[` `]` 로 둘러싼 자리표시자가 남아 있지 않다.
- [ ] 입력한 원칙 5개가 모두 반영되어 있다.
- [ ] 버전(예: `1.0.0`)과 날짜가 기록되어 있다.
- [ ] 각 원칙이 "검증 가능한 문장"인지 직접 읽고 확인했다. 아니면 직접 수정하거나 다시 요청한다.

---

# 3 단계: 명세(Specify) — 무엇을, 왜 만드는가

**목적** — 만들고 싶은 기능을 자연어로 설명하면, AI가 **사용자 스토리·요구사항·성공 기준**을 갖춘 기능 명세를 만든다.

**입력**

```text
/speckit-specify 혼자 쓰는 간단한 할 일 관리 앱을 만들고 싶다. 사용자는 할 일을 입력해 목록에 추가하고, 완료 여부를 체크하거나 해제하고, 필요 없는 할 일을 삭제할 수 있다. 목록은 '전체 / 진행 중 / 완료'로 걸러 볼 수 있고, 남은 할 일 개수가 항상 보인다. 페이지를 새로 고치거나 브라우저를 다시 열어도 목록이 그대로 남아 있어야 한다. 로그인이나 여러 사용자 기능은 이번 범위가 아니다.
```

## 규칙

- **"무엇을"과 "왜"만 쓴다. 기술 스택(HTML, React, DB 이름 등)은 쓰지 않는다.** 기술은 5단계(plan)에서 정한다.
- **범위 밖(Out of scope)** 을 명시하면 AI가 기능을 부풀리지 않는다. (예: "로그인은 이번 범위가 아니다")
- AI는 불확실한 부분을 `[NEEDS CLARIFICATION: 질문]` 으로 표시하며, **최대 3개**까지만 남긴다. 남으면 선택지(A/B/C)와 함께 질문하므로 답해 준다.
- AI가 설명을 읽고 영어 짧은 이름(2~4 단어)을 정해 `specs/001-todo-list-app/` 같은 폴더를 만든다. 두 번째 기능은 `002-...` 가 된다.
- git 확장을 설치했다면 같은 이름의 브랜치(`001-todo-list-app`)가 만들어지고 자동으로 체크아웃되며, `.specify/feature.json` 에 `"feature_directory": "specs/001-todo-list-app"` 이 기록된다.
- 현재 작업 중인 기능 폴더는 `.specify/feature.json` 에 기록된다. **git 브랜치를 바꿔도 활성 기능은 바뀌지 않는다는 점**에 주의한다.

## 산출물

```
specs/001-todo-list-app/         ← 번호(001)는 자동, 이름(todo-list-app)은 AI가 정함
├── spec.md                      ← 기능 명세
└── checklists/
    └── requirements.md          ← 명세 품질 자동 점검표
```

`spec.md` 의 주요 구성:

| 섹션 | 내용 |
| --- | --- |
| User Scenarios & Testing | 우선순위(P1, P2, P3)가 붙은 사용자 스토리 + Given/When/Then 인수 조건 |
| Edge Cases | 빈 입력, 아주 긴 텍스트 같은 경계 상황 |
| Functional Requirements | `FR-001: 시스템은 사용자가 할 일을 추가할 수 있어야 한다(MUST)` 형식 |
| Key Entities | 할 일(Todo) 같은 핵심 개념과 속성 |
| Success Criteria | `SC-001: 사용자는 5초 안에 할 일을 추가할 수 있다` 처럼 **측정 가능한 기준** |
| Assumptions | AI가 합리적으로 가정한 내용 |

## 체크리스트

- [ ] `specs/001-todo-list-app/spec.md` 가 생성되었다. (파일 위쪽에 Feature Branch: 001-todo-list-app 이 적혀 있다)
- [ ] `.specify/feature.json` 이 `specs/001-todo-list-app` 을 가리킨다.
- [ ] `spec.md` 에 HTML, JavaScript, localStorage 같은 **구현 용어가 없다**(있다면 지우라고 요청).
- [ ] 사용자 스토리마다 **우선순위(P1~)** 와 **인수 조건(Given/When/Then)** 이 있다.
- [ ] 성공 기준이 숫자나 관찰 가능한 결과로 **측정 가능**하다.
- [ ] `checklists/requirements.md` 의 항목이 대부분 `[x]` 이다.
- [ ] (git 확장 사용 시) `git branch` 결과에 `* 001-todo-list-app` 과 `main` 이 보인다.

---

# 4 단계: 명확화(Clarify) — 모호함 없애기

**목적** — 계획을 세우기 전에, 명세에서 **덜 정해진 부분을 AI가 질문**하고 답을 명세에 다시 반영한다. "모호한 명세 위에 계획을 세우는" 실수를 막는다.

**입력** (초점 영역은 선택)

```text
/speckit-clarify 할 일 입력 규칙(빈 값, 최대 길이, 중복 허용 여부)과 삭제할 때 확인 절차를 중심으로 확인해 줘.
```

AI가 질문을 **한 번에 하나씩, 최대 5개** 보여 준다. 보통 추천 답(Recommended)과 선택지 표가 함께 나온다.

```text
Q1: 할 일 텍스트의 최대 길이는?
| Option | Answer |
| A | 100자 |
| B | 200자 |
| C | 제한 없음 |
Recommended: B ...
```

→ `B` 처럼 기호로 답하거나, `추천대로` / 직접 짧게 답하면 된다. 그만하려면 `done` 이라고 입력한다.

## 규칙

- 질문에는 **짧게** 답한다(선택지 기호 또는 5단어 이내). 길게 설명하면 다음 질문으로 넘어가기 어렵다.
- 모르는 질문은 "추천대로"라고 답해도 된다. 다만 **비즈니스 결정**(예: 삭제 확인 여부)은 직접 정한다.
- 명확화는 **plan 이전**에 한다. plan 이후에 명세가 바뀌면 plan부터 다시 만들어야 한다.
- 이 단계는 선택이지만, 처음 배울 때는 **반드시 해 보는 것**을 권장한다.

## 산출물

- `spec.md` 에 다음 섹션이 추가되고, 관련 요구사항(FR-xxx)도 함께 갱신된다.

```markdown
## Clarifications

### Session 2026-10-10
- Q: 할 일 텍스트의 최대 길이는? → A: 200자
- Q: 공백만 입력하면? → A: 추가하지 않고 안내 문구를 보여 준다
- Q: 삭제 시 확인 대화상자를 띄우는가? → A: 띄우지 않는다
```

## 체크리스트

- [ ] `spec.md` 에 `## Clarifications` → `### Session 날짜` 섹션이 생겼다.
- [ ] 답한 내용이 Functional Requirements / Edge Cases 에도 반영되었다.
- [ ] `[NEEDS CLARIFICATION` 문자열이 spec.md 에 남아 있지 않다.

---

# 5 단계: 계획(Plan) — 어떻게 만들 것인가

**목적** — 이제서야 **기술 스택과 구조**를 정한다. AI는 명세 + 헌법을 바탕으로 설계 문서를 만들고, 설계가 헌법을 어기지 않는지(**Constitution Check**) 검사한다.

**입력**

```text
/speckit-plan 빌드 도구 없이 순수 HTML, CSS, JavaScript(ES 모듈)로 만든다. 화면은 index.html 하나다. 할 일 데이터를 다루는 로직은 src/todo.js 의 순수 함수로, 저장은 src/storage.js 에서 localStorage를 사용하고, 화면 그리기와 이벤트 처리는 src/app.js 가 맡는다. 테스트는 tests/todo.test.js 에 Node.js 내장 테스트 러너(node --test)로 작성하고, package.json 에는 "type": "module" 만 지정하며 외부 의존성은 두지 않는다. 로컬 실행은 python3 -m http.server 로 한다.
```

**추가 입력 (선택) — 요구사항 품질 체크리스트**

```text
/speckit-checklist 사용자 경험(UX)과 데이터 보존 요구사항이 빠짐없고 명확한지 점검하는 체크리스트를 만들어 줘.
```

## 규칙

- 기술 선택은 **이 단계에서만** 한다. 구체적일수록(파일 이름, 실행 방법까지) 결과가 안정적이다.
- AI는 Phase 0(조사) → Phase 1(설계) 순으로 문서를 만들며, `plan.md` 의 **Constitution Check** 에서 위반이 있으면 **Complexity Tracking** 에 사유를 적어야 한다. 이유 없는 위반이 있으면 plan을 다시 요청한다.
- 헌법과 충돌하는 요청(예: 헌법은 "프레임워크 금지"인데 React 사용)은 AI가 지적해야 정상이다. 지적하지 않으면 사람이 잡아낸다.
- `/speckit-checklist` 가 만든 체크리스트는 **"요구사항이 잘 쓰였는가"를 점검**하는 것이지 구현 완료 표시가 아니다. 검토자가 직접 읽고 만족할 때만 `[x]` 로 바꾼다.
- 체크되지 않은 체크리스트가 있으면 7단계 `/speckit-implement` 가 진행 전에 **계속할지 물어본다**.

## 산출물

```
specs/001-todo-list-app/
├── spec.md
├── plan.md            ← 요약, 기술 맥락, Constitution Check, 프로젝트 구조
├── research.md        ← 기술 결정과 근거·대안 (Phase 0)
├── data-model.md      ← 엔티티(Todo: id, text, completed, createdAt …)와 검증 규칙 (Phase 1)
├── contracts/         ← 외부 인터페이스가 있을 때 (모듈 함수 계약 등, 없을 수도 있음)
├── quickstart.md      ← 기능을 검증하는 실행 시나리오 (Phase 1)
└── checklists/
    ├── requirements.md
    └── ux.md          ← /speckit-checklist 결과 (이름은 주제에 따라 다름)
```

## 체크리스트

- [ ] `plan.md` 의 Technical Context 에 언어·저장소·테스트·실행 방법이 채워져 있다(`NEEDS CLARIFICATION` 없음).
- [ ] `plan.md` 의 Constitution Check 가 모두 통과(PASS)이거나, 위반 사유가 Complexity Tracking 에 적혀 있다.
- [ ] `research.md`, `data-model.md`, `quickstart.md` 가 생성되었다.
- [ ] Project Structure 에 `index.html`, `src/todo.js`, `src/storage.js`, `src/app.js`, `tests/todo.test.js` 가 보인다.
- [ ] (선택) `checklists/` 의 사용자 정의 체크리스트를 직접 읽고 만족한 항목만 `[x]` 로 바꿨다.

---

# 6 단계: 작업 분해(Tasks)와 일관성 점검(Analyze)

**목적** — 설계 문서를 **실행 가능한 작업 목록(tasks.md)** 으로 쪼개고, 구현 전에 spec·plan·tasks 사이에 **모순·누락이 없는지** 점검한다.

**입력**

```text
/speckit-tasks 헌법의 테스트 우선 원칙에 따라 테스트 작업을 포함해 줘.
```

```text
/speckit-analyze
```

## 규칙

- 작업은 **사용자 스토리 단위**로 묶인다: Phase 1 Setup → Phase 2 Foundational → Phase 3+ 사용자 스토리별(P1부터) → 마지막 Polish.
- 작업 형식: `- [ ] T001 [P] [US1] 설명 (파일 경로)`
  - `T001` 실행 순서 번호, `[P]` 병렬 가능(서로 다른 파일·의존성 없음), `[US1]` 해당 사용자 스토리
- 테스트 작업은 **요청했을 때만** 생성된다. 헌법에 테스트 우선 원칙이 있다면 위 입력처럼 명시한다.
- `/speckit-analyze` 는 **읽기 전용**이다. 파일을 고치지 않고 보고서(CRITICAL/HIGH/MEDIUM/LOW)만 낸다. 문제가 나오면 **원본 문서(spec/plan/tasks)를 고친 뒤** 다시 analyze 한다.
- 특히 **CRITICAL**(헌법 위반, 요구사항에 대응하는 작업 없음)은 구현 전에 반드시 해결한다.

## 산출물

- `specs/001-todo-list-app/tasks.md`

```markdown
## Phase 1: Setup
- [ ] T001 Create project structure (index.html, src/, tests/, package.json)
- [ ] T002 [P] Add base styles in src/style.css

## Phase 3: User Story 1 - 할 일 추가하고 보기 (Priority: P1) 🎯 MVP
### Tests for User Story 1
- [ ] T005 [P] [US1] addTodo 단위 테스트 작성 in tests/todo.test.js
### Implementation for User Story 1
- [ ] T006 [US1] addTodo 구현 in src/todo.js
...
```

- `/speckit-analyze` 결과: 발견 사항 표, 요구사항↔작업 커버리지 표, 헌법 정합성 이슈, 다음 행동 제안 (콘솔 출력)

## 체크리스트

- [ ] `tasks.md` 의 모든 작업이 `- [ ] T번호` 형식이고 **파일 경로**가 적혀 있다.
- [ ] spec.md 의 모든 사용자 스토리(US1, US2 …)가 각각 Phase 로 존재한다.
- [ ] 테스트 작업이 해당 구현 작업보다 **앞에** 있다.
- [ ] `/speckit-analyze` 에 CRITICAL 이슈가 없다(있으면 고치고 재실행).
- [ ] 요구사항 커버리지가 100%에 가깝다(작업이 없는 FR이 없다).

---

# 7 단계: 구현(Implement)과 수렴(Converge)

**목적** — `tasks.md` 의 작업을 순서대로 실행해 **실제 코드**를 만들고, 완성된 코드가 명세·계획·작업을 **모두 만족하는지 검증**한다. 부족하면 작업을 추가하고 다시 구현한다.

**입력**

```text
/speckit-implement
```

큰 기능이라면 단계별로 끊어서 진행할 수 있다.

```text
/speckit-implement Phase 1과 Phase 2만 먼저 진행해 줘.
```

구현이 끝나면:

```text
/speckit-converge
```

## 규칙

- 구현 전, AI는 `checklists/` 의 체크 상태를 확인하고 **미완료 항목이 있으면 계속할지 묻는다.** 학습용이면 `yes` 로 진행해도 된다.
- Claude Code가 파일 생성·명령 실행(`node --test` 등) **권한을 물어보면** 내용을 확인하고 허용한다.
- 완료된 작업은 `tasks.md` 에서 `[X]` 로 바뀐다. 이 표시로 진행 상황을 추적한다.
- **수정이 필요하면 코드보다 명세를 먼저 고친다.** (예: 요구사항 변경 → spec.md 수정 → plan/tasks 갱신 → implement)
- `/speckit-converge` 가 **✅ Converged** 를 보고할 때까지 `implement → converge` 를 반복한다. 남은 작업이 있으면 converge가 `tasks.md` 끝에 새 작업을 추가한다.

## 산출물

```
my-todo/
├── index.html
├── package.json          {"type": "module"}  ← 외부 의존성 없음
├── src/
│   ├── todo.js           ← 순수 함수 (addTodo, toggleTodo, removeTodo, filterTodos, countActive …)
│   ├── storage.js        ← localStorage 저장/불러오기 (키 예: my-todo:todos)
│   ├── app.js            ← 화면 렌더링·이벤트
│   └── style.css
├── tests/
│   └── todo.test.js
└── specs/001-todo-list-app/tasks.md   ← 모든 작업이 [X]
```

- `/speckit-converge` 결과: `✅ Converged — the implementation satisfies the spec, plan, and tasks.` 또는 추가된 작업 목록

## 체크리스트

- [ ] `tasks.md` 의 모든 작업이 `[X]` 이다.
- [ ] `node --test` 가 `# fail 0` 으로 통과한다.
- [ ] [SAMPLE.md](SAMPLE.md) 의 순서대로 앱을 실행하고, 모든 시나리오(추가·완료·데이터 유지·삭제·걸러 보기·키보드)가 명세대로 동작함을 확인했다.
- [ ] `/speckit-converge` 가 **Converged** 를 보고했다.

---

# 8 단계: (도전) 두 번째 기능 추가 — 명세부터 다시

**목적** — SDD에서는 **변경도 명세에서 시작한다.** 이미 완성된 앱에 마감일 기능을 새 기능 폴더(`specs/002-…`)로 추가하며 2~7단계를 한 번 더 돌린다.

**입력** — 7단계까지 끝낸 상태에서 Claude Code에 순서대로

```text
/speckit-specify 기존 할 일 앱에 마감일 기능을 추가한다. 사용자는 할 일에 선택적으로 마감일을 지정할 수 있고, 마감일이 지난 미완료 할 일은 눈에 띄게 표시된다. 목록을 마감일이 가까운 순으로 정렬해 볼 수 있다. 기존에 저장된 마감일 없는 할 일도 그대로 보여야 한다.
```
```text
/speckit-clarify
```
```text
/speckit-plan 기존 구조(src/todo.js, src/storage.js, src/app.js)를 유지하고, 마감일은 HTML date 입력과 ISO 날짜 문자열(YYYY-MM-DD)로 저장한다. 기존에 저장된 마감일 없는 데이터도 그대로 읽혀야 한다.
```
```text
/speckit-tasks 헌법의 테스트 우선 원칙에 따라 테스트 작업을 포함해 줘.
```
```text
/speckit-analyze
```
```text
/speckit-implement
```
```text
/speckit-converge
```

## 규칙

- 헌법(2단계)은 다시 만들지 않는다. 프로젝트당 한 번이다.
- 저장 데이터 형식이 바뀌므로 **예전 데이터 호환**(마감일 없는 할 일)을 명세·테스트에 꼭 포함한다.
- 새 기능 폴더가 만들어지면 `.specify/feature.json` 이 그 폴더를 가리킨다. 001 폴더의 문서는 그대로 남아 이력이 된다.

## 산출물

```
specs/
├── 001-todo-list-app/        ← 그대로 유지
└── 002-…/                    ← 예: 002-todo-due-date (이름은 AI가 정함)
    ├── spec.md  plan.md  research.md  data-model.md  quickstart.md  tasks.md
    └── checklists/ contracts/
```

## 체크리스트

- [ ] `specs/002-…` 폴더가 새로 생겼고 `001-todo-list-app` 은 그대로다.
- [ ] `.specify/feature.json` 이 002 폴더를 가리킨다. (git 확장 사용 시 `git branch` 에 `002-…` 브랜치)
- [ ] `node --test` 가 통과하고, [SAMPLE.md](SAMPLE.md) 8단계(마감일)와 5단계(기존 기능) 시나리오가 모두 동작한다.
- [ ] `/speckit-converge` 가 **Converged** 를 보고했다.

---

# 부록 A. CLAUDE.md 규칙 조각

Spec Kit 프로젝트에서 Claude Code가 지켜야 할 규칙을 프로젝트 루트의 `CLAUDE.md` 에 붙여 넣어 두면, 단계 밖에서 대화할 때도 SDD 흐름을 지킨다.

```markdown
## Spec-Driven Development 규칙 (Spec Kit)

- 이 프로젝트는 GitHub Spec Kit으로 스펙 주도 개발을 한다. 원칙은 `.specify/memory/constitution.md` 를 따른다.
- 기능 문서는 `specs/NNN-기능이름/` (예: `specs/001-todo-list-app/`) 에 있다. 현재 기능은 `.specify/feature.json` 을 확인한다.
- 명세(`spec.md`)에는 기술 스택을 쓰지 않는다. 기술 결정은 `plan.md` 와 `research.md` 에만 기록한다.
- 요구사항이 바뀌면 코드부터 고치지 말고 `spec.md` → `/speckit-plan` → `/speckit-tasks` 순서로 갱신을 제안한다.
- 구현은 `tasks.md` 의 작업 순서를 따르고, 완료한 작업은 `[X]` 로 표시한다.
- 헌법 원칙과 충돌하는 요청을 받으면 구현하기 전에 충돌을 먼저 알린다.
- 문서와 화면 문구는 한국어로 작성한다.
```

# 부록 B. 자주 겪는 문제

| 증상 | 원인 / 해결 |
| --- | --- |
| Finder나 `ls` 에서 `.claude`, `.specify` 폴더가 안 보인다 | 이름이 `.` 으로 시작하는 **숨김 폴더**다. 터미널에서 `ls -a` 또는 `ls .claude/skills`, Finder에서는 `⌘ + Shift + .` 로 표시. 홈의 `~/.claude` 가 아니라 **프로젝트 폴더 안의** `.claude` 를 봐야 한다 |
| `command not found: specify` | `uv tool install` 후 PATH 미반영. 터미널을 새로 열거나 `uv tool update-shell` 실행 |
| `/speckit-...` 가 Claude Code에서 안 보인다 | 프로젝트 폴더(`my-todo`) **안에서** `claude` 를 실행했는지 확인. `.claude/skills/` 존재 여부 확인 |
| 인터넷 글처럼 `/speckit.specify` 를 입력했더니 안 된다 | Claude Code 통합은 스킬 방식이라 `/speckit-specify` (하이픈) 사용 |
| `--ai` 옵션 오류 | 현재 버전은 `--integration claude` |
| 다른 기능 폴더를 작업하고 싶다 | `.specify/feature.json` 의 `feature_directory` 를 수정하거나 환경 변수 `SPECIFY_FEATURE_DIRECTORY` 지정 |
| 브라우저에서 화면이 비어 있다 | ES 모듈은 `file://` 로 열면 막힌다. 반드시 `python3 -m http.server` 로 띄운 주소로 접속 |
| 대화가 길어져 AI가 앞 내용을 헷갈린다 | 산출물이 파일로 남아 있으므로 단계 사이에 `/clear` 해도 된다 |

# 부록 C. 용어 정리

| 용어 | 뜻 |
| --- | --- |
| Constitution (헌법) | 프로젝트의 불변 원칙. 모든 계획과 구현의 검사 기준 |
| Spec (명세) | 무엇을·왜 만드는지. 사용자 스토리, 요구사항, 성공 기준 |
| Plan (계획) | 어떻게 만드는지. 기술 스택, 구조, 데이터 모델 |
| Tasks (작업) | 계획을 실행 순서대로 쪼갠 체크리스트 |
| Converge (수렴) | 코드가 명세를 모두 만족하는 상태에 도달했는지 검증하는 것 |
| User Story / P1 | 사용자 관점의 기능 단위 / 우선순위(P1이 가장 중요, MVP) |
| FR / SC | Functional Requirement(기능 요구사항) / Success Criteria(성공 기준) |
| `[P]` | 다른 작업과 병렬로 해도 되는 작업 표시 |

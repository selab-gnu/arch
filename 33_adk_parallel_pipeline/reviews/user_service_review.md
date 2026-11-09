# PR 리뷰: user_service.py

❌ Request changes — 임의 코드 실행, 비밀키 유출, SQL·명령어 인젝션 등 HIGH 보안 문제와 심각한 성능 문제가 있어 병합 전 수정이 필요합니다.

## 반드시 고칠 것(Blocking)

1. **[HIGH] 6줄 — API 비밀키 하드코딩**
   - 저장소와 로그를 통해 키가 유출될 수 있습니다.
   - 노출된 키를 즉시 폐기·재발급하고 Secret Manager 또는 `os.environ["API_SECRET"]`을 사용하세요.

2. **[HIGH] 23줄 — 안전하지 않은 `pickle` 역직렬화**
   - 신뢰할 수 없는 바이트를 `pickle.loads()`로 처리하면 임의 코드가 실행될 수 있습니다.
   - JSON으로 교체하고 스키마와 입력 크기를 검증하세요.

3. **[HIGH] 31줄 — 외부 입력을 `eval()`로 실행**
   - 임의 코드 실행이 가능합니다.
   - 할인식 문법을 제한적으로 파싱하거나 허용된 연산자만 처리하는 AST 파서를 사용하세요.

4. **[HIGH] 18~19줄 — 경로 및 셸 명령어 인젝션**
   - 검증되지 않은 `user_dir`를 명령 문자열에 연결하고 `shell=True`로 실행하고 있습니다.
   - `Path.resolve()` 후 승인된 루트 내부인지 확인하고 셸 없이 인자 목록으로 실행하세요.
   ```python
   subprocess.run(["tar", "-czf", out, "--", user_dir], check=True)
   ```

5. **[HIGH] 9~12줄 — SQL 인젝션 및 DB 자원 관리**
   - 사용자 입력을 SQL 문자열에 직접 삽입하고, DB 연결도 닫지 않아 호출 누적 시 파일 핸들·메모리·DB 잠금이 고갈될 수 있습니다.
   - 파라미터 바인딩과 컨텍스트 관리자를 사용하고 `users(name)` 인덱스를 추가하세요.
   ```python
   def find_user(username):
       with sqlite3.connect(DB_PATH) as conn:
           return conn.execute(
               "SELECT id, name, email FROM users WHERE name = ?",
               (username,),
           ).fetchall()
   ```

6. **[HIGH] 36줄 — 중복 이메일 탐색의 O(n²) 복잡도**
   - 이중 반복과 리스트 멤버십 검사로 동일한 사용자 쌍을 양방향으로 비교합니다.
   - 집합을 사용해 기대 시간 O(n), 공간 O(n)으로 개선하세요.
   ```python
   def find_duplicate_emails(users):
       seen, emitted = set(), set()
       duplicates = []
       for user in users:
           email = user["email"]
           if email in seen and email not in emitted:
               duplicates.append(email)
               emitted.add(email)
           seen.add(email)
       return duplicates
   ```

## 권장 사항(Non-blocking)

- **[MEDIUM] 18줄:** `user_dir`는 `Path.resolve()` 후 승인된 루트 디렉터리 내부인지 확인하세요. 고정된 `/tmp/backup.tar.gz`는 심볼릭 링크 공격과 요청 간 충돌 가능성이 있으므로 `tempfile.NamedTemporaryFile()` 등으로 전용 임시 파일을 생성하세요.
- **[MEDIUM] 27줄:** 비밀번호에 빠르고 솔트 없는 MD5를 사용하지 말고 Argon2id, bcrypt 또는 무작위 솔트를 적용한 `hashlib.scrypt()`를 사용하세요.
- **[MEDIUM] 47줄:** 이름·이메일의 CSV 수식 인젝션을 막기 위해 `csv.writer`로 이스케이프하고 `=`, `+`, `-`, `@` 접두 값에는 `'`를 붙이세요. 문자열 `+=` 누적도 최악 O(L²)이므로 한 번에 결합하도록 개선하세요.
- **[MEDIUM] 54줄:** `active_list`를 집합으로 변환해 O(nm) 멤버십 검사를 O(n+m)으로 개선하세요.
- **스타일:** 2줄의 다중 import를 각각 분리하고, 35·38줄의 연산자 주변에 PEP 8 공백을 추가하세요.

## 잘한 점

- 별도로 보고된 긍정적인 사항은 없습니다.

---

## 🔒 보안 리뷰

HIGH 5건, MEDIUM 3건, LOW 1건

- [HIGH] 6줄 — API 비밀키가 소스에 하드코딩되어 저장소·로그를 통해 유출될 수 있음 — 해당 키를 즉시 폐기·재발급하고 Secret Manager 또는 `os.environ["API_SECRET"]` 사용
- [HIGH] 12줄 — 사용자 입력을 SQL 문자열에 직접 삽입하여 SQL 인젝션 가능 — `cur.execute("SELECT id, name, email FROM users WHERE name = ?", (username,))`
- [MEDIUM] 18줄 — `user_dir` 검증이 없어 허용되지 않은 시스템 경로를 백업할 수 있음 — `Path.resolve()` 후 승인된 루트 디렉터리 내부인지 확인
- [LOW] 18줄 — 고정된 `/tmp/backup.tar.gz` 사용으로 심볼릭 링크 공격이나 다른 요청과의 충돌 가능 — `tempfile.NamedTemporaryFile()` 등으로 전용 임시 파일 생성
- [HIGH] 19줄 — 입력값을 셸 명령에 연결하고 `shell=True`로 실행하여 명령어 인젝션 가능 — `subprocess.run(["tar", "-czf", out, "--", user_dir], check=True)` 사용
- [HIGH] 23줄 — 신뢰할 수 없는 바이트를 `pickle.loads()`로 역직렬화하면 임의 코드 실행 가능 — JSON으로 교체하고 스키마·크기 검증 수행
- [MEDIUM] 27줄 — 비밀번호를 빠르고 솔트 없는 MD5로 해시하여 크래킹에 취약 — Argon2id, bcrypt 또는 `hashlib.scrypt()`와 무작위 솔트 사용
- [HIGH] 31줄 — 외부 입력을 `eval()`로 실행하여 임의 코드 실행 가능 — 할인식 문법을 제한적으로 파싱하거나 허용 연산자만 처리하는 AST 파서 사용
- [MEDIUM] 47줄 — 이름·이메일이 `=`, `+`, `-`, `@`로 시작하면 보고서를 스프레드시트로 열 때 CSV 수식 인젝션 가능 — `csv.writer`로 이스케이프하고 위험한 접두 문자는 `'`를 붙여 무력화

## 🎨 스타일 리뷰

HIGH 0건, MEDIUM 1건, LOW 1건

- [MEDIUM] 2줄 — `E401`: 한 줄에 여러 모듈을 import했습니다(1곳). — 각각 별도 줄로 분리하세요.
  ```python
  import os
  import pickle
  import sqlite3
  import subprocess
  ```

- [LOW] 35, 38줄 — `E225`: 연산자 주변 공백이 누락되었습니다(3곳). — PEP 8에 따라 공백을 추가하세요.
  ```python
  duplicates = []
  if i != j and users[i]['email'] == users[j]['email']:
  ```

## ⚡ 성능 리뷰

HIGH 2건, MEDIUM 2건

- [HIGH] 9줄 — `find_user`: DB 연결을 닫지 않아 호출이 누적되면 파일 핸들·메모리·DB 잠금이 고갈될 수 있습니다. `fetchall()`도 결과가 크면 O(k) 메모리를 사용하며, 인덱스가 없으면 조회가 O(n)입니다. — 컨텍스트 관리자를 사용하고 `users(name)` 인덱스를 추가하세요. 조회는 통상 O(log n + k)로 개선됩니다.
  ```python
  def find_user(username):
      with sqlite3.connect(DB_PATH) as conn:
          return conn.execute(
              "SELECT id, name, email FROM users WHERE name = ?",
              (username,),
          ).fetchall()
  ```

- [HIGH] 36줄 — `find_duplicate_emails`: 이중 반복과 리스트 멤버십 검사로 O(n²), 결과 저장에 O(n) 메모리를 사용합니다. 동일한 사용자 쌍을 양방향으로 불필요하게 비교합니다. — 집합 두 개로 한 번만 순회하면 기대 시간 O(n), 공간 O(n)입니다.
  ```python
  def find_duplicate_emails(users):
      seen, emitted = set(), set()
      duplicates = []
      for user in users:
          email = user["email"]
          if email in seen and email not in emitted:
              duplicates.append(email)
              emitted.add(email)
          seen.add(email)
      return duplicates
  ```

- [MEDIUM] 47줄 — `build_report`: 반복문 안의 문자열 `+=`는 매번 기존 내용을 복사하여 최악 O(L²)의 시간과 불필요한 임시 메모리를 유발할 수 있습니다. — 한 번에 결합하면 전체 출력 길이 L에 대해 O(L) 시간·O(L) 결과 메모리입니다.
  ```python
  def build_report(users):
      return "".join(
          f"{u['id']},{u['name']},{u['email']}\n" for u in users
      )
  ```

- [MEDIUM] 54줄 — `get_active_users`: `active_list`가 리스트이면 각 ID마다 선형 검색하여, 사용자 ID 수 n과 활성 목록 크기 m에 대해 O(nm)입니다. — 활성 목록을 집합으로 변환하면 O(n+m), 추가 공간 O(m)입니다.
  ```python
  def get_active_users(user_ids, active_list):
      active = set(active_list)
      return [uid for uid in user_ids if uid in active]
  ```

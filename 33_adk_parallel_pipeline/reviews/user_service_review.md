# PR 리뷰: user_service.py

❌ Request changes — 운영 비밀키 노출과 SQL·명령어 인젝션, 임의 코드 실행 등 다수의 HIGH 보안 문제와 심각한 성능 문제가 있습니다.

## 반드시 고칠 것(Blocking)

1. **[HIGH, 6줄] 운영 API 비밀키 노출**
   - 노출된 키를 즉시 폐기·재발급하고 Secret Manager 또는 환경변수로 이동하세요.
   ```python
   API_SECRET = os.environ["API_SECRET"]
   ```

2. **[HIGH, 23줄] 안전하지 않은 `pickle` 역직렬화**
   - 신뢰할 수 없는 바이트를 `pickle.loads()`에 전달하면 임의 코드가 실행될 수 있습니다. JSON처럼 코드 실행 기능이 없는 형식을 사용하세요.
   ```python
   json.loads(raw_bytes.decode("utf-8"))
   ```

3. **[HIGH, 31줄] 외부 입력을 `eval()`로 실행**
   - 임의 코드 실행이 가능합니다. 허용 연산자만 처리하는 AST 기반 파서를 구현하고 입력 길이와 숫자 범위를 제한하세요.

4. **[HIGH, 17~19줄] 백업 경로 검증 누락 및 명령어 인젝션**
   - `user_dir`를 `Path.resolve()`한 뒤 허용된 루트 내부인지 확인하고, 호출자에게 해당 사용자 파일 접근 권한이 있는지 검사하세요.
   - `shell=True`를 제거하고 검증된 값을 인자 목록으로 전달하세요.
   ```python
   subprocess.run(
       ["tar", "-czf", out, "--", safe_user_dir],
       check=True,
   )
   ```

5. **[HIGH, 9~12줄] SQL 인젝션 및 DB 자원 관리 문제**
   - 사용자 입력을 SQL 문자열에 직접 삽입하지 말고 매개변수 바인딩을 사용하세요.
   - 연결을 컨텍스트 관리자로 닫고 `users(name)` 인덱스를 추가하세요. 인덱스가 없으면 O(N)이며, 인덱스 사용 시 O(log N + K)로 개선할 수 있습니다.
   ```python
   def find_user(username):
       with sqlite3.connect(DB_PATH) as conn:
           return conn.execute(
               "SELECT id, name, email FROM users WHERE name = ?",
               (username,),
           ).fetchall()

   # CREATE INDEX idx_users_name ON users(name);
   ```

6. **[HIGH, 36~39줄] 중복 이메일 탐색의 O(N²) 복잡도**
   - 모든 사용자 쌍을 비교하고 결과 리스트까지 선형 탐색하고 있습니다. `set` 두 개를 사용해 평균 O(N)으로 개선하세요.
   ```python
   def find_duplicate_emails(users):
       seen, duplicate_set = set(), set()
       duplicates = []
       for user in users:
           email = user["email"]
           if email in seen and email not in duplicate_set:
               duplicate_set.add(email)
               duplicates.append(email)
           seen.add(email)
       return duplicates
   ```

## 권장 사항(Non-blocking)

- **[MEDIUM, 27줄]** MD5는 비밀번호 저장에 부적합합니다. 솔트와 비용 조정이 가능한 Argon2id, bcrypt 또는 scrypt를 사용하세요.
  ```python
  hashlib.scrypt(
      pw.encode(),
      salt=os.urandom(16),
      n=2**14,
      r=8,
      p=1,
  )
  ```

- **[MEDIUM, 47줄]** 보고서 셀이 `=`, `+`, `-`, `@`로 시작하면 CSV 수식 인젝션이 발생할 수 있습니다. `csv.writer`를 사용하고 위험한 값 앞에 `'`를 붙이세요. 문자열 `+=` 누적도 최악 O(S²)이므로 `join`으로 변경하세요.
  ```python
  return "".join(
      f"{u['id']},{u['name']},{u['email']}\n" for u in users
  )
  ```

- **[MEDIUM, 54줄]** `active_list`가 리스트이면 O(N×M)입니다. 한 번 `set`으로 변환해 평균 O(N+M)으로 개선하세요.
  ```python
  active = set(active_list)
  return [uid for uid in user_ids if uid in active]
  ```

- **[LOW, 18줄]** 고정된 `/tmp/backup.tar.gz` 대신 `tempfile.NamedTemporaryFile()` 또는 `mkstemp()`로 예측 불가능한 전용 임시 파일을 생성하세요.

- **[MEDIUM/LOW, 2·35·38줄]** import를 모듈별로 분리해 알파벳순으로 정리하고, 대입·비교 연산자 양쪽에 공백을 추가해 `E401` 및 `E225`를 해소하세요.
  ```python
  import hashlib
  import os
  import pickle
  import sqlite3
  import subprocess

  duplicates = []
  if i != j and users[i]["email"] == users[j]["email"]:
  ```

---

## 🔒 보안 리뷰

HIGH 6건, MEDIUM 2건, LOW 1건

- [HIGH] 6줄 — 운영 API 비밀키가 소스 코드에 노출됨 — 키를 즉시 폐기·재발급하고 Secret Manager 또는 환경변수로 이동: `API_SECRET = os.environ["API_SECRET"]`
- [HIGH] 12줄 — 사용자 입력을 SQL 문자열에 삽입해 SQL 인젝션 가능 — 매개변수 바인딩 사용: `cur.execute("SELECT id, name, email FROM users WHERE name = ?", (username,))`
- [HIGH] 17~18줄 — `user_dir`의 경로 및 접근 권한 검증이 없어 허용되지 않은 파일까지 백업할 수 있음 — `Path.resolve()` 후 허용된 루트 경로 내부인지 확인하고 호출자의 해당 사용자 접근 권한을 검사
- [LOW] 18줄 — 고정된 `/tmp/backup.tar.gz` 사용으로 심볼릭 링크 공격이나 파일 덮어쓰기 가능 — `tempfile.NamedTemporaryFile()` 또는 `mkstemp()`로 예측 불가능한 전용 파일 생성
- [HIGH] 19줄 — 외부 입력이 포함된 명령을 `shell=True`로 실행해 명령어 인젝션 가능 — 셸 없이 인자 목록 사용: `subprocess.run(["tar", "-czf", out, "--", safe_user_dir], check=True)`
- [HIGH] 23줄 — 신뢰할 수 없는 바이트를 `pickle.loads()`로 역직렬화하면 임의 코드 실행 가능 — JSON처럼 코드 실행 기능이 없는 형식을 사용: `json.loads(raw_bytes.decode("utf-8"))`
- [MEDIUM] 27줄 — MD5는 비밀번호 저장에 부적합하며 솔트와 비용 조정이 없음 — Argon2id, bcrypt 또는 scrypt 사용: `hashlib.scrypt(pw.encode(), salt=os.urandom(16), n=2**14, r=8, p=1)`
- [HIGH] 31줄 — 외부 입력을 `eval()`로 실행해 임의 코드 실행 가능 — 허용 연산자만 처리하는 AST 기반 파서를 구현하고 입력 길이·숫자 범위를 제한
- [MEDIUM] 47줄 — 이름이나 이메일이 `=`, `+`, `-`, `@`로 시작하면 보고서를 스프레드시트에서 열 때 CSV 수식 인젝션 가능 — `csv.writer`를 사용하고 위험한 셀 값 앞에 `'`를 붙여 무력화

## 🎨 스타일 리뷰

MEDIUM 1건, LOW 3건

- [MEDIUM] 2줄 — `E401`: 한 줄에 여러 모듈을 import함 — 모듈별로 분리하고 알파벳순으로 정리하세요.
  ```python
  import hashlib
  import os
  import pickle
  import sqlite3
  import subprocess
  ```

- [LOW] 35, 38줄 — `E225` 3건: 대입·비교 연산자 주변 공백 누락 — 연산자 양쪽에 공백을 추가하세요.
  ```python
  duplicates = []
  if i != j and users[i]["email"] == users[j]["email"]:
  ```

## ⚡ 성능 리뷰

HIGH 2건, MEDIUM 2건

- [HIGH] 9 — `find_user`가 DB 연결을 닫지 않아 반복 호출 시 연결·파일 디스크립터가 누적될 수 있고, `fetchall()`은 결과 전체를 메모리에 적재합니다. 인덱스가 없으면 시간 O(N), 결과 메모리 O(K)입니다. — 컨텍스트 관리와 인덱스를 사용하면 O(log N + K)로 개선할 수 있습니다.
  ```python
  def find_user(username):
      with sqlite3.connect(DB_PATH) as conn:
          return conn.execute(
              "SELECT id, name, email FROM users WHERE name = ?",
              (username,),
          ).fetchall()
  # CREATE INDEX idx_users_name ON users(name);
  ```

- [HIGH] 36, 37, 39 — 모든 사용자 쌍을 비교하고 `duplicates` 리스트까지 선형 탐색합니다. 시간 O(N²), 결과 저장 외에도 중첩 반복으로 CPU를 낭비합니다. — `set` 두 개를 사용하면 평균 O(N), 추가 메모리 O(N)입니다.
  ```python
  def find_duplicate_emails(users):
      seen, duplicate_set = set(), set()
      duplicates = []
      for user in users:
          email = user["email"]
          if email in seen and email not in duplicate_set:
              duplicate_set.add(email)
              duplicates.append(email)
          seen.add(email)
      return duplicates
  ```

- [MEDIUM] 47 — 반복문에서 문자열을 `+=`로 누적해 기존 내용을 반복 복사할 수 있습니다. 최악 시간 O(S²) 및 큰 임시 메모리 할당이 발생할 수 있습니다. — `join`을 사용하면 전체 출력 크기 S에 대해 O(S)입니다.
  ```python
  return "".join(
      f"{u['id']},{u['name']},{u['email']}\n" for u in users
  )
  ```

- [MEDIUM] 54 — `active_list`가 리스트이면 사용자마다 전체 목록을 탐색하므로 시간 O(N×M)입니다. — 한 번 `set`으로 변환하면 평균 O(N+M), 추가 메모리 O(M)입니다.
  ```python
  def get_active_users(user_ids, active_list):
      active = set(active_list)
      return [uid for uid in user_ids if uid in active]
  ```

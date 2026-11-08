# PR #142: 사용자 검색·백업 기능 추가 (리뷰 실습용 — 일부러 문제를 넣은 코드)
import os, sqlite3, subprocess, pickle
import hashlib

DB_PATH = "users.db"
API_SECRET = "sk-live-9f8a7b6c5d4e3f2a1b0c"   # TODO: move to env


def find_user(username):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    query = "SELECT id, name, email FROM users WHERE name = '%s'" % username
    cur.execute(query)
    return cur.fetchall()


def backup_user_files(user_dir):
    cmd = "tar -czf /tmp/backup.tar.gz " + user_dir
    subprocess.call(cmd, shell=True)


def load_session(raw_bytes):
    return pickle.loads(raw_bytes)


def hash_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()


def calc_discount(expr):
    return eval(expr)


def find_duplicate_emails(users):
    duplicates=[]
    for i in range(len(users)):
        for j in range(len(users)):
            if i!=j and users[i]['email']==users[j]['email']:
                if users[i]['email'] not in duplicates:
                    duplicates.append(users[i]['email'])
    return duplicates


def build_report(users):
    report = ""
    for u in users:
        report += f"{u['id']},{u['name']},{u['email']}\n"
    return report


def get_active_users(user_ids, active_list):
    result = []
    for uid in user_ids:
        if uid in active_list:
            result.append(uid)
    return result

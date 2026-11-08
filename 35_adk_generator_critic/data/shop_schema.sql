-- 실습용 가상 온라인 쇼핑몰 DB (SQLite). 모든 데이터는 가상입니다.
-- 컬럼 이름을 일부러 흔한 이름과 다르게 지었습니다(cust_name, ordered_at, unit_price_krw 등).
-- → LLM이 첫 시도에 'name', 'order_date' 같은 흔한 이름을 지어내면 Critic이 오류를 잡아 되돌려 보냅니다.

CREATE TABLE customers (
    cust_id      INTEGER PRIMARY KEY,
    cust_name    TEXT NOT NULL,
    grade        TEXT NOT NULL CHECK (grade IN ('BRONZE', 'SILVER', 'GOLD', 'VIP')),
    city         TEXT NOT NULL,
    joined_on    TEXT NOT NULL            -- 'YYYY-MM-DD'
);

CREATE TABLE products (
    prod_id         INTEGER PRIMARY KEY,
    prod_name       TEXT NOT NULL,
    category        TEXT NOT NULL,        -- 'electronics', 'books', 'food', 'fashion'
    unit_price_krw  INTEGER NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1   -- 1: 판매중, 0: 단종
);

CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    cust_id      INTEGER NOT NULL REFERENCES customers(cust_id),
    ordered_at   TEXT NOT NULL,           -- 'YYYY-MM-DD HH:MM:SS'
    status       TEXT NOT NULL CHECK (status IN ('PAID', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'REFUNDED'))
);

CREATE TABLE order_items (
    order_id     INTEGER NOT NULL REFERENCES orders(order_id),
    prod_id      INTEGER NOT NULL REFERENCES products(prod_id),
    qty          INTEGER NOT NULL,
    PRIMARY KEY (order_id, prod_id)
);

INSERT INTO customers VALUES
 (1, '김민준', 'VIP',    '서울', '2023-03-14'),
 (2, '이서연', 'GOLD',   '부산', '2024-01-09'),
 (3, '박지호', 'SILVER', '진주', '2024-07-22'),
 (4, '최유나', 'BRONZE', '서울', '2025-02-03'),
 (5, '정하준', 'GOLD',   '대구', '2025-05-17'),
 (6, '한소희', 'VIP',    '진주', '2022-11-30'),
 (7, '오지훈', 'BRONZE', '광주', '2026-01-12'),
 (8, '윤채원', 'SILVER', '서울', '2026-03-08');

INSERT INTO products VALUES
 (101, '노이즈캔슬링 헤드폰', 'electronics', 289000, 1),
 (102, '기계식 키보드',       'electronics', 139000, 1),
 (103, '4K 모니터 27인치',    'electronics', 459000, 1),
 (104, '파이썬 데이터 분석',  'books',        32000, 1),
 (105, '소프트웨어 아키텍처', 'books',        38000, 1),
 (106, '유기농 원두 1kg',     'food',         27000, 1),
 (107, '수제 그래놀라',       'food',         15000, 0),
 (108, '울 코트',             'fashion',     219000, 1),
 (109, '러닝화',              'fashion',     129000, 1),
 (110, '구형 USB 허브',       'electronics',  19000, 0);

INSERT INTO orders VALUES
 (1001, 1, '2026-08-03 10:12:00', 'DELIVERED'),
 (1002, 2, '2026-08-15 21:40:00', 'DELIVERED'),
 (1003, 1, '2026-09-01 09:05:00', 'DELIVERED'),
 (1004, 3, '2026-09-11 14:22:00', 'CANCELLED'),
 (1005, 6, '2026-09-20 18:30:00', 'DELIVERED'),
 (1006, 4, '2026-10-02 08:47:00', 'REFUNDED'),
 (1007, 5, '2026-10-05 13:15:00', 'SHIPPED'),
 (1008, 6, '2026-10-18 20:01:00', 'DELIVERED'),
 (1009, 2, '2026-10-25 11:11:00', 'PAID'),
 (1010, 8, '2026-11-01 16:45:00', 'PAID'),
 (1011, 1, '2026-11-03 19:20:00', 'SHIPPED'),
 (1012, 3, '2026-11-05 07:58:00', 'PAID');

INSERT INTO order_items VALUES
 (1001, 101, 1), (1001, 106, 2),
 (1002, 104, 1), (1002, 105, 1),
 (1003, 103, 1),
 (1004, 108, 1),
 (1005, 102, 1), (1005, 106, 3),
 (1006, 109, 1),
 (1007, 101, 1), (1007, 104, 2),
 (1008, 103, 2),
 (1009, 108, 1), (1009, 105, 1),
 (1010, 109, 2),
 (1011, 102, 1), (1011, 107, 4),
 (1012, 106, 1);

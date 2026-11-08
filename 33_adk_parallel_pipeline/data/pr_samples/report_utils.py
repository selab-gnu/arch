# PR #151: 월간 매출 리포트 유틸 추가 (리뷰 실습용 — 스타일·성능 위주로 문제가 있는 코드)
import json,csv
from datetime import datetime


class reportGenerator:
    def __init__(self, Sales):
        self.Sales = Sales

    def TotalByMonth(self):
        months = {}
        for s in self.Sales:
            m = s["date"][:7]
            if m in months.keys():
                months[m] = months[m] + s["amount"]
            else:
                months[m] = s["amount"]
        return months

    def top_products(self, n = 5):
        names = list(set([s["product"] for s in self.Sales]))
        totals = []
        for name in names:
            t = 0
            for s in self.Sales:
                if s["product"] == name: t += s["amount"]
            totals.append((name, t))
        totals.sort(key = lambda x: -x[1])
        return totals[:n]

    def fibonacci_growth(self, k):
        if k < 2: return k
        return self.fibonacci_growth(k - 1) + self.fibonacci_growth(k - 2)

    def export(self, path):
        f = open(path, "w")
        for m, v in self.TotalByMonth().items():
            f.write(m + "," + str(v) + "\n")
        f.close()

    def load_rates(self, path):
        for s in self.Sales:
            rates = json.load(open(path))
            s["amount_usd"] = s["amount"] * rates.get(s.get("currency", "USD"), 1.0)
        return self.Sales

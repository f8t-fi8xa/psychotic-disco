import sqlite3
from datetime import datetime

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''


conn = sqlite3.Connection(r"C:\Users\liams\Gallery\DB\resources\main.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()


'''input query here'''
cur.execute('''
SELECT * FROM products LIMIT 5
            ''')

for l in cur.fetchall():
    print("===========================================================")
    line = ""
    for k, v in dict(l).items():
        if k == "sale_date":
            v = datetime.fromtimestamp(v)
        line += f"{bcolors.BOLD}{bcolors.OKCYAN}{k}{bcolors.ENDC}: {v}, "
    print(line)

conn.commit()
conn.close()
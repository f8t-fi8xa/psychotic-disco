from flask import Flask, request, jsonify
import sqlite3
import os
from database.LightSpeed import Orders, Products, Sales, Suppliers
from database.utils import InitializeDB
from sql import make_select

db_name = "main"
db_path = fr"{InitializeDB.DEFAULT_LOC}\{db_name}.db"

app = Flask(__name__)

@app.post("/api/create")
def create():
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        for table in tables:
            cur.execute(f'''TABLE IF EXISTS "{table[0]}"''')
        conn.commit()
        InitializeDB.Database(conn).make_tables()
    return jsonify({"status": "success"})

# update routes
@app.post("/api/update")
def update():
    with sqlite3.connect(db_path) as conn:
        Orders(conn).update()
        #Products(conn).update()
        Sales(conn).update()
        Suppliers(conn).update()
    return jsonify({"status": "success"})

@app.post("/api/orders/update")
def update_orders():
    with sqlite3.connect(db_path) as conn:
        Orders(conn).update()
    return jsonify({"status": "success"})

@app.post("/api/products/update")
def update_products():
    with sqlite3.connect(db_path) as conn:
        Products(conn).update()
    return jsonify({"status": "success"})

@app.post("/api/sales/update")
def update_sales():
    with sqlite3.connect(db_path) as conn:
        Sales(conn).update()
    return jsonify({"status": "success"})

@app.post("/api/suppliers/update")
def update_suppliers():
    with sqlite3.connect(db_path) as conn:
        Suppliers(conn).update()
    return jsonify({"status": "success"})

# get routes

@app.post("/api/search")
def search():
    data = request.get_json()
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        inventory = data["inventory"]
        sales = data["sales"]

        price_min = inventory["price_min"]
        price_max = inventory["price_max"]
        count_min = inventory["count_min"]
        count_max = inventory["count_max"]
        name = inventory["name"]
        sku = inventory["sku"]
        supplier = inventory["supplier"]
        last_sold_date_min = inventory["last_sold_date_min"]
        last_sold_date_max = inventory["last_sold_date_max"]
        cat_1 = inventory["category_1"]
        cat_2 = inventory["category_2"]
        cat_3 = inventory["category_3"]
        in_store_active = inventory["in_store_active"]
        in_store_inactive = inventory["in_store_inactive"]
        online_active = inventory["online_active"]
        online_inactive = inventory["online_inactive"]
        sale_date_min = sales["sale_date_min"]
        sale_date_max = sales["sale_date_max"]
        qty_min = sales["quantity_min"]
        qty_max = sales["quantity_max"]
        revenue_min = sales["revenue_min"]
        revenue_max = sales["revenue_max"]
        grouping = sales["grouping"]

        in_store = None
        online = None
        if in_store_active and not in_store_inactive: in_store = 1
        elif not in_store_active and in_store_inactive: in_store = 0
        elif in_store_active == in_store_inactive: in_store = -1

        if online_active and not online_inactive: online = 1
        elif not online_active and online_inactive: online = 0
        elif online_active == online_inactive: online = -1

        if in_store is None and online is None: 
            in_store = -1
            online = -1

        if grouping == "Product" or grouping == "Register":
            grouping_value = "p.id"
            primary_fields = [
                {"name": "p.sku"}, 
                {"name": "su.name", "alias": "seller"}, 
                {"name": "p.category_2"}, 
                {"name": "p.category_3"},  
                {"name": "p.name"}, 
                {"name": "p.price"}, 
                {"name": "p.in_store"}, 
                {"name": "p.online"}
                ]

            secondary_fields = [
                {"name": "p.sku"},
                {"name": "p.created_at"},
                {"name": "si.seller"},
                {"name": "si.category_2"},
                {"name": "si.category_3"},
                {"name": "si.name"},
                {"name": "si.price"},
                {"name": "si.in_store"},
                {"name": "si.online"},
                {"name": "si.count", "alias": "count", "func": "SUM"}
                ]

        elif grouping == "Supplier":
            grouping_value = "p.supplier_id"
            primary_fields = [{"name": "su.name", "alias": "seller"}]

            secondary_fields = [{"name": "si.seller"}]
        elif grouping == "Category 1":
            grouping_value = "p.category_1"
            primary_fields = []

            secondary_fields = []
        elif grouping == "Category 2":
            grouping_value = "p.category_2"
            primary_fields = [{"name": "p.category_2"}]

            secondary_fields = [{"name": "si.category_2"}]
        elif grouping == "Category 3":
            grouping_value = "p.category_3"
            primary_fields = [{"name": "p.category_2"}, {"name": "p.category_3"}]

            secondary_fields = [{"name": "si.category_2"}, {"name": "si.category_3"}]
        elif grouping == "All":
            grouping_value = "NULL"
            primary_fields = []

            secondary_fields = []
        else:
            grouping_value = None
            primary_fields = [None]
            secondary_fields = [None]

        

        sale_interval = {
            "fields": [
                {"name": grouping_value, "alias": "grouping_value"},
                {"name": "p.id", "alias": "product_id"},
                {"func": "SUM", "name": "sp.count", "alias": "quantity"},
                {"func": "SUM", "name": "sp.discount_total", "alias": "discount"},
                {"name": "i.count"},
                {"func": "SUM", "name": "sp.price_total", "alias": "revenue"},
                {"func": "MAX", "name": "s.date", "alias": "last_sold"},
                {"name": "sp.tax_total", "alias": "tax", "func": "SUM"}
            ] + primary_fields,
            "main_table": {"name": "products", "alias": "p"},
            "tables": [
                {"name": "sale_products", "alias": "sp", "join_type": "LEFT", "link": ("p.id", "sp.product_id")},
                {"name": "sales", "alias": "s", "join_type": "LEFT", "link": ("sp.sale_id", "s.id")},
                {"name": "inventory", "alias": "i", "join_type": "LEFT", "link": ("p.id", "i.product_id")},
                {"name": "suppliers", "alias": "su", "join_type": "LEFT", "link": ("p.supplier_id", "su.id")},
            ],
            "conditions": [
                {"operator": "OR", "terms": [
                    {"operator": "=", "terms": ["sp.status", "'CONFIRMED'"]}, 
                    {"operator": "IS", "terms": ["sp.status", "NULL"]}
                ]},
                {"operator": "IS", "terms": ["p.deleted_at", "NULL"]},
                {"operator": "OR", "terms": [
                    {"operator": ">=", "terms": ["s.date", sale_date_min]}, 
                    {"operator": "<", "terms": [sale_date_min, 0]}
                ]},
                {"operator": "OR", "terms": [
                    {"operator": "<=", "terms": ["s.date", sale_date_max]}, 
                    {"operator": "<", "terms": [sale_date_max, 0]}
                ]},
                {"operator": ">=", "terms": ["p.price", price_min]},
                {"operator": "<=", "terms": ["p.price", price_max]},
                {"operator": "OR", "terms": [
                    {"operator": "AND", "terms": [
                        {"operator": ">=", "terms": ["i.count", count_min]}, 
                        {"operator": "<=", "terms": ["i.count", count_max]}
                    ]}, 
                    {"operator": "AND", "terms": [
                        {"operator": "IS", "terms": ["i.count", "NULL"]}, 
                        {"operator": "<=", "terms": [count_min, 0]}, 
                        {"operator": ">=", "terms": [count_max, 0]}
                    ]}
                ]},
                {"operator": "OR", "terms": [name, sku]},
                {"operator": "OR", "terms": [
                    supplier, 
                    {"operator": "AND", "terms": [
                        {"operator": "=", "terms": [supplier['terms'][0]['terms'][0], '"%%"']}, 
                        {"operator": "IS", "terms": ["p.supplier_id", "NULL"]}
                    ]}
                ]},
                cat_1, 
                cat_2,
                cat_3,
                {"operator": "OR", "terms": [
                    {"operator": "=", "terms": ["p.in_store", in_store]}, 
                    {"operator": "=", "terms": [in_store, -1]}
                ]},
                {"operator": "OR", "terms": [
                    {"operator": "=", "terms": ["p.online", online]}, 
                    {"operator": "=", "terms": [online, -1]}
                ]}
            ],
            "end": {
                "group": ["p.id"]
            }
        }

        main_query = {
            "fields": [
                {"name": "si.quantity", "alias": "quantity", "func": "SUM"},
                {"name": "si.discount", "alias": "discount", "func": "SUM"},
                {"name": "si.revenue", "alias": "revenue", "func": "SUM"},
                {"name": "si.last_sold", "alias": "last_sold", "func": "MAX"},
                {"name": "si.tax", "alias": "tax", "func": "SUM"}
            ] + secondary_fields,
            "main_table": {"name": "products", "alias": "p"},
            "tables": [
                {"name": "sale_interval", "alias": "si", "link": ("p.id", "si.product_id")}
            ],
            "conditions": [
                {"operator": "OR", "terms": [
                    {"operator": "AND", "terms": [
                        {"operator": ">=", "terms": ["si.quantity", qty_min]}, 
                        {"operator": "<=", "terms": ["si.quantity", qty_max]}
                    ]},
                    {"operator": "AND", "terms": [
                        {"operator": "<=", "terms": [qty_min, 0]}, 
                        {"operator": ">=", "terms": [qty_max, 0]},
                        {"operator": "IS", "terms": ["si.quantity", "NULL"]}
                    ]}
                ]},
                {"operator": "OR", "terms": [
                    {"operator": "AND", "terms": [
                        {"operator": ">=", "terms": ["si.revenue", revenue_min]}, 
                        {"operator": "<=", "terms": ["si.revenue", revenue_max]}
                    ]},
                    {"operator": "AND", "terms": [
                        {"operator": "<=", "terms": [revenue_min, 0]}, 
                        {"operator": ">=", "terms": [revenue_max, 0]},
                        {"operator": "IS", "terms": ["si.revenue", "NULL"]}
                    ]}
                ]},
                {"operator": "OR", "terms": [
                    {"operator": ">=", "terms": ["si.last_sold", last_sold_date_min]}, 
                    {"operator": "<", "terms": [last_sold_date_min, 0]}
                ]},
                {"operator": "OR", "terms": [
                    {"operator": "<=", "terms": ["si.last_sold", last_sold_date_max]}, 
                    {"operator": "<", "terms": [last_sold_date_max, 0]}
                ]},
            ],
        }

        if grouping_value != "NULL":
            main_query["end"] = {"group": ["grouping_value"]}

        product_result = cur.execute(f"WITH sale_interval AS ({make_select(sale_interval)}) {make_select(main_query)}").fetchall()
        return jsonify([dict(row) for row in product_result])

@app.post("/api/sales/get")
def get_sales():
    data = request.get_json()
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute('''
        CREATE TEMP VIEW IF NOT EXISTS intervals AS
        SELECT
        date,
        strftime('%Y-W%W', date(sales.date, 'unixepoch')) AS week,
        strftime('%Y-%m', date(sales.date, 'unixepoch')) AS month,
        strftime('%Y', date(sales.date, 'unixepoch')) || '-Q' || ((CAST(strftime('%m', date(sales.date, 'unixepoch')) AS INTEGER)+2)/3) AS quarter,
        strftime('%Y', date(sales.date, 'unixepoch')) AS year
        FROM sales''')

        conn.commit()

        inventory = data["inventory"]
        sales = data["sales"]

        price_min = inventory["price_min"]
        price_max = inventory["price_max"]
        count_min = inventory["count_min"]
        count_max = inventory["count_max"]
        name = inventory["name"]
        sku = inventory["sku"]
        supplier = inventory["supplier"]
        cat_1 = inventory["category_1"]
        cat_2 = inventory["category_2"]
        cat_3 = inventory["category_3"]
        in_store_active = inventory["in_store_active"]
        in_store_inactive = inventory["in_store_inactive"]
        online_active = inventory["online_active"]
        online_inactive = inventory["online_inactive"]
        date_min = sales["sale_date_min"]
        date_max = sales["sale_date_max"]
        qty_min = sales["quantity_min"]
        qty_max = sales["quantity_max"]
        revenue_min = sales["revenue_min"]
        revenue_max = sales["revenue_max"]
        register = sales["register"]
        interval = sales["interval"]
        grouping = sales["grouping"]

        in_store = None
        online = None

        if in_store_active and not in_store_inactive: in_store = 1
        elif not in_store_active and in_store_inactive: in_store = 0
        elif in_store_active == in_store_inactive: in_store = -1

        if online_active and not online_inactive: online = 1
        elif not online_active and online_inactive: online = 0
        elif online_active == online_inactive: online = -1

        if in_store is None and online is None: 
            in_store = -1
            online = -1

        if grouping == "Product":
            grouping_value = "p.id"
            grouping_label = "p.name"
        elif grouping == "Supplier":
            grouping_value = "p.supplier_id"
            grouping_label = "su.name"
        elif grouping == "Category 1":
            grouping_value = "p.category_1"
            grouping_label = "p.category_1"
        elif grouping == "Category 2":
            grouping_value = "p.category_2"
            grouping_label = "p.category_2"
        elif grouping == "Category 3":
            grouping_value = "p.category_3"
            grouping_label = "p.category_3"
        elif grouping == "Register":
            grouping_value = "r.id"
            grouping_label = "r.name"
        elif grouping == "All":
            grouping_value = "NULL"
            grouping_label = "NULL"
        else:
            grouping_value = "NULL"
            grouping_label = "NULL"

        sale_interval = {
            "fields": [
                {"name": grouping_value, "alias": "grouping_value"},
                {"name": grouping_label, "alias": "grouping_label"},
                {"name": interval, "alias": "interval"},
                {"name": "p.id", "alias": "product_id"},
                {"func": "SUM", "name": "sp.count", "alias": "quantity"},
                {"func": "SUM", "name": "sp.discount_total", "alias": "discount"},
                {"func": "SUM", "name": "sp.price_total", "alias": "revenue"},
            ],
            "main_table": {"name": "products", "alias": "p"},
            "tables": [
                {"name": "sale_products", "alias": "sp", "link": ("p.id", "sp.product_id")},
                {"name": "sales", "alias": "s", "link": ("sp.sale_id", "s.id")},
                {"name": "inventory", "alias": "i", "link": ("p.id", "i.product_id")},
                {"name": "suppliers", "alias": "su", "link": ("p.supplier_id", "su.id")},
                {"name": "intervals", "alias": "iv", "link": ("s.date", "iv.date")},
                {"name": "registers", "alias": "r", "link": ("s.register_id", "r.id")}
            ],
            "conditions": [
                {"operator": "=", "terms": ["sp.status", "'CONFIRMED'"]}, 
                {"operator": "!=", "terms": ["su.name", "'The Galleryat57'"]},
                {"operator": "IS", "terms": ["p.deleted_at", "NULL"]},
                {"operator": "OR", "terms": [
                    {"operator": ">=", "terms": ["s.date", date_min]}, 
                    {"operator": "<", "terms": [date_min, 0]}
                ]},
                {"operator": "OR", "terms": [
                    {"operator": "<=", "terms": ["s.date", date_max]}, 
                    {"operator": "<", "terms": [date_max, 0]}
                ]},
                {"operator": ">=", "terms": ["p.price", price_min]},
                {"operator": "<=", "terms": ["p.price", price_max]},
                {"operator": "OR", "terms": [
                    {"operator": "AND", "terms": [
                        {"operator": ">=", "terms": ["i.count", count_min]}, 
                        {"operator": "<=", "terms": ["i.count", count_max]}
                    ]}, 
                    {"operator": "AND", "terms": [
                        {"operator": "IS", "terms": ["i.count", "NULL"]}, 
                        {"operator": "<=", "terms": [count_min, 0]}, 
                        {"operator": ">=", "terms": [count_max, 0]}
                    ]}
                ]},
                {"operator": "OR", "terms": [name, sku]},
                {"operator": "OR", "terms": [
                    supplier, 
                    {"operator": "AND", "terms": [
                        {"operator": "=", "terms": [supplier['terms'][0]['terms'][0], "'%%'"]}, 
                        {"operator": "IS", "terms": ["p.supplier_id", "NULL"]}
                    ]}
                ]},
                cat_1, 
                cat_2,
                cat_3,
                {"operator": "OR", "terms": [
                    {"operator": "=", "terms": ["p.in_store", in_store]}, 
                    {"operator": "=", "terms": [in_store, -1]}
                ]},
                {"operator": "OR", "terms": [
                    {"operator": "=", "terms": ["p.online", online]}, 
                    {"operator": "=", "terms": [online, -1]}
                ]},
                {"operator": "OR", "terms": [
                    {"operator": "=", "terms": ["r.id", f"'{register}'"]},
                    {"operator": "=", "terms": [f"'{register}'", "'All'"]}
                ]}
            ],
            "end": {
                "group": ["interval", "p.id"]
            }
        }
        main_query = {
            "fields": [
                {"name": "si.grouping_value"},
                {"name": "si.grouping_label"},
                {"name": "si.interval"},
                {"name": "si.quantity", "alias": "quantity", "func": "SUM"},
                {"name": "si.discount", "alias": "discount", "func": "SUM"},
                {"name": "si.revenue", "alias": "revenue", "func": "SUM"},
            ],
            "main_table": {"name": "products", "alias": "p"},
            "tables": [
                {"name": "sale_interval", "alias": "si", "link": ("p.id", "si.product_id")}
            ],
            "conditions": [
                {"operator": "OR", "terms": [
                    {"operator": "AND", "terms": [
                        {"operator": ">=", "terms": ["si.quantity", qty_min]}, 
                        {"operator": "<=", "terms": ["si.quantity", qty_max]}
                    ]},
                    {"operator": "AND", "terms": [
                        {"operator": "<=", "terms": [qty_min, 0]}, 
                        {"operator": ">=", "terms": [qty_max, 0]},
                        {"operator": "IS", "terms": ["si.quantity", "NULL"]}
                    ]}
                ]},
                {"operator": "OR", "terms": [
                    {"operator": "AND", "terms": [
                        {"operator": ">=", "terms": ["si.revenue", revenue_min]}, 
                        {"operator": "<=", "terms": ["si.revenue", revenue_max]}
                    ]},
                    {"operator": "AND", "terms": [
                        {"operator": "<=", "terms": [revenue_min, 0]}, 
                        {"operator": ">=", "terms": [revenue_max, 0]},
                        {"operator": "IS", "terms": ["si.revenue", "NULL"]}
                    ]}
                ]}
            ],
            "end": {
                "group": ["interval"]
            }
        }

        if grouping_value != "NULL":
            main_query["end"]["group"].append("grouping_value")

        result = cur.execute(f"WITH sale_interval AS ({make_select(sale_interval)}) {make_select(main_query)}").fetchall()
        return jsonify([dict(row) for row in result])

if __name__ == "__main__":
    app.run(debug=True)
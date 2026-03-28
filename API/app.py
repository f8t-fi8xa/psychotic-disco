from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from mysql.connector import pooling
from dotenv import load_dotenv
import os
from LightSpeed import Orders, Products, Sales, Suppliers, Registers
from utils.sql import make_select
import secrets
import time
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf.csrf import CSRFProtect, generate_csrf

load_dotenv()

pool = pooling.MySQLConnectionPool(
    pool_size=5,
    pool_name='pool',
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
CORS(app, origins=os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000'), supports_credentials=True)
csrf = CSRFProtect(app)

limiter = Limiter(app=app, key_func=get_remote_address)

tokens = {}
users = {
    os.getenv("USER_0"): generate_password_hash(os.getenv("PASSWORD_0", "oh fuck"))
}

#security/https stuff

def verify_token(token):
    entry = tokens.get(token)
    if not entry:
        return None
    if entry['expires'] < time.time():
        tokens.pop(token)
        return None
    return entry['user']

def cookies_needed(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('auth_token')

        if not verify_token(token):
            return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    return decorated

@app.get("/api/csrf-token")
@csrf.exempt
def csrf_token():
    return jsonify({"token": generate_csrf()})

@app.post("/api/login")
@limiter.limit('5 per minute')
def login():
    data = request.get_json()
    username = users.get(data.get('username'), '')
    if not check_password_hash(username, data.get('password', '')):
        return jsonify({'error': 'Invalid Credentials'}), 401
    
    token = secrets.token_hex(32)
    tokens[token] = {'user': data['username'], 'expires': time.time() + 60*60*24}

    response = make_response(jsonify({"message": 'logged in successfully'}))
    response.set_cookie(
        key='auth_token',
        value=token,
        httponly=True,
        secure=True,
        samesite='None'
    )
    return response

@app.post("/api/logout")
def logout():
    token = request.cookies.get('auth_token')
    tokens.pop(token, None)
    response = make_response(jsonify({'message': 'logged out'}))
    response.delete_cookie('auth_token', samesite='None', secure=True)
    return response

@app.get("/api/me")
@cookies_needed
def me():
    token = request.cookies['auth_token']
    return jsonify({'user': tokens[token]['user']})

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        return '', 204
    
#tests/config info

@app.get("/test")
def test():
    return 'test'

@app.get('/myip')
def get_ip():
    if tokens:
        import requests
        return requests.get('https://ifconfig.me').text
    else:
        return jsonify({"status": "failed"})

@app.get("/api/last_updated")
@cookies_needed
def last_updated():
    conn = pool.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT last_updated FROM config")
        result = jsonify(cur.fetchall()[0])
        cur.close()
        return result
    finally:
        conn.close()

# update routes

@app.post("/api/update")
@cookies_needed
def update():
    conn = pool.get_connection()
    try:
        Orders(conn).update()
        Products(conn).update()
        Sales(conn).update()
        Suppliers(conn).update()
    finally:
        conn.close()
    return jsonify({"status": "success"})

@app.post("/api/orders/update")
@cookies_needed
def update_orders():
    conn = pool.get_connection()
    try:
        Orders(conn).update()
    finally:
        conn.close()
    return jsonify({"status": "success"})

@app.post("/api/products/update")
@cookies_needed
def update_products():
    conn = pool.get_connection()
    try:
        Products(conn).update()
    finally:
        conn.close()
    return jsonify({"status": "success"})

@app.post("/api/sales/update")
@cookies_needed
def update_sales():
    conn = pool.get_connection()
    try:
        Sales(conn).update()
    finally:
        conn.close()
    return jsonify({"status": "success"})

@app.post("/api/suppliers/update")
@cookies_needed
def update_suppliers():
    conn = pool.get_connection()
    try:
        Suppliers(conn).update()
    finally:
        conn.close()
    return jsonify({"status": "success"})

@app.post("/api/registers/update")
@cookies_needed
def update_registers():
    conn = pool.get_connection()
    try:
        Registers(conn).update()
    finally:
        conn.close()
    return jsonify({"status": "success"})

# get routes

@app.post("/api/select")
@cookies_needed
def select():
    conn = pool.get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        query = request.get_json()
        query_str, params = make_select(query)
        cur.execute(query_str, params)
        result = cur.fetchall()
        return jsonify([dict(row) for row in result])
    finally:
        conn.close()

@app.post("/api/search")
@cookies_needed
def search():
    data = request.get_json()
    
    conn = pool.get_connection()
    cur = conn.cursor(dictionary=True)
    try:
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

        sale_interval_query_str, sale_interval_params = make_select(sale_interval)
        main_query_str, main_params = make_select(main_query)
        params = sale_interval_params + main_params
        cur.execute(f"WITH sale_interval AS ({sale_interval_query_str}) {main_query_str}", params)
        product_result = cur.fetchall()
        return jsonify([dict(row) for row in product_result])
    finally:
        conn.close()

@app.post("/api/sales/get")
@cookies_needed
def get_sales():
    data = request.get_json()

    conn = pool.get_connection()
    cur = conn.cursor(dictionary=True)
    try:
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

        sale_interval_query_str, sale_interval_params = make_select(sale_interval)
        main_query_str, main_params = make_select(main_query)
        params = sale_interval_params + main_params
        cur.execute(f"WITH sale_interval AS ({sale_interval_query_str}) {main_query_str}", params)
        result = cur.fetchall()
        return jsonify([dict(row) for row in result])
    finally:
        conn.close()

application = app

if __name__ == "__main__":
    application.run(debug=False)
import sqlite3
from database.LightSpeed import Orders, Products, Sales, Suppliers, Registers

DEFAULT_LOC = r"C:\Users\liams\Gallery\DB\resources"

class Database:
	def __init__(self, conn):
		self.conn = conn
		self.cur = self.conn.cursor()

	def make_orders_table(self):
		self.cur.execute('''
				CREATE TABLE IF NOT EXISTS orders (
					id TEXT PRIMARY KEY,
					supplier_id TEXT,
					name TEXT,
					reference TEXT,
					type TEXT NOT NULL,
					date INTEGER NOT NULL,
					received_at INTEGER,
					status TEXT NOT NULL,
					version INTEGER NOT NULL,
					FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
				)
			'''
			)
		self.conn.commit()

	def make_products_table(self):
		self.cur.execute('''
			CREATE TABLE IF NOT EXISTS products (
				id TEXT PRIMARY KEY,
				sku TEXT,
				name TEXT,
				variant_name TEXT,
				has_variants INTEGER NOT NULL,
				variant_count INTEGER,
				description TEXT,
				handle TEXT,
				brand TEXT,
				has_inventory INTEGER,
				is_composite INTEGER,
				category_1 TEXT,
				category_2 TEXT,
				category_3 TEXT,
				supplier_id TEXT,
				supplier_code TEXT,
				price REAL,
				updated_at INTEGER NOT NULL,
				created_at INTEGER NOT NULL,
				deleted_at INTEGER,
				source TEXT,
				type TEXT,
				account_code,
				account_code_purchase,
				supply_price REAL,
				in_store INTEGER NOT NULL,
				online INTEGER NOT NULL,
				loyalty_amount,
				weight REAL,
				weight_unit TEXT,
				length REAL,
				width REAL,
				height REAL,
				dimensions_unit TEXT,
				version INTEGER NOT NULL,
				FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
			)
		'''
		)
		self.conn.commit()

	def make_sales_table(self):
		self.cur.execute('''
			CREATE TABLE IF NOT EXISTS sales (
				id TEXT PRIMARY KEY,
				register_id TEXT NOT NULL,
				customer_id TEXT NOT NULL,
				date INTEGER NOT NULL,
				total_price REAL NOT NULL,
				invoice_number INTEGER NOT NULL,
				status TEXT NOT NULL,
				version INTEGER NOT NULL,
				FOREIGN KEY(customer_id) REFERENCES customers(id),
				FOREIGN KEY(register_id) REFERENCES registers(id)
			)
		'''
		)
		self.conn.commit()

	def make_order_products_table(self):
		self.cur.execute('''
			CREATE TABLE IF NOT EXISTS order_products (
				order_id TEXT,
				product_id TEXT,
				count INTEGER,
				status TEXT NOT NULL,
				FOREIGN KEY(order_id) REFERENCES orders(id),
				FOREIGN KEY(product_id) REFERENCES products(id)
			)
		'''
		)
		self.conn.commit()

	def make_sales_products_table(self):
		self.cur.execute('''
			CREATE TABLE IF NOT EXISTS sale_products (
				sale_id TEXT,
				product_id TEXT,
				discount_total REAL,
				price_total REAL,
				cost_total REAL,
				tax_total REAL,
				count INTEGER,
				status TEXT NOT NULL,
				FOREIGN KEY(sale_id) REFERENCES sales(id),
				FOREIGN KEY(product_id) REFERENCES products(id)
			)
		'''
		)
		self.conn.commit()

	def make_items_table(self):
		self.cur.execute('''
			CREATE TABLE IF NOT EXISTS service_items (
				id TEXT NOT NULL UNIQUE,
				name TEXT,
				description TEXT,
				price REAL,
				updated_at INTEGER,
				created_at INTEGER,
				deleted_at INTEGER,
				source TEXT,
				type TEXT,
				active INTEGER,
				version INTEGER NOT NULL
			)
		'''
		)
		self.conn.commit()

	def make_product_variants_table(self):
		self.cur.execute('''
			CREATE TABLE IF NOT EXISTS product_variants (
				product_id TEXT,
				option_name TEXT,
				option_value,
				FOREIGN KEY(product_id) REFERENCES products(id)
			)
		'''
		)
		self.conn.commit()

	def make_suppliers_table(self):
		self.cur.execute('''
			CREATE TABLE IF NOT EXISTS suppliers (
				id TEXT PRIMARY KEY,
				name TEXT NOT NULL,
				code TEXT UNIQUE,
				active INTEGER,
				seller_type TEXT,
				tier INTEGER,
				deal_type TEXT,
				deal
			)
		'''
		)
		self.conn.commit()

	def make_customers_table(self):	
		self.cur.execute('''
			CREATE TABLE IF NOT EXISTS customers (
				id TEXT PRIMARY KEY
			)
		'''
		)
		self.conn.commit()

	def make_inventory_table(self):
		self.cur.execute('''
			CREATE TABLE IF NOT EXISTS inventory (
				product_id TEXT UNIQUE,
				count INTEGER NOT NULL,
				FOREIGN KEY(product_id) REFERENCES products(id)
			)
		'''
		)
		self.conn.commit()

	def make_registers_table(self):
		self.cur.execute('''
				CREATE TABLE IF NOT EXISTS registers (
					id TEXT PRIMARY KEY,
					name TEXT NOT NULL,
					invoice_sequence INTEGER,
					open INTEGER NOT NULL,
					version INTEGER NOT NULL
			)
		'''
		)
		self.conn.commit()
		Registers(self.conn).update()


	def make_tables(self):
		self.make_orders_table()
		self.make_products_table()
		self.make_sales_table()
		self.make_order_products_table()
		self.make_sales_products_table()
		self.make_product_variants_table()
		self.make_suppliers_table()
		self.make_customers_table()
		self.make_inventory_table()
		self.make_registers_table()
		self.make_items_table()
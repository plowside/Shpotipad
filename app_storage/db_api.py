import threading, sqlite3, random, time, os

from .models import *
from .storage import *

mega_client = StorageMega()

def DB_DictFactory(cursor, row):
	_ = {}
	for i, column in enumerate(cursor.description):
		_[column[0]] = row[i]
	return _

def os_delete(*paths):
	for path in paths:
		for x in range(50):
			try: os.remove(path); break
			except Exception as e: time.sleep(.8)


class database_driver:
	def __init__(self):
		self.con = sqlite3.connect('storage/storage_db.db')
		self.con.row_factory = DB_DictFactory
		self.cur = self.con.cursor()

	def _get_connection(self):
		return self.con, self.cur
	
	def change_list(self, *query):
		for q in query:
			self.cur.execute(q)
		self.con.commit()

	def select(self, q, *p):
		return self.cur.execute(q, p).fetchone()
	
	def selecta(self, q, *p):
		return self.cur.execute(q, p).fetchall()

	def insert(self, q, *p):
		self.cur.execute(q, p)
		self.con.commit()

	def close(self):
		self.cur.close()
		self.con.close()

	def create_tables(self):
		table_queries = {
			'sounds': '''
				CREATE TABLE IF NOT EXISTS sounds(
					sound_id INTEGER,
					sound_name TEXT,
					sound_url TEXT,
					sound_url_data TEXT
				)
			'''
		}

		for table_name, q in table_queries.items():
			self.cur.execute(q)

		self.con.commit()






	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def __del__(self):
		self.close()


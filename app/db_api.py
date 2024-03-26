import threading, sqlite3, random, time, os

from .api.models import *
from .api.storage import *
from .api.sound_utils import *

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
		self.con = sqlite3.connect('storage/db.db')
		self.con.row_factory = DB_DictFactory
		self.cur = self.con.cursor()

	def _get_connection(self):
		return self.con, self.cur
	
	def change_list(self, *query):
		for q in query:
			self.cur.execute(q)
		self.con.commit()

	def close(self):
		self.cur.close()
		self.con.close()

	def create_tables(self):
		table_queries = {
			'users': '''
				CREATE TABLE IF NOT EXISTS users(
					user_id INTEGER PRIMARY KEY AUTOINCREMENT,
					username TEXT,
					email TEXT,
					hashed_password TEXT,
					registration_date INTEGER
				)
			''',
			'sounds': '''
				CREATE TABLE IF NOT EXISTS sounds(
					sound_id INTEGER PRIMARY KEY AUTOINCREMENT,
					user_id INTEGER,
					sound_name TEXT,
					sound_url TEXT,
					sound_url_data TEXT,
					sound_duration INTEGER
					sound_downloads INTEGER DEFAULT (0),
					create_date INTEGER
				)
			''',
			'sounds_tags': '''
				CREATE TABLE IF NOT EXISTS sounds_tags(
					sound_id INTEGER,
					tag_name TEXT,
					tag_id INTEGER DEFAULT (0)
				)
			''',
			'sounds_stats': '''
				CREATE TABLE IF NOT EXISTS sounds_stats(
					sound_id INTEGER,
					user_id INTEGER,
					stat_id INTEGER
				)
			''',

		}

		for table_name, q in table_queries.items():
			self.cur.execute(q)

		self.con.commit()


	async def get_sounds(self, q, limit, state):
		sql_query = '''SELECT s.*, GROUP_CONCAT(st.tag_name || '|' || st.tag_id) AS sound_tags FROM sounds AS s LEFT JOIN sounds_tags AS st ON st.sound_id = s.sound_id'''
		params = []

		if q:
			params.append(q)
			sql_query += f' WHERE s.sound_name LIKE \'%\' || ? || \'%\''
		sql_query += f' GROUP BY s.sound_id'
		if limit:
			limit = limit.split(',')
			sql_query += f' LIMIT {limit[0]}' if len(limit) == 1 else f' LIMIT {limit[1]} OFFSET {limit[0]}'


		sounds = self.cur.execute(sql_query, params).fetchall()
		for x in sounds:
			x['sound_stats'] = self.cur.execute('SELECT (SELECT COUNT(*) FROM sounds_stats WHERE sound_id = ? AND stat_id = 1) - (SELECT COUNT(*) FROM sounds_stats WHERE sound_id = ? AND stat_id = 0) AS q', [x['sound_id'], x['sound_id']]).fetchone()['q']
			x['sound_tags'] = x['sound_tags'].split(',')
		return [SoundInDB(**x).dict() for x in sounds]


	def upload_sound(self, sound, sound_file):
		sound_id = self.cur.execute('SELECT seq AS q FROM sqlite_sequence WHERE name = "sounds"').fetchone()
		sound_id = sound_id['q'] + 1 if sound_id else 1
		sound.sound_id = sound_id

		sound_file_name = f'{sound_id}-{sound.sound_name.replace(" ", "-")}.mp3'
		open(f'storage/uploads/sounds/{sound_file_name}', "wb").write(sound_file.file.read())
		sound_info = convert_to_mp3(f'storage/uploads/sounds/{sound_file_name}', f'storage/uploads/sounds/{sound_file_name}')
		if not sound_info['status']:
			threading.Thread(target=os_delete, args=[sound_info['path']]).start()
			return sound_info
		sound.sound_duration = int(sound_info['duration'])
		sound.sound_url = sound_info['path']
		sound.sound_url_data = f'local'
		uploaded_file = mega_client.upload_file(sound_info['path'])
		if uploaded_file['status']:
			sound.sound_url = uploaded_file['path']
			sound.sound_url_data = f'mega|{uploaded_file["account"]}'

		sound.create_date = int(time.time())
		self.cur.execute('INSERT INTO sounds (user_id, sound_name, sound_url, sound_url_data, sound_duration, create_date) VALUES (?, ?, ?, ?, ?, ?)', [sound.user_id, sound.sound_name, sound.sound_url, sound.sound_url_data, sound.sound_duration, sound.create_date])
		if sound_info['is_loud']:
			sound.sound_tags.append(['Loud', 1])
		for tag in sound.sound_tags:
			self.cur.execute('INSERT INTO sounds_tags VALUES (?, ?, ?)', [sound.sound_id, tag[0], tag[1]])
		self.con.commit()

		return {'status': True, 'sound': sound}


	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def __del__(self):
		self.close()


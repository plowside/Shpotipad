from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import logging, random, string, time

from .models import *
from ..db_api import *
from ..utils.email_utils import *
from config import cfg_jwt_secret_key, cfg_jwt_algorithm, cfg_jwt_alive_munites

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")

#####################################################################################
def check_string(s, b='abcdefghijklmnopqrstuvwxyz1234567890_!@#$&/'):
	return all(char in set(b) for char in s.lower())

def random_string(l = 32):
	return ''.join(random.choice(string.ascii_lowercase) for _ in range(l))

def get_password_hash(password):
	return pwd_context.hash(password, salt=cfg_jwt_secret_key[:22])

def verify_password(plain_password, hashed_password):
	return pwd_context.verify(plain_password, hashed_password)

async def create_jwt_token(data: dict, expire_delta: timedelta):
	to_encode = data.copy()
	expire = int(time.time() + expire_delta.total_seconds())
	to_encode.update({"expire": expire})
	return {'token': jwt.encode(to_encode, cfg_jwt_secret_key, algorithm=cfg_jwt_algorithm), 'expire': expire}



#####################################################################################
async def get_user(payload: UserLogin):
	_db = database_driver()
	con, cur = _db._get_connection()

	if payload.username:
		cur.execute('SELECT * FROM users WHERE username = ?', [payload.username])
	else:
		cur.execute('SELECT * FROM users WHERE email = ?', [payload.email])
	user = cur.fetchone()

	if not user: return user
	user = UserInDB(**user)
	if not verify_password(payload.password, user.hashed_password): return None
	return user

# Создание пользователя
async def create_user(payload: UserRegister):
	_db = database_driver()
	temp_db = temp_database_driver()
	con, cur = _db._get_connection()
	payload.username = payload.username.strip(); payload.password = payload.password.strip(); payload.email = payload.email.strip()
	if len(payload.token) != 16 or not temp_db.select('SELECT * FROM tokens WHERE token = ?', payload.token):
		return {'status': False, 'message': 'Verify Token expired'}

	if not (3 <= len(payload.username) <= 32):
		if len(payload.username) > 32:
			return {'status': False, 'message': 'Max. username\'s length is 32 characters'}
		else:
			return {'status': False, 'message': 'Min. username\'s length is 3 characters'}
	elif not (4 <= len(payload.password) <= 128) or not (check_string(payload.password)):
		if not check_string(payload.password):
			return {'status': False, 'message': 'Password contains banned characters'}
		elif len(payload.password) > 128:
			return {'status': False, 'message': 'Max. password\'s length is 128 characters'}
		else:
			return {'status': False, 'message': 'Min. password\'s length is 4 characters'}

	user = cur.execute('SELECT * FROM users WHERE username = ? OR email = ?', [payload.username, payload.email]).fetchone()
	if user:
		if user['username'] == payload.username:
			return {'status': False, 'message': f'Username "{payload.username}" already taken'}
		elif user['email'] == payload.email:
			return {'status': False, 'message': f'User with {payload.email} already exists'}

	cur.execute('INSERT INTO users (username, email, hashed_password, registration_date) VALUES (?, ?, ?, ?)', [payload.username, payload.email, get_password_hash(payload.password), int(time.time())])
	con.commit()
	temp_db.insert('DELETE FROM tokens WHERE token = ?', payload.token)
	return {'status': True, 'user': UserInDB(**cur.execute('SELECT * FROM users WHERE email = ?', [payload.email]).fetchone())}

# Восстановление пользователя
async def reset_user(payload: UserRegister):
	_db = database_driver()
	temp_db = temp_database_driver()
	con, cur = _db._get_connection()
	payload.email = payload.email.strip(); payload.password = payload.password.strip()
	if len(payload.token) != 16 or not temp_db.select('SELECT * FROM tokens WHERE token = ?', payload.token):
		return {'status': False, 'message': 'Verify Token expired'}

	elif not (4 <= len(payload.password) <= 128) or not (check_string(payload.password)):
		if not check_string(payload.password):
			return {'status': False, 'message': 'Password contains banned characters'}
		elif len(payload.password) > 128:
			return {'status': False, 'message': 'Max. password\'s length is 128 characters'}
		else:
			return {'status': False, 'message': 'Min. password\'s length is 4 characters'}

	cur.execute('UPDATE users SET hashed_password = ? WHERE email = ? OR username = ?', [get_password_hash(payload.password), payload.email, payload.email])
	con.commit()
	temp_db.insert('DELETE FROM tokens WHERE token = ?', payload.token)
	return {'status': True, 'user': UserInDB(**cur.execute('SELECT * FROM users WHERE email = ? OR username = ?', [payload.email, payload.email]).fetchone())}

# Отправка\верификация проверочного кода
async def send_code(payload: UserSendCode):
	_db = temp_database_driver()
	if payload.reset:
		if payload.code:
			token = _db.select('SELECT token FROM tokens WHERE some_data = ?', f'{payload.email}|{payload.code}|reset')
			if not token:
				return {'status': False, 'message': 'Invalid Verify code'}
			return {'status': True, 'code': 200, 'token': token['token']}
		else:
			_code = random.randint(10000, 99999)
			user = database_driver().select('SELECT * FROM users WHERE email = ? OR username = ?', payload.email, payload.email)
			if not user:
				return {'status': False, 'message': f'User with {payload.email} doesn\'t exist'}
			code = await send_email(f'{_code} - Verify code', user['email'], html=templates.get_template('email.html').render({'current_date': 'March 28, 2024' , 'verify_code': _code}))
			if code['status']:
				_db.insert('INSERT INTO tokens (token, some_data, ts) VALUES (?, ?, ?)', random_string(16), f'{payload.email}|{_code}|reset', time.time()) 
				return {'status': True, 'code': 200, 'message': 'Verify code sent'}
			else:
				return {'status': False, 'message': code['message']}

	else:
		if payload.code:
			token = _db.select('SELECT token FROM tokens WHERE some_data = ?', f'{payload.email}|{payload.code}|reg')
			if not token:
				return {'status': False, 'message': 'Invalid Verify code'}
			return {'status': True, 'code': 200, 'token': token['token']}
		else:
			_code = random.randint(10000, 99999)
			if database_driver().select('SELECT * FROM users WHERE email = ?', payload.email):
				return {'status': False, 'message': f'User with {payload.email} already exists'}
			code = await send_email(f'{_code} - Verify code', payload.email, html=templates.get_template('email.html').render({'current_date': 'March 28, 2024' , 'verify_code': _code}))
			if code['status']:
				_db.insert('INSERT INTO tokens (token, some_data, ts) VALUES (?, ?, ?)', random_string(16), f'{payload.email}|{_code}|reg', time.time()) 
				return {'status': True, 'code': 200, 'message': 'Verify code sent'}
			else:
				return {'status': False, 'message': code['message']}

 

async def auth_user(user: UserInDB):
	_db = database_driver()
	con, cur = _db._get_connection()

	access_token = await create_jwt_token(data={'user_id': user.user_id, 'k': get_password_hash(f'{user.user_id}|{user.hashed_password}')}, expire_delta=timedelta(minutes=cfg_jwt_alive_munites))
	return access_token


def jwt_token_check(token: str):
	try:
		try: payload = jwt.decode(token, cfg_jwt_secret_key, algorithms=[cfg_jwt_algorithm])
		except: return None
		user_jwt = JWTTokenPayload(**payload)
		_db = database_driver()
		con, cur = _db._get_connection()

		if user_jwt.expire < int(time.time()):
			return None
		user = cur.execute('SELECT * FROM users WHERE user_id = ?', [user_jwt.user_id]).fetchone()
		if not user or user_jwt.k != get_password_hash(f'{user["user_id"]}|{user["hashed_password"]}'):
			return None
		return {'user_jwt': user_jwt, 'user': UserSafe(**user)}
	except Exception as e:
		logging.error(f'[jwt_token_check] Error: {e}')
		return None
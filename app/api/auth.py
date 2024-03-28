from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import logging, random, time

from .models import *
from .. import db_api
from config import cfg_jwt_secret_key, cfg_jwt_algorithm, cfg_jwt_alive_munites
from ..utils.email_utils import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")

#####################################################################################
def check_string(s, b='abcdefghijklmnopqrstuvwxyz1234567890_!@#$&/'):
	return all(char in set(b) for char in s.lower())

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
	_db = db_api.database_driver()
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

async def create_user(payload: UserRegister):
	_db = db_api.database_driver()
	con, cur = _db._get_connection()
	payload.username = payload.username.strip(); payload.password = payload.password.strip(); payload.email = payload.email.strip()

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
		return {'status': False, 'message': f'User with {payload.email} already exists' if user['email'] == payload.email else f'Username "{payload.username}" already taken'}


	cur.execute('INSERT INTO users (username, email, hashed_password, registration_date) VALUES (?, ?, ?, ?)', [payload.username, payload.email, get_password_hash(payload.password), int(time.time())])
	con.commit()

	return {'status': False, 'user': UserInDB(**cur.execute('SELECT * FROM users WHERE email = ?', [payload.email]).fetchone())}

async def send_code(payload: UserSendCode):
	code = random.randint(10000, 99999)
	code = await send_email(f'{code} - Verify code', payload.email, html=templates.get_template('email.html').render({'current_date': 'March 28, 2024' , 'verify_code': code}))
	return code


async def auth_user(user: UserInDB):
	_db = db_api.database_driver()
	con, cur = _db._get_connection()

	access_token = await create_jwt_token(data={'user_id': user.user_id, 'k': get_password_hash(f'{user.user_id}|{user.hashed_password}')}, expire_delta=timedelta(minutes=cfg_jwt_alive_munites))
	return access_token


def jwt_token_check(token: str):
	try:
		try: payload = jwt.decode(token, cfg_jwt_secret_key, algorithms=[cfg_jwt_algorithm])
		except: return None
		user_jwt = JWTTokenPayload(**payload)
		_db = db_api.database_driver()
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
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import logging, time

from .models import *
from .. import db_api
from config import cfg_jwt_secret_key, cfg_jwt_algorithm, cfg_jwt_alive_munites




pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
	return pwd_context.hash(password, salt=cfg_jwt_secret_key[:22])

def verify_password(plain_password, hashed_password):
	return pwd_context.verify(plain_password, hashed_password)

async def create_jwt_token(data: dict, expire_delta: timedelta):
	to_encode = data.copy()
	expire = int(time.time() + expire_delta.total_seconds())
	to_encode.update({"expire": expire})
	return {'token': jwt.encode(to_encode, cfg_jwt_secret_key, algorithm=cfg_jwt_algorithm), 'expire': expire}



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

	user = cur.execute('SELECT * FROM users WHERE username = ? OR email = ?', [payload.username, payload.email]).fetchone()
	if user:
		return {'message': f'User with {payload.email} already exists' if user['email'] == payload.email else f'Username "{payload.username}" already taken'}


	cur.execute('INSERT INTO users (username, email, hashed_password, registration_date) VALUES (?, ?, ?, ?)', [payload.username, payload.email, get_password_hash(payload.password), int(time.time())])
	con.commit()

	return {'user': UserInDB(**cur.execute('SELECT * FROM users WHERE email = ?', [payload.email]).fetchone())}

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
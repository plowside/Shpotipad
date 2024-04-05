from fastapi import APIRouter, UploadFile, Response, Request, Header, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from typing import Optional

import logging, hashlib, json

from ..db_api import *
from .models import *
from .auth import *
from config import *



router = APIRouter(prefix='/api', tags=['api'])


@router.post('/login')
async def router_login(request: Request, response: Response, payload: UserLogin):
	user = await get_user(payload)
	if not user:
		return {'status': False, 'code': 404, 'message': 'User not found'}

	jwt_token = await auth_user(user)
	return {'status': True, 'code': 200, **jwt_token}

@router.post('/register')
async def router_register(request: Request, response: Response, payload: UserRegister):
	user = await create_user(payload)
	if not user['status']:
		return {'status': False, 'code': 409, 'message': user.get('message')}
	user = user['user']

	jwt_token = await auth_user(user)
	return {'status': True, 'code': 200, **jwt_token}

@router.post('/reset')
async def router_register(request: Request, response: Response, payload: UserReset):
	user = await reset_user(payload)
	if not user['status']:
		return {'status': False, 'code': 409, 'message': user.get('message')}
	user = user['user']

	jwt_token = await auth_user(user)
	return {'status': True, 'code': 200, **jwt_token}

@router.post('/send_code')
async def router_send_code(request: Request, response: Response, payload: UserSendCode):
	code = await send_code(payload)
	if not code['status']:
		return {'status': False, 'code': 409, 'message': code.get('message')}

	return code



@router.get('/me')
async def router_me(request: Request, response: Response, Authorization: str = Header(None)):
	user = jwt_token_check(Authorization)
	if not user:
		return {'status': False, 'code': 401, 'message': 'Unauthorized'}
	user = user['user']

	return {'status': True, 'code': 200, 'user': dict(user)}

@router.put('/me')
async def router_me(request: Request, response: Response, payload: UserUpdate, Authorization: str = Header(None)):
	user = jwt_token_check(Authorization)
	if not user:
		return {'status': False, 'code': 401, 'message': 'Unauthorized'}
	user = user['user']

	payload.password = None if payload.password in ('', ' ') else payload.password
	if not (3 <= len(payload.username) <= 32):
		if len(payload.username) > 32:
			return {'status': False, 'code': 409, 'message': 'Max. username\'s length is 32 characters'}
		else:
			return {'status': False, 'code': 409, 'message': 'Min. username\'s length is 3 characters'}
	elif payload.password and (not (4 <= len(payload.password) <= 128) or not (check_string(payload.password))):
		if not check_string(payload.password):
			return {'status': False, 'code': 409, 'message': 'Password contains banned characters'}
		elif len(payload.password) > 128:
			return {'status': False, 'code': 409, 'message': 'Max. password\'s length is 128 characters'}
		else:
			return {'status': False, 'code': 409, 'message': 'Min. password\'s length is 4 characters'}

	payload.hashed_password = get_password_hash(payload.password) if payload.password else None
	payload.password = None

	_db = database_driver()
	user = _db.update_user(user, payload)
	response = {'status': True, 'code': 200, 'user': UserSafe(**user).dict()}
	if payload.hashed_password:
		token = await auth_user(UserInDB(**user))
		response['token'] = token['token']
	return response



@router.post('/sound')
def router_upload_sound(request: Request, response: Response, sound_file: UploadFile, sound_data: str = Form(...), Authorization: str = Header(None)):
	user = jwt_token_check(Authorization)
	if not user:
		return {'status': False, 'code': 401, 'message': 'Unauthorized'}
	user = user['user']

	try:
		sound = SoundInDB(**json.loads(sound_data))
		sound.sound_tags = [[x, 0] for x in sound.sound_tags]
		sound.user_id = user.user_id
	except Exception as e:
		return {'status': False, 'code': 422, 'message': 'Missing data'}

	_db = database_driver()
	sound = _db.upload_sound(sound, sound_file)
	if not sound['status']: return sound

	return {'status': True, 'sound': sound}


@router.put('/sound')
def router_update_sound(request: Request, response: Response, sound: SoundUpdate, Authorization: str = Header(None)):
	user = jwt_token_check(Authorization)
	if not user:
		return {'status': False, 'code': 401, 'message': 'Unauthorized'}
	user = user['user']

	_db = database_driver()
	try:
		sound = _db.update_sound(sound, user.user_id)
	except Exception as e:
		return {'status': False, 'code': 422, 'message': 'Missing data'}

	return {'status': True, 'sound': sound}


@router.get('/search')
async def router_get_sounds(request: Request, response: Response, q: str = None, limit: str = None, state: str = None, Authorization: str = Header(None)):
	user = jwt_token_check(Authorization)
	if not user: user_id = None
	else: user_id = user['user'].user_id
	if q == '': q = None
	_db = database_driver()
	sounds = await _db.get_sounds(user_id, q, limit, state)

	return {'status': True, 'sounds': sounds}
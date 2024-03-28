from fastapi import FastAPI, Request, Response, Header, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from urllib.parse import urlparse

import logging, json, os 

from .api.models import *
from .api.routers import router as api_router
from .api.auth import jwt_token_check
from .db_api import database_driver, mega_client
from config import *

#################################################################################################################################
logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s', level=logging.INFO,)

app = FastAPI(redoc_url=None, tags=[])#docs_url=None, 
app.include_router(api_router)

templates = Jinja2Templates(directory="templates")
for x in ['storage/uploads/sounds']: os.makedirs(x, exist_ok=True)
#################################################################################################################################
@app.on_event("startup")
async def on_startup():
	database_driver().create_tables()



@app.get('/')
async def route_index(request: Request, Authorization: str = Header(None)):
	return templates.TemplateResponse('index.html', {'request': request})

@app.get('/test')
async def route_test(request: Request, Authorization: str = Header(None)):
	return templates.TemplateResponse('test.html', {'request': request})



@app.get('/search')
async def router_search(request: Request, response: Response, q: str = None, tag: str = None, Authorization: str = Header(None)):
	if q == '': q = None
	if tag == '': tag = None
	_db = database_driver()
	sounds = await _db.get_sounds(q=q, tag=tag)

	return {'status': True, 'sounds': sounds}
	return templates.TemplateResponse('index.html', {'request': request})










#############################################################
@app.get('/sound/{sound_id}')
def route_get_sound(sound_id: int):
	_db = database_driver()
	con, cur = _db._get_connection()

	sound = cur.execute('SELECT * FROM sounds WHERE sound_id = ?', [sound_id]).fetchone()
	if not sound:
		raise HTTPException(status_code=404, detail="Sound not found")
	sound = SoundInDB(**sound)

	try:
		sound_storage = sound.sound_url_data.split('|')
		filename = f'{sound.sound_id}-{sound.sound_name.replace(" ", "-")}.mp3'
		if sound_storage[0] == 'local':
			path = sound.sound_url
		elif sound_storage[0] == 'mega':
			path = mega_client.get_file(filename, sound.sound_url)
			if not path['status']: raise HTTPException(status_code=404, detail="Sound not found")
			path = path['path']
		if os.path.exists(path):
			return FileResponse(path=path)
	except Exception as e:
		logging.error(e)
		raise HTTPException(status_code=404, detail="Sound not found")


@app.get('/sounds/{sound_id}')
def route_dwn_sound(sound_id: int):
	_db = database_driver()
	con, cur = _db._get_connection()

	sound = cur.execute('SELECT * FROM sounds WHERE sound_id = ?', [sound_id]).fetchone()
	if not sound:
		raise HTTPException(status_code=404, detail="Sound not found")
	sound = SoundInDB(**sound)

	try:
		sound_storage = sound.sound_url_data.split('|')
		filename = f'{sound.sound_id}-{sound.sound_name.replace(" ", "-")}.mp3'
		if sound_storage[0] == 'local':
			path = sound.sound_url
		elif sound_storage[0] == 'mega':
			path = mega_client.get_file(filename, sound.sound_url)
			if not path['status']: raise HTTPException(status_code=404, detail="Sound not found")
			path = path['path']
		if os.path.exists(path):
			cur.execute('UPDATE sounds SET sound_downloads = sound_downloads + 1 WHERE sound_id = ?', [sound_id])
			con.commit()
			return FileResponse(path=path)
	except Exception as e:
		logging.error(e)
		raise HTTPException(status_code=404, detail="Sound not found")


@app.get('/static/{path:path}')
async def route_get_image(path: str):
	path_ = urlparse(path)
	path_ = path_.path[:-1] if path_.path[-1] == '/' else path_.path
	path = f'static/{path_}' if f'static/{path_}' == '/' else f'static/{path_}'
	try:
		if os.path.exists(path): return FileResponse(path=path)
	except: raise HTTPException(status_code=404, detail="File not found")

################################################################
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
	return templates.TemplateResponse('404.html', {'request': request}, status_code=404)

@app.exception_handler(500)
async def internal_error_exception_handler(request: Request, exc: HTTPException):
	return templates.TemplateResponse('500.html', {'request': request}, status_code=500)

if __name__ == '__main__':
	uvicorn.run()
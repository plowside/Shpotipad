from fastapi import FastAPI, Request, Response, Header, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from urllib.parse import urlparse

import logging, json, os 

from .models import *
from .db_api import *
from config import *

#################################################################################################################################
logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s', level=logging.INFO,)

app = FastAPI(docs_url=None, redoc_url=None, tags=[]) 
app.include_router(api_router)

templates = Jinja2Templates(directory="templates")
for x in ['storage/uploads/sounds']: os.makedirs(x, exist_ok=True)
#################################################################################################################################
@app.on_event("startup")
async def on_startup():
	database_driver().create_tables()



@app.post('/sound')
def router_upload_sound(request: Request, response: Response, payload: SoundUpload):
	try:
		payload = SoundUpload(**json.loads(payload))
		if payload.token != cfg_jwt_secret_key:
			return {'status': False, 'message': 'Unauthorized'}
	except: return {'status': False, 'message': 'Missing data'}
	_db = database_driver()
	con, cur = _db._get_connection()


	try:
		cur.execute('INSERT INTO sounds VALUES (?, ?, ?, ?)', [payload.sound_id, payload.sound_name, payload.sound_url, payload.sound_url_data])
		con.commit()
	except Exception as e: return {'status': False, 'message': str(e)}

	return {'status': True, 'sound_id'}


if __name__ == '__main__':
	uvicorn.run()
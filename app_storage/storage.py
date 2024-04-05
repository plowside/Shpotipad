import asyncio, logging, requests, httpx, mega, os

from config import *


ses = requests.Session()
ses.proxies = None#{"http": "http://proxy.server:3128", "https": "http://proxy.server:3128"}
mega.mega.requests = ses
#logging.getLogger('mega').setLevel(logging.ERROR)




class StorageMega:
	def __init__(self):
		self.accounts = {x: True for x in cfg_mega_accounts}
		self.m = mega.Mega().login()

		self.on_startup()

	def on_startup(self):
		logging.info('[StorageMega] Checking remaining space...')
		for acc in list(self.accounts):
			try:
				email, password = acc.split(':')
				_mega = mega.Mega()
				m = _mega.login(email, password)
				remaining_space = m.get_storage_space(mega=True)
				if remaining_space['total'] - remaining_space['used'] < 10:
					logging.info(f'[StorageMega] No remaining space {acc}: {remaining_space["total"] - remaining_space["used"]}')
					self.accounts[acc] = False
			except Exception as e:
				logging.info(f'[StorageMega] Error while checking {acc}: {e}')
				del self.accounts[acc]
		logging.info(f'[StorageMega] Available accounts: {len([x for x in self.accounts if self.accounts[x]])}')

	def upload_file(self, file_path):
		available_accounts = [x for x in self.accounts if self.accounts[x]]
		if len(available_accounts) == 0:
			return {'status': False, 'message': 'There is not enough space on the server. Try again later.'}

		for acc in available_accounts:
			try:
				email, password = acc.split(':')
				_mega = mega.Mega()
				m = _mega.login(email, password)
				file = m.upload(file_path)
				return {'status': True, 'path': m.get_upload_link(file), 'account': acc}
			except Exception as e:
				del self.accounts[acc]
				logging.info(f'[StorageMega] Error while uploading {acc}: {e}')

		try:
			file = self.m.upload(file_path)
			return {'status': True, 'path': m.get_upload_link(file), 'account': 'anonymous:anonymous'}
		except: return {'status': False, 'message': 'There is not enough space on the server. Try again later.'}


	def get_file(self, filename = None, url = None, storage_path = 'storage/uploads/sounds'):
		return {'status': True, 'path': f'{storage_path}/{filename}'}
		if os.path.exists(f'{storage_path}/{filename}'): return {'status': True, 'path': f'{storage_path}/{filename}'}
		try: file = self.m.download_url(url, dest_filename=f'storage/uploads/sounds/{filename}')
		except: 
			try: os.remove(f'storage/uploads/sounds/{filename}')
			except: pass
			pass
		if os.path.exists(f'{storage_path}/{filename}'): return {'status': True, 'path': f'{storage_path}/{filename}'}
		else: return {'status': False, 'message': 'The file could not be found on the server.'}

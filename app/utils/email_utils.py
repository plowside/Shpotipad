from config import *

import httpx



async def send_email(title: str, recipient_email: str, html: str = None, content: str = None):
	try:
		async with httpx.AsyncClient() as client: #proxies={"http://": "http://proxy.server:3128", "https://": "http://proxy.server:3128"}
			mail = (await client.post('https://api.resend.com/emails', headers={'Authorization': f'Bearer {cfg_email["password"]}'}, json={'from':cfg_email['from'], 'to': [recipient_email], 'subject': title, 'html': html})).json()
		if 'id' in mail: return {'status': True}
		else: return {'status': False, 'message': 'Failed to send code', 'error': str(mail)}
	except Exception as e:
		return {'status': False, 'message': 'Failed to send code', 'error': str(e)}

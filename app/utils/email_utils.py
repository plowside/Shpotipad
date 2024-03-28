from email.message import EmailMessage
from aiosmtplib import SMTP
from config import *


async def send_email(title: str, recipient_email: str, html: str = None, content: str = None):
	try:
		smtp = SMTP(
			hostname=cfg_email['host'],
			port=cfg_email['port'],
			start_tls=False,
			use_tls=False,
		)
		await smtp.connect()
		await smtp.starttls()
		await smtp.login(cfg_email['user'], cfg_email['password'])

		message = EmailMessage()
		message['From'] = cfg_email['from']
		message['To'] = recipient_email
		message['Subject'] = title

		if content is not None and html is not None:
			message.set_content(content)
			message.add_alternative(html, subtype='html')
		elif content is not None:
			message.set_content(content)
		elif html is not None:
			message.add_alternative(html, subtype='html')
		await smtp.send_message(message)
		await smtp.quit()
		return {'status': True}
	except Exception as e:
		return {'status': False, 'message': 'Failed to send code', 'error': str(e)}

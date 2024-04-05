from pydantic import BaseModel


class SoundUpload(BaseModel):
	token: str
	sound_id: int
	sound_name: str
	sound_url: str
	sound_url_data: str
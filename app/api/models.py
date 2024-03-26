from pydantic import BaseModel


class UserInDB(BaseModel):
	user_id: int
	username: str
	email: str
	hashed_password: str
	registration_date: int

class UserSafe(BaseModel):
	user_id: int
	username: str
	email: str
	registration_date: int


class UserLogin(BaseModel):
	username: str = None
	email: str = None
	password: str

class UserRegister(BaseModel):
	username: str
	email: str
	password: str

class JWTTokenPayload(BaseModel):
	user_id: int
	k: str
	expire: int


class SoundInDB(BaseModel):
	sound_id: int | None = None
	user_id: int | None = None
	sound_name: str | None = None
	sound_url: str | None = None
	sound_url_data: str | None = None
	sound_downloads: int | None = 0
	sound_duration: float | None = None
	create_date: int | None = None

	sound_tags: list | None = []
	sound_stats: int | None = 0


class GetSounds(BaseModel):
	state: str = 'new'
	limit: list = [0, 20]
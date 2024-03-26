import requests, json

# Замените URL на актуальный
url = 'http://192.168.0.13:8000/api/sound'
# Путь к файлу звука
sound_file_path = r"C:\Users\plows\AppData\Roaming\Leppsoft\104228-реклама-pron-саита.mp3"
# Данные звука
sound_data = {
    'sound_data': json.dumps({
        'sound_name': 'Патрик',
        'sound_tags': ['tag1', 'tag2']
    })
}
# Заголовок Authorization (если необходим)
headers = {
    'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJrIjoiJDJiJDEyJDMxN2FlZjJiMTQxYzkyMTY4Yjk5M3VSWm1UUzBaU3Q4ZDA0NUZXMDNmUXZ0OU83ZjhKakZxIiwiZXhwaXJlIjoxNzExNDQ0Mjg5fQ.tPry--lnQE8UF-3ROBYmQfpXg95e5dIHGyxw61BH3Rk'
}

# Создание запроса
with open(sound_file_path, 'rb') as file:
    files = {'sound_file': file}
    req = requests.post(url, files=files, data=sound_data, headers=headers)

print(req.json())
import requests, json

# Замените URL на актуальный
url = 'https://shpotipad.pythonanywhere.com/api/sound'
# Путь к файлу звука
sound_file_path = r"C:\Users\plows\Downloads\поздравляю с днём дрочения💖💕💓💕💓 #рек #рофл #мем #активвернись #tiktok (480p).mp4"
# Данные звука
sound_data = {
    'sound_data': json.dumps({
        'sound_name': 'С днем дрочения',
        'sound_tags': ['поздравление']
    })
}
# Заголовок Authorization (если необходим)
headers = {
    'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJrIjoiJDJiJDEyJDMxN2FlZjJiMTQxYzkyMTY4Yjk5M3VSWm1UUzBaU3Q4ZDA0NUZXMDNmUXZ0OU83ZjhKakZxIiwiZXhwaXJlIjoxNzExNjM0NzcyfQ.kWIwkxOMiTkZTQffctOKlD9a1rLE5Z0nx6gQ2Fb4w7o'
}

# Создание запроса
with open(sound_file_path, 'rb') as file:
    files = {'sound_file': file}
    req = requests.post(url, files=files, data=sound_data, headers=headers)

print(req.json())
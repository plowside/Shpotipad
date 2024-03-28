import requests, json

# Замените URL на актуальный
url = 'https://shpotipad.pythonanywhere.com/api/sound'
# Путь к файлу звука
sound_file_path = r"C:\Users\plows\OneDrive\Рабочий стол\чсмчсмчсм\bear1_weap_reload3_n.wav-CAB_12ae3460088df36a0c1fac14b76afbbc-1308837438952614786.wav"
# Данные звука
sound_data = {
    'sound_data': json.dumps({
        'sound_name': 'Красный',
        'sound_tags': ['тарков', 'Tarkov', 'Красный', 'Миша', 'Игра года']
    })
}
# Заголовок Authorization (если необходим)
headers = {
    'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJrIjoiJDJiJDEyJDMxN2FlZjJiMTQxYzkyMTY4Yjk5M3VSWm1UUzBaU3Q4ZDA0NUZXMDNmUXZ0OU83ZjhKakZxIiwiZXhwaXJlIjoxNzExNjE0MDIzfQ.sDz7VjiEXrPEL_8o5-lQVqAiuAwv5hADytLjSmS2XRE'
}

# Создание запроса
with open(sound_file_path, 'rb') as file:
    files = {'sound_file': file}
    req = requests.post(url, files=files, data=sound_data, headers=headers)

print(req.json())
import requests

data = {'name': '尤勇', 'email': 'test@gmail.com', 'message':"test"}

# 發送 POST 請求
web = requests.post('http://127.0.0.1:5555/send-message', json=data)   
print(web.text)
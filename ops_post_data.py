import requests

data = {'name': '尤勇', 'age': '12'}

# 發送 POST 請求
web = requests.post('http://127.0.0.1:5555/', data=data)   
print(web.text)
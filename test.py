import urllib.request
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', data=b'{"username":"advaith","password":"test"}', headers={'Content-Type':'application/json'})
try:
    print(urllib.request.urlopen(req).read().decode())
except Exception as e:
    try:
        print(e.read().decode())
    except:
        print(e)

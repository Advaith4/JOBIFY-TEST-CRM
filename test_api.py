import requests
import json

f = open("dummy.pdf", "rb")
r = requests.post("http://127.0.0.1:8000/api/analyze", 
    files={"file": ("dummy.pdf", f, "application/pdf")}, 
    data={"location": "India", "job_type": "Full-time", "work_mode": "Any", "experience": "Entry-level"}
)

print(r.status_code)
try:
    with open("out.json", "w") as out:
        out.write(r.text)
except Exception as e:
    print(e)

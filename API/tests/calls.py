import requests

headers = {
        "accept": "application/json",
        "content-type": "application/json",
    }

json = {"username": 'Admin', 'password': 'Gallery'}

if __name__ == "__main__":
    requests.post(r"http://localhost:5000/api/login", json=json, headers=headers)

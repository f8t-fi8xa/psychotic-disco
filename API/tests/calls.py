import requests

headers = {
        "accept": "application/json",
        "content-type": "application/json",
    }

json = {}

if __name__ == "__main__":
    requests.post(r"http://localhost:5000/api/update", json=json, headers=headers)

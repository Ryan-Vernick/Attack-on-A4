import requests
from requests import Response
''' redundant with server imports:
from pydantic import BaseModel
import rsa
import base64
import json
'''

import base64
import csv
import rsa
import uvicorn
import json
from hashlib import sha256
from pydantic import BaseModel
from pathlib import Path
from fastapi import FastAPI, status, Request
from fastapi.responses import Response
from starlette.responses import JSONResponse

# this is us
app = FastAPI()
# !!! this should be changed to 8000 at the end
PORT = 8001


# in order to talk to the server we need it's address
SERVER_ADDR = "127.0.0.1"
# !!! this should be changed to 8001 at the end
SERVER_PORT = "8000"
SERVER_URL = f"http://{SERVER_ADDR}:{SERVER_PORT}"



# we'll see if we need these

##PINS_FILE = "PIN.csv"
##VOTES_FILE = "votes.csv"


@app.get("/candidates")
def get_candidates():
    candidates = requests.get(url=f"{SERVER_URL}/candidates")
    print ("router: candidates")
    return candidates

@app.get("/validate_votes")
def validate_votes_endpoint():
    print ("router: validate_votes")

@app.post("/deauthorize")
async def deauthorize_pin_endpoint(request: Request):
    print ("router: deauthorize")

@app.post("/authorize")
async def authorize_pin_endpoint(request: Request):
    print ("router: authorize")

@app.post("/vote")
async def vote_endpoint(request: Request):
    print ("router: vote")

'''
implement the attack once the pass-through works properly

### pulled directly from client.py
def check_votes():
    response = requests.get(url=f"{SERVER_URL}/validate_votes")
    
    response_text = get_res(response)
    
    if not response_text:
        print("No candidates with votes returned from server!")
        return
    
    print(response_text)
    
    data = json.loads(response_text)
    
    for entry in data.keys():
        entry_name = "# of valid pins voted" if entry == "num_pins" else entry
        
        print(f"{entry_name}: {data[entry]}")

### pulled directly from client.py
def get_res(res: Response):
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        return None

'''
        

if __name__ == "__main__":
    print(f"[i] Started server on port {PORT}")

    if not Path("public.pem").exists() or not Path("private.pem").exists():
        (public_key, private_key) = rsa.newkeys(2048, exponent=65537)

        with open("public.pem", "wb") as f:
            f.write(public_key.save_pkcs1())

        with open("private.pem", "wb") as f:
            f.write(private_key.save_pkcs1())

        print("[i] Generated new public/private keypair")

    with open("private.pem", "rb") as f:
        private_key = rsa.PrivateKey.load_pkcs1(f.read())
        print("[i] Opened private key")

    uvicorn.run(app, host="0.0.0.0", port=PORT)
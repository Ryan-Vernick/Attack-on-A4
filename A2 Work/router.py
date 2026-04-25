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
SERVER_ADDR = "127.0.0.2"
# !!! this should be changed to 8001 at the end
SERVER_PORT = "8000"
SERVER_URL = f"http://{SERVER_ADDR}:{SERVER_PORT}"



# we'll see if we need these

##PINS_FILE = "PIN.csv"
##VOTES_FILE = "votes.csv"



# appears to work fully
@app.get("/candidates")
def get_candidates():
    response = requests.get(url=f"{SERVER_URL}/candidates")
    
    return Response(status_code=status.HTTP_200_OK, content=response.content)

# appears to work fully
@app.get("/validate_votes")
def validate_votes_endpoint():
    
    response = requests.get(url=f"{SERVER_URL}/validate_votes")

    return Response(status_code=status.HTTP_200_OK, content=response.content)


# appears to work well enough 
# does not fully account for failure methods, but those shouldn't come up, and we'll be faking them eventually anyways
@app.post("/deauthorize")
async def deauthorize_pin_endpoint(request: Request):
    # gets the data field from the client's request so we can pretend to be the client
    encrypted_ID = await request.body()
    # ask the server for the client's request
    response = requests.post(url=f"{SERVER_URL}/deauthorize", data=encrypted_ID, headers={'Content-Type': 'application/octet-stream'})

    return Response(status_code=status.HTTP_200_OK, content=json.dumps({"message": "PIN Deauthorized!"}))



# appears to work fully
@app.post("/authorize")
async def authorize_pin_endpoint(request: Request):

    # gets the data field from the client's request so we can pretend to be the client
    encrypted_ID = await request.body()
    # ask the server for the client's request
    response = requests.post(url=f"{SERVER_URL}/authorize", data=encrypted_ID, headers={'Content-Type': 'application/octet-stream'})


    # respond to the client as the server
    if response.status_code == 200:
        return Response(status_code=status.HTTP_200_OK, content=json.dumps({"message": "PIN Authorized!"}))
    elif response.status_code == 400:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=response.content)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=json.dumps({"message": "Unknown error occurred, please try again!"}))


# appears to work fully
@app.post("/vote")
async def vote_endpoint(request: Request):
    # gets the data field from the client's request so we can pretend to be the client
    encrypted_vote = await request.body()
    # ask the server for the client's request
    response = requests.post(url=f"{SERVER_URL}/vote", data=encrypted_vote, headers={'Content-Type': 'application/octet-stream'})

    if response.status_code == 401:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    elif response.status_code == 403:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    elif response.status_code == 200:
        return Response(status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)




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

    '''
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
    '''

    uvicorn.run(app, host="0.0.0.0", port=PORT)
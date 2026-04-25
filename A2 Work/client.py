import requests
from requests import Response
#from hashlib import sha256
#from argon2 import PasswordHasher
from pydantic import BaseModel
import rsa
import base64
import json

from fastapi import status

SERVER_ADDR = "127.0.0.1"
## actually the router port
SERVER_PORT = "8001"

SERVER_URL = f"http://{SERVER_ADDR}:{SERVER_PORT}"

#ph = PasswordHasher()
class Candidate(BaseModel):
    number: int
    name: str
    
def print_res(res: Response):
    json = get_res(res)
    
    if not json:
        print("No valid message body returned by server")
    else:
        print(json["message"])

def get_res(res: Response):
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        return None
    
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

if __name__ == "__main__":
    voting = True

    with open("public.pem", "rb") as f:
        server_pub_key_data = f.read()
        
    server_pub_key = rsa.PublicKey.load_pkcs1(server_pub_key_data, "PEM")
    
    print("Welcome to e-voting!")
    
    while(voting):
        user_pin = input("Please enter your 9 digit ID number, enter 'c' to check the vote numbers, or enter 'q' to exit: ")
        
        if user_pin.lower() == 'q':
            voting = False
            continue
        
        if user_pin.lower() == 'c':
            check_votes()
            continue
        
        if not str.isdecimal(user_pin) or len(user_pin) != 9:
            print("PIN must be a 9 digit PIN or 'q' to quit!")
            continue

        
        auth_req_data = {
            "PIN": user_pin
        }
        
        auth_req_data = json.dumps(auth_req_data).encode("utf8")
        
        enc_req = rsa.encrypt(auth_req_data, server_pub_key)
        
        response = requests.post(url=f"{SERVER_URL}/authorize", data=enc_req, headers={'Content-Type': 'application/octet-stream'})
        
        if(response.status_code != 200):
            print(f"Server responded with {response.status_code}!")
            print_res(response)
            continue
        
        response = requests.get(url=f"{SERVER_URL}/candidates")
        
        response_text = get_res(response)
        
        if response_text is None or "candidates" not in response_text or len(response_text["candidates"]) == 0:
            print("Could not find cadidates in response!")
            continue
        
        candidates = response_text["candidates"]
        
        print("Submitting your ballot:\n")
            
        candidate_choice: str = ""
        while True:
            candidate_number: int = 1
            for candidate in candidates:
                print(f"{candidate_number}: {candidate}")
                candidate_number += 1
            
            candidate_choice = input(f"Choose the candidate you would like to vote for (numbers 1 - {len(candidates)}): ")
            
            if not candidate_choice.isdecimal():
                print(f"Please only enter numbers for your choice!")
                continue
            
            elif len(candidate_choice) > 1 or len(candidate_choice) < 1:
                print("Please enter at most and at least 1 number for your choice!")
                continue
            
            elif int(candidate_choice) < 1 or int(candidate_choice) > len(candidates):
                print(f"Your choice should be between the numbers 1 and {len(candidates)}")
                continue
            
            else:
                break
            
        ballot = {
            "PIN": user_pin,
            "Vote": candidates[int(candidate_choice) - 1]
        }
        
        ballot_req_data = json.dumps(ballot).encode("utf8")

        #!!! REMOVE !!!
        print(ballot_req_data)
        
        ballot_req_enc = rsa.encrypt(ballot_req_data, server_pub_key)
        
        response = requests.post(url=f"{SERVER_URL}/vote", data=ballot_req_enc, headers={'Content-Type': 'application/octet-stream'})
        
        if response.status_code == status.HTTP_200_OK:
            print("Vote received! Deauthenticating...")
            response = requests.post(url=f"{SERVER_URL}/deauthorize", data=enc_req, headers={'Content-Type': 'application/octet-stream'})
            
            if response.status_code != status.HTTP_200_OK:
                print("Could not deauthorize your pin!")
                print_res(response)

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


class PIN(BaseModel):
    PIN: str

class Vote(BaseModel):
    PIN: str
    Vote: str

app = FastAPI()
PORT = 8000
private_key = None
public_key = None

PINS_FILE = "PIN.csv"
VOTES_FILE = "votes.csv"

candidate_votes_internal = {}

def read_database(filename: str) -> list[dict]:
    """
    Takes in a filename and returns the contents of the file as a list of OrderedDicts.
    """

    # this function can be modified if we need to switch from a CSV to a sqlite database or smth else
    output = []
    with open(filename, mode='r') as db_file:
        csv_reader = csv.DictReader(db_file)
        for entry in csv_reader:
            output.append(entry)

    return output

def write_database(filename: str, data: list[dict]):
    """
    Writes a list of data to the given file.
    """

    with open(filename, mode='w') as db_file:
        field_names = data[0].keys()

        csv_writer = csv.DictWriter(db_file, field_names, lineterminator="\n")
        csv_writer.writeheader()

        csv_writer.writerows(data)

def check_pin_voted(pin: str) -> bool:
    """
    Checks if a given PIN has already voted.
    """
    votes_file = read_database(VOTES_FILE)
    for entry in votes_file:
        if entry["PIN"] == pin:
            return True

    return False

def handle_vote(vote: Vote) -> int:
    if check_pin_voted(vote.PIN):
        return status.HTTP_403_FORBIDDEN

    # checking if the PIN has been authorized
    votes = read_database(VOTES_FILE)
    pins = read_database(PINS_FILE)
    for entry in pins:
        if entry["PIN"] == vote.PIN and entry["auth"] != 'True':
            return status.HTTP_401_UNAUTHORIZED

    votes.append({"PIN": vote.PIN})

    # extremely simple sanitization, making sure they cant overwrite someone's PIN, doubt this is really an issue though
    # also a check to make sure a valid candidate was given
    if vote.Vote == "PIN" or vote.Vote not in votes[0].keys():
        return status.HTTP_400_BAD_REQUEST

    candidate_votes = votes[0]
    
    print(candidate_votes)
    
    candidate_votes[vote.Vote] = int(candidate_votes[vote.Vote]) + 1

    if vote.Vote not in candidate_votes_internal:
        candidate_votes_internal[vote.Vote] = 1
    else:
        candidate_votes_internal[vote.Vote] += 1

    write_database(VOTES_FILE, votes)

    return status.HTTP_200_OK

async def decrypt_request(request: Request) -> tuple[bool, dict[str, str]]:
    if private_key is None:
        print("[!] No private key provided")
        return False, {}

    body = await request.body()

    decrypted = rsa.decrypt(body, private_key)

    return True, json.loads(decrypted)

def initialize_votes_internal():
    votes = read_database(VOTES_FILE)
    candidate_votes = votes[0]
    for candidate in candidate_votes:
        if candidate == "PIN":
            continue
        candidate_votes_internal[candidate] = int(candidate_votes[candidate])

def validate_external_count() -> dict:
    """
    Returns a dict of all candidates and the difference between the number of votes they have and how many have been
    recorded in the database, alongside the number of PINs and the total number of votes.
    """
    output = {}
    votes = read_database(VOTES_FILE)

    num_pins = len(votes) - 1
    print(num_pins)
    total_votes = 0

    candidate_votes = votes[0]
    for candidate in candidate_votes:
        if candidate == "PIN":
            continue

        vote_count = int(candidate_votes[candidate])
        total_votes += vote_count

        if candidate not in candidate_votes_internal:
            candidate_votes_internal[candidate] = 0

        # output[candidate] = abs(candidate_votes_internal[candidate] - vote_count)
        output[candidate] = candidate_votes_internal[candidate]

    # output["num_pins"] = abs(total_votes - num_pins)
    output["num_pins"] = num_pins
    return output

def hash_pin(pin: str):
    hashed_pin = sha256(pin.encode("utf8")).digest()
    return base64.b64encode(hashed_pin).decode("utf8")

@app.get("/candidates")
def get_candidates():
    votes_db = read_database(VOTES_FILE)
    candidates = list(votes_db[0].keys())[1:]
    return Response(status_code=status.HTTP_200_OK, content=json.dumps({"candidates": candidates}))

@app.get("/validate_votes")
def validate_votes_endpoint():
    return JSONResponse(status_code=status.HTTP_200_OK, content=json.dumps(validate_external_count()))

@app.post("/deauthorize")
async def deauthorize_pin_endpoint(request: Request):

    (decrypted, pin) = await decrypt_request(request)
    
    if not decrypted:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # this makes sure we have the correct data
    if "PIN" not in pin:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=json.dumps({"message": "Could not find PIN field!"}))
    
    return authorize(pin["PIN"], False)

@app.post("/authorize")
async def authorize_pin_endpoint(request: Request):

    print (request)

    (decrypted, pin) = await decrypt_request(request)

    if not decrypted:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # this makes sure we have the correct data
    if "PIN" not in pin:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=json.dumps({"message": "Could not find PIN field!"}))

    return authorize(pin["PIN"], True)

def authorize(pin_unhashed: str, authorize_state: bool = True):
    pin = hash_pin(pin_unhashed)
    if authorize_state and check_pin_voted(pin):
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=json.dumps({"message": "PIN already voted!"}))

    if authorize_pin(pin.strip(), authorize_state):
        return Response(status_code=status.HTTP_200_OK, content=json.dumps({"message": "PIN Authorized!"}))
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content=json.dumps({"message": "PIN not authorized!"}))

def authorize_pin(pin: str, authorize_state: bool = True) -> bool:
    """
    Takes in a PIN, and if valid, authorizes the PIN to vote and returns True, returns False otherwise.
    """

    if authorize_state and check_pin_voted(pin):
       return False

    valid_pins = read_database(PINS_FILE)

    valid = False
    for pin_entry in valid_pins:
        if pin_entry["PIN"] == pin:
            pin_entry["auth"] = authorize_state
            valid = True
            break

    if valid:
        write_database(PINS_FILE, valid_pins)

    return valid

@app.post("/vote")
async def vote_endpoint(request: Request):
    (decrypted, vote) = await decrypt_request(request)

    if not decrypted:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if "PIN" not in vote or "Vote" not in vote:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    print("Validating vote")
    
    vote = Vote(PIN = hash_pin(vote["PIN"].strip()), Vote = vote["Vote"].strip())

    return Response(status_code=handle_vote(vote))

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
        
    initialize_votes_internal()

    uvicorn.run(app, host="0.0.0.0", port=PORT)
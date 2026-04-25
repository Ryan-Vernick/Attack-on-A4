
import base64
from hashlib import sha256
import csv

from datetime import datetime
import multiprocessing
'''
import rsa
import uvicorn
import json
from pydantic import BaseModel
from pathlib import Path
from fastapi import FastAPI, status, Request
from fastapi.responses import Response
from starlette.responses import JSONResponse
'''
##########################
###  PULLED FROM server.py DIRECTLY
##########################

# takes in an unhashed PIN, and returns it after being hashed and encoded
def hashPin(pin: str):
    hashed_pin = sha256(pin.encode("utf8")).digest()
    return base64.b64encode(hashed_pin).decode("utf8")

##########################
### ADAPTED FROM server.py
##########################

#Takes takes the csv of valid PINs (with other information) and turns it into a list of just the valid pins
# this hopefully redices overhead by making fewer file read calls
# if the csv were adapted to be a database, this would definitely reduce calls and thus time
def readPins():

    output = []
    with open("PIN.csv", mode='r') as db_file:
        csv_reader = csv.DictReader(db_file)
        for entry in csv_reader:
            valid_hashed_pins.append(entry["PIN"])

## takes in a hasked pin, and sees if that hash is stored as a valid user PIN
def isValidPin(pin: str):
    # get the list of valid pins
    pins = valid_hashed_pins

    # if any of the pin hashes match what you have, return that you found a valid PIN
    # and remove that pin from the list you are searching through
    for entry in pins:
        if entry == pin:
            valid_hashed_pins.remove(pin)
            return True
    
    # if none return True, it is not a valid PIN
    return False



##########################
### ENTIRELY OUR OWN CODE
##########################

RANGE = 100_000_000

valid_hashed_pins = []

readPins()

# goes through N numbers, wher N = RANGE
# for each number: it hashes it, uses utf-8 encoding, and then checks it against the list of known valid hashed keys
# if it is a valid key: it saves the hashed/unhashed key pair in a list that can be checked much more easily
def checkHashes(startNum: int):

    pin = startNum

    while pin < (startNum + RANGE):
        hashed_pin = hashPin(str(pin))
        if isValidPin(hashed_pin):
            print (f"{pin} is a valid PIN")
        pin += 1


if __name__ == '__main__':

    start_time = datetime.now()

    ##checkHashes(111_111_100)

    
    p0 = multiprocessing.Process(target= checkHashes, args=(0,))
    p1 = multiprocessing.Process(target= checkHashes, args=(100_000_000,))
    p2 = multiprocessing.Process(target= checkHashes, args=(200_000_000,))
    p3 = multiprocessing.Process(target= checkHashes, args=(300_000_000,))
    p4 = multiprocessing.Process(target= checkHashes, args=(400_000_000,))
    p5 = multiprocessing.Process(target= checkHashes, args=(500_000_000,))
    p6 = multiprocessing.Process(target= checkHashes, args=(600_000_000,))
    p7 = multiprocessing.Process(target= checkHashes, args=(700_000_000,))
    p8 = multiprocessing.Process(target= checkHashes, args=(800_000_000,))
    p9 = multiprocessing.Process(target= checkHashes, args=(900_000_000,))

    #checkHashes(111_100_000)

    p1.start()
    p2.start()
    p3.start()
    p4.start()
    p5.start()
    p6.start()
    p7.start()
    p8.start()
    p9.start()

    p1.join()
    p2.join()
    p3.join()
    p4.join()
    p5.join()
    p6.join()
    p7.join()
    p8.join()
    p9.join()
    

    end_time = datetime.now()

    runtime = end_time - start_time

    print(f"{RANGE*10} PINs took {runtime} seconds to execute")
    #print(hash_pin(str(111111111)))

    #testHash = hash_pin(str(111111112))
    #print (is_valid_pin(testHash))
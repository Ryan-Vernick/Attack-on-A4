
import base64
from hashlib import sha256
import csv

from datetime import datetime
import time
import multiprocessing
import asyncio
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
    # makes the PIN.csv readable
    with open("PIN.csv", mode='r') as db_file:
        csv_reader = csv.DictReader(db_file)

        # as you read through PIN.csv, add each pin to a local list
        for entry in csv_reader:
            valid_hashed_pins.append(entry["PIN"])

## takes in a hasked pin, and sees if that hash is stored as a valid user PIN
def isValidPin(pin: str):
    # get the list of valid pins
    pins = valid_hashed_pins

    # if any of the pin hashes match what you have, return that you found a valid PIN
    for entry in pins:
        if entry == pin:
            valid_hashed_pins.remove(pin)
            return True
    
    # if none return True, it is not a valid PIN
    return False



##########################
### ENTIRELY OUR OWN CODE
##########################

# how many pins each thread will search through
RANGE = 100_000

# a list of known valid pins (pulled from PIN.csv)
valid_hashed_pins = []
readPins()

known_pins = {}

SEARCHING = False
KEYS_KNOWN = False

# goes through N numbers, wher N = RANGE
# for each number: it hashes it, uses utf-8 encoding, and then checks it against the list of known valid hashed keys
# if it is a valid key: it saves the hashed/unhashed key pair in a list that can be checked much more easily
def checkHashes(startNum: int, pins_dict):

    local_known_pins = []

    # sets the starting pin as the input value
    pin = startNum

    # keeps going for the decided range of the keyspace
    while pin < (startNum + RANGE):

        # hashes the guessed PIN
        hashed_pin = hashPin(str(pin))

        # if it matches a known valid pin, add the pin to a dict of known pins, with the hash as it's key
        if isValidPin(hashed_pin):

            pins_dict[hashed_pin] = pin
            ###pins_dict.append([hashed_pin, pin])

            print (f"{pin} is a valid PIN")

        # incrememnt to the next pin
        pin += 1

async def findKeys():

    SEARCHING = True

    manager = multiprocessing.Manager()
    ret_dict = manager.dict()

    # assigns processes their own sections of the keyspace to search
    p0 = multiprocessing.Process(target= checkHashes, args=(0,ret_dict))
    '''
    p1 = multiprocessing.Process(target= checkHashes, args=(100_000_000,ret_dict))
    p2 = multiprocessing.Process(target= checkHashes, args=(200_000_000,ret_dict))
    p3 = multiprocessing.Process(target= checkHashes, args=(300_000_000,ret_dict))
    p4 = multiprocessing.Process(target= checkHashes, args=(400_000_000,ret_dict))
    p5 = multiprocessing.Process(target= checkHashes, args=(500_000_000,ret_dict))
    p6 = multiprocessing.Process(target= checkHashes, args=(600_000_000,ret_dict))
    p7 = multiprocessing.Process(target= checkHashes, args=(700_000_000,ret_dict))
    p8 = multiprocessing.Process(target= checkHashes, args=(800_000_000,ret_dict))
    p9 = multiprocessing.Process(target= checkHashes, args=(900_000_000,ret_dict))
    '''

    p1 = multiprocessing.Process(target= checkHashes, args=(111_100_000,ret_dict))
    p2 = multiprocessing.Process(target= checkHashes, args=(222_200_000,ret_dict))
    p3 = multiprocessing.Process(target= checkHashes, args=(333_300_000,ret_dict))
    p4 = multiprocessing.Process(target= checkHashes, args=(444_400_000,ret_dict))
    p5 = multiprocessing.Process(target= checkHashes, args=(555_500_000,ret_dict))
    p6 = multiprocessing.Process(target= checkHashes, args=(666_600_000,ret_dict))
    p7 = multiprocessing.Process(target= checkHashes, args=(777_700_000,ret_dict))
    p8 = multiprocessing.Process(target= checkHashes, args=(888_800_000,ret_dict))
    p9 = multiprocessing.Process(target= checkHashes, args=(999_900_000,ret_dict))    

    # searches the keyspace
    p0.start()
    p1.start()
    p2.start()
    p3.start()
    p4.start()
    p5.start()
    p6.start()
    p7.start()
    p8.start()
    p9.start()
    

    # waits for them all to return
    p0.join()
    p1.join()
    p2.join()
    p3.join()
    p4.join()
    p5.join()
    p6.join()
    p7.join()
    p8.join()
    p9.join()

    #print(ret_dict)
    known_pins.update(ret_dict)
    #print(known_pins)
    

    SEARCHING = False
    IS_DONE = True


# originally returned (still does) a dictionary containing the PINS.
# because it's now called asynchronously, it now includes a parameter to pass your own dictionary that it will put the PINS into
async def getKeys(ret_dict: dict):

    if  (not SEARCHING) and (not KEYS_KNOWN):
        await findKeys()
        ret_dict.update(known_pins)
        return known_pins

    elif (SEARCHING) and (not KEYS_KNOWN):
        print ("waiting for keys to be known...")
        time.sleep(30)
        return getKeys(ret_dict)
    
    else:
        ret_dict.update(known_pins)
        return known_pins

if __name__ == '__main__':

    start_time = datetime.now()

    myPins = {}

    asyncio.run(getKeys(myPins))   

    print(f"the pins are:")
    for key, val in myPins.items():
        print(f"{key}: {val}")

    end_time = datetime.now()

    runtime = end_time - start_time

    print(f"{RANGE*10} PINs took {runtime} seconds to execute")
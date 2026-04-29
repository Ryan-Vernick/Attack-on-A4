# Running the code

First, create a Python venv in the root folder here and run the following command to install all the dependencies:

```
python -m pip install -r requirements.txt
```

Then, open three terminal windows and run first the `server.py` file first in one window, followed by the `router.py` file in the second, and lastly the `client.py` file in the thirs window. Follow the on-screen prompts to authenticate a pin and submit a ballot. The following pins are already registered to be used, any other pins will not be allowed to submit a ballot to the server. If you want to reset the ballots, clear the pins from the `votes.csv` file and change the numbers under each candidate to 0.



After submitting a vote via the client, if you go to the router window, you will see both of out implemented attacks working. 
- First, a leaked private key attack that allows us to simply read the vote request as it passes through. this appears directly along with each vote, and shows up as 


// Breach
// Intercepted Plaintext PIN: [clients pin]
// Intercepted Vote For: Candidate [candidate of choice]


-Second, a brute force attack on the valid PINs. This attack creates a separate thread that goes through the entire keyspace, saving the hashed and unhashed versions of every valid key into a dictionary. Separately, as each vote comes in, it saves the before and after state of the election data (candidate votes & voted PINs). When the thread finding all valid keys finishes, it goes through the collected data and finds the pin and candidate of each vote already cast. After that, it finds that information live as the vote goes through. this will show up in terminal as either:

// bruteforce: pins not known yet 

if the thread is still running, OR

// bruteforce: voter with PIN #[client's pin] voted for candidate [candidate of choice].

if the thread is finished already.



Valid PINs:

* 528293088
* 123456789
* 987654321
* 1111111111
* 222222222
* 333333333
* 444444444
* 555555555
* 666666666
* 777777777
* 888888888
* 999999999

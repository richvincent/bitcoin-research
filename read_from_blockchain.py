import json
import urllib2

# Function to gather json data from blockchain address
def get_blockchain_json(address):
    #API call to blockchain
    url = "https://blockchain.info/address/"+ address +"?format=json"
    # Open url and extract raw data; if error, set json_obj to None
    try:
        json_obj = urllib2.urlopen(url)
    except Exception as e:
        print("[-] Error accessing address '{}' : {}".format(address,e))
        json_obj = None
    # If available, load raw data into json format and return; return None otherwise
    if json_obj:
        return json.load(json_obj)
    else:
        return None

        
if __name__ == '__main__':
    test_addresses = ['1GA9RVZHuEE8zm4ooMTiqLicfnvymhzRVm','1NAF7GbdyRg3miHNrw2bGxrd63tfMEmJob','1HS9RLmKvJ7D1ZYgfPExJZQZA1DMU3DEVd']
    for taddr in test_addresses:
        data = get_blockchain_json(taddr)
        print data
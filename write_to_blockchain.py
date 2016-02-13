import binascii
from btctxstore import BtcTxStore
from blockchain import createwallet
from blockchain.wallet import Wallet
from blockchain import blockexplorer
from blockchain import exchangerates
from blockchain import pushtx
from blockchain import statistics

# Create a test wallet
wifs = ["cUZfG8KJ3BrXneg2LjUX4VoMg76Fcgx6QDiAZj2oGbuw6da8Lzv1"]

# use testnet and dont post tx to blockchain for example
api = BtcTxStore(testnet=True, dryrun=False)

# store data in blockchain as nulldata output (max 40bytes)
data = binascii.hexlify(b"example_data")
txid = api.store_nulldata(data, wifs)

# Show current transaction id
print("Current Transaction ID: {}".format(txid))


# Now, retrieve data based on transaction id
hexnulldata = api.retrieve_nulldata(txid)


print("Retrieved Data: {}".format(hexnulldata))

# create new private key
wif = api.create_key()  

 # get private key address
address = api.get_address(wif) 

 # hexlify messagetext
data = binascii.hexlify(b"messagetext")

# sign data with private key
signature = api.sign_data(wif, data)
print("signature:", signature)

# verify signature (no public or private key needed)
isvalid = api.verify_signature(address, signature, data)
print("valid signature" if isvalid else "invalid signature")
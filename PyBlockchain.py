
# coding: utf-8

# In[2]:

from blockchain import createwallet
from blockchain.wallet import Wallet
from blockchain import blockexplorer
from blockchain import exchangerates
from blockchain import pushtx
from blockchain import statistics
import binascii


# In[ ]:

# First, create a wallet for your account.
# Go to https://blockchain.info/api/api_create_code and request and api...


# The following will display the current exchange rate between the Bitcoin Satoshi and the world's major currencies.
ticker = exchangerates.get_ticker()
#print the 15 min price for every currency
for k in ticker:
    print(k, ticker[k].p15min)


# This code will create a Bitcoin wallet. The following are the parameters and an example declaration
# (this example won't work; you will first need an API Key and some bitcoins)
# Again, to get an API key, go to https://blockchain.info/api/api_create_code and request one.

#password : str - password for the new wallet. At least 10 characters.
#api_code : str - API code with the create wallets permission
#priv : str - private key to add to the wallet (optional)
#label : str - label for the first address in the wallet (optional)
#email : str - email to associate with the new wallet (optional)

wallet = createwallet.create_wallet(password = '1234password', 
                                    api_code = 'api-code-here-ex123456789',
                                    priv = 'optional-private-key',
                                    label='example string data',
                                    email='myemail@gmail.com')


                                    
# The following is how to perform a transaction with the wallet you created.
# The 'to' and 'from' addresses are examples; they may work, but I doubt it.

#to : str - receiving address
#amount : int - amount to send (in satoshi)
#from_address : str - specific address to send from (optional)
#fee : int - transaction fee in satoshi. Must be greater than default (optional)
#note : str - public note to include with the transaction if amount >= 0.005 BTC (optional)
payment = wallet.send(to='1NAF7GbdyRg3miHNrw2bGxrd63tfMEmJob', 
                      amount=1000000, 
                      from_address='1A8JiWcwvpY7tAopUkSnGuEYHmzGYfZPiq',
                      fee=0,
                      note='Here is an example')

                      
# This is the transaction number you would use to pull up the transaction you just made...
transaction_hash = payment.tx_hash


# To see how much money is currently in your wallet, use this line of code...
print(wallet.get_balance())


# This will print the addresses in the wallet

addresses = wallet.list_addresses()
for a in addresses:
    print(a.balance)

# This will show the balance of a given address
addr = wallet.get_address('1NAF7GbdyRg3miHNrw2bGxrd63tfMEmJob')
print(addr.balance)


# To pull up and explore a transaction; This uses an example transaction
tx = blockexplorer.get_tx('d4af240386cdacab4ca666d178afc88280b620ae308ae8d2585e9ab8fc664a94')


# Blockchain posts must be hexlified first. Here is a function to change a string to hex...
data = binascii.hexlify('here is where you would put the transaction data to be hexlified.')


# Now, to push (or "broadcast") the above data to the blockchain, do the following...
pushtx.pushtx(data)


# Here is another example which uses a valid hex string as an example...

hex_encoded_string = '0100000001fd468e431cf5797b108e4d22724e1e055b3ecec59af4ef17b063afd36d3c5cf6010000008c4930460221009918eee8be186035be8ca573b7a4ef7bc672c59430785e5390cc375329a2099702210085b86387e3e15d68c847a1bdf786ed0fdbc87ab3b7c224f3c5490ac19ff4e756014104fe2cfcf0733e559cbf28d7b1489a673c0d7d6de8470d7ff3b272e7221afb051b777b5f879dd6a8908f459f950650319f0e83a5cf1d7c1dfadf6458f09a84ba80ffffffff01185d2033000000001976a9144be9a6a5f6fb75765145d9c54f1a4929e407d2ec88ac00000000'

pushtx.pushtx(hex_encoded_string)


# To see the current statistics of the block chain, do this...
stats = statistics.get()


# And to see the number of transactions...
print(stats.number_of_transactions)


# In[ ]:




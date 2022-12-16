#!/usr/bin/env python3
import json
import os

import solcx
from dotenv import load_dotenv
from web3 import Web3

# read .env
load_dotenv()

# read config file
with open("web3_py_simple_storage/config.json", "r") as f:
    config = json.load(f)

# read .sol file
with open("web3_py_simple_storage/SimpleStorage.sol", "r") as f:
    simple_storage_file = f.read()

# compile the .sol code
solcx.install_solc("0.6.0")
compiled_sol = solcx.compile_standard(
    {
        "language": "Solidity",
        "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.6.0",
)

# save compiled file
with open("web3_py_simple_storage/SimpleStorage_compiled.json", "w") as f:
    json.dump(compiled_sol, f)

# deploy sol
byte_code = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"][
    "bytecode"
]["object"]

# get abi
abi = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["abi"]

# deploy on JavaScript VM (Remix (London)), so it is local net, not a test net
# =deploy on Local Ganache chain (similated blockchain) https://trufflesuite.com/ganache/
# connect to Ganache
w3 = Web3(Web3.HTTPProvider(config["goerliTestnet"]))
chain_id = config["goerliChainId"]
my_address = config["metamaskAcc1Address"]
pr_key = os.getenv("MM_PRIVATE_KEY")

# create contract
# 1. build contract deploy transaction
SimpleStorage = w3.eth.contract(abi=abi, bytecode=byte_code)

# 2. sign transaction
# get nonce as latest transaction count (so nunce here is just the nth transaction from my address)
nonce = w3.eth.getTransactionCount(my_address)

# every contract technically has a constructor (if no given, its blank),
# but web3.py requires some paramaets in addition to your defined ones
print("Creating contract...")
transaction = SimpleStorage.constructor().buildTransaction(
    {
        "gasPrice": w3.eth.gas_price,
        "chainId": chain_id,
        "from": my_address,
        "nonce": nonce,
    }
)

singed_transaction = w3.eth.account.sign_transaction(transaction, private_key=pr_key)

# 3. send transaction
tx_hash = w3.eth.send_raw_transaction(singed_transaction.rawTransaction)
# wait for block confirmations
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# working with contract
# contract address and contract abi is needed
# create contract
# address - either from Ganache or also in tr receipt
simple_storage = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
# use methods from SimpleStorage.sol
# interact with a Call -> simulate making the call and getting the return value
# to state change to the blockchain (like blue buttons in remix)
# so calling transaction just mean to simulate the behavior
# interact with a Transaction -> actual make a state change (like orange buttons in remic)
# but you can also transact a view function and it will try to make a state change (but view wont make a state change even for transact)

# Call -> call()
retrieve_res = simple_storage.functions.retrieve().call()
print(retrieve_res)

# update favoriteNumber with Transaction
# Transact -> build_transaction({})
# Step 1: build transaction with new nonce
print("Make transaction...")
store_tx = simple_storage.functions.store(256).build_transaction(
    {
        "gasPrice": w3.eth.gas_price,
        "chainId": chain_id,
        "from": my_address,
        "nonce": nonce + 1,  # each tx should have differen nonce
    }
)
# Step 2; sign transaction with private key
signed_store_tx = w3.eth.account.sign_transaction(store_tx, private_key=pr_key)
# Step 3: send transaction
tx_hash = w3.eth.send_raw_transaction(signed_store_tx.rawTransaction)
# Step 4: get verification
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
retrieve_res = simple_storage.functions.retrieve().call()
print(retrieve_res)

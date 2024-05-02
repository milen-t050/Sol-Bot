from colorama import Fore
import requests
import sys
import json
import base64
import asyncio
import solders
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction 
from solders.signature import Signature
from solders.transaction import Legacy
from solders.transaction import TransactionError
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solana.rpc.api import Client 
from solana.rpc.types import TxOpts
from solana.transaction import Transaction
import math

from datetime import datetime
import personal as p
from typing import Dict, Any, Optional, Sequence, Tuple, Union
import httpx

####################################################################################################
# CONFIG 
RESET = Fore.RESET
GREEN = Fore.GREEN
RED = Fore.RED
YELLOW = Fore.YELLOW
BLUE = Fore.BLUE
PURPLE = Fore.MAGENTA
CYAN = Fore.CYAN

SLIPPAGE = 1000 #in BPS, this is 10% slippage
SOL = "So11111111111111111111111111111111111111112"
PRIORITY_FEE_LAMPORTS = 1000000
KEY = p.sol_wallet_private_key
BASE_URL = "https://public-api.birdeye.so/defi/"

SWAP_MODE = "ExactIn", "ExactOut"
JUPITER_QUOTE_ENDPOINT = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_ENDPOINT = "https://quote-api.jup.ag/v6/swap"

api_devnet = "https://api.devnet.solana.com"
MAX_RETRIES = 3
CONFRIMATION_SLEEP_SECONDS = 0.5
BANK_NOTE_COMMITMENT = "confirmed"

'''
SIDENODE MAKE SURE TO HAVE AMOUNTS IN LAMPORTS
'''
####################################################################################################

def logWithTimestamp(message: str):
    timestamp = datetime.now().strftime("%Y/%m/%d %I:%M %p")
    print(f"{YELLOW}[{timestamp}] {message}{RESET}")
    
    

async def fetch_quote_response(
    input_mint: str,
    output_mint: str, 
    amount: int, 
    swap_mode: str=SWAP_MODE
) -> Dict[str, Any]:
    
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": amount,
        "slippageBps": SLIPPAGE,
        "swapMode": swap_mode
    }
        
    async with httpx.AsyncClient() as client:
        response = await client.get(JUPITER_QUOTE_ENDPOINT, params=params)
    await client.aclose()
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(e)
    
    if "error" in data.keys():
        print(f"Error: {data['error']}")
        print("oops")
    return data

asyncio.run(fetch_quote_response(SOL, "8XethNffiUbgXEsjqJcPZzJYkCw2Q44fhPuMrZsNaZda", 20, "ExactIn"))

async def fetch_swap_transaction(
    input_mint: str,
    output_mint: str, 
    amount: int,
    swap_mode: str=SWAP_MODE   
) -> Tuple[bytes, Dict[str, Any]]:

    quote_response = await fetch_quote_response(input_mint, output_mint, amount, swap_mode)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(JUPITER_SWAP_ENDPOINT, json={
            "qouteResponse": quote_response,
            "userPublicKey": p.sol_wallet_public_key,
            "wrapAndUnwrapSol" : True,
            "dynamicComputeUnitLimit": True,
            "prioritizationFeeLamports": PRIORITY_FEE_LAMPORTS
        })
    
    await client.aclose()
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(e)
    
    if "error" in data.keys():
        print(f"Error: {data['error']}")
        
    transaction_bytes = base64.b64decode(data['swapTransaction'])
    
    quote = {
        "inAmount": int(quote_response['inAmount']),
        "outAmount": int(quote_response['outAmount']),
        "priceImpactPct": float(quote_response['priceImpactPct']) # percentage
    }
    print(quote)
    print(transaction_bytes)
    
    return transaction_bytes, quote

async def create_swap_txn(
    input_mint: str,
    output_mint: str,
    amount: int,
    swap_mode: str=SWAP_MODE
) -> Tuple[Union[VersionedTransaction], Dict[str, Any]]:
    
    transaction_bytes, quote = await fetch_swap_transaction(input_mint, output_mint, amount, swap_mode)
    
    txn = VersionedTransaction.from_bytes(transaction_bytes)
    
    return txn, quote

async def send_txn(
    client: AsyncClient,
    txn: Union[Transaction, VersionedTransaction],
    signer: Keypair,
    max_retries: int=MAX_RETRIES,
    confirmation_sleep_seconds: float=0.5
    ) -> Signature:
    
    txn = Transaction.from_solders(txn) if isinstance(txn, Legacy) else txn
    num_retires = 0
    while num_retires < max_retries:
        try:
            blockhash_resp = await client.get_latest_blockhash(commitment=BANK_NOTE_COMMITMENT)
            recent_blockhash = blockhash_resp.value.blockhash
            last_valid_block_height = blockhash_resp.value.last_valid_block_height
            if not isinstance(txn, VersionedTransaction):
                txn_response = await client.send_transaction(txn, signer, recent_blockhash=recent_blockhash)
            else:
                txn = change_blockhash_of_versioned_transaction(txn, signer=signer, new_blockhash=recent_blockhash)
                txn_response = await client.send_transaction(txn)
            txn_signature = txn_response.value
            
            if txn_signature:
                confirmation_resp =  await client.confirm_transaction(
                    txn_signature,
                    commitment=BANK_NOTE_COMMITMENT,
                    sleep_seconds=confirmation_sleep_seconds
                    last_valid_block_height=last_valid_block_height
                )
                
                confirmation_json_resp = json.loads(confirmation_resp.value[0].to_json())
                if (
                    "status" in confirmation_json_resp.keys() and
                    "Ok" in confirmation_json_resp["status"].keys()
                ): raise Exception("Transaction failed")
                return txn_signature
        
        except (UnconfimredTxError, TransactionExpiredBlockheightExceededError) as e:
            num_retires += 1
            continue
        
        except RPCException as e:
            if "Blockhash not found" in str(e):
                num_retires += 1
                continue
            elif "0x1" in str(e) and "insufficent" in str(e):
                raise InsufficentFunndsError(f"Insufficent funds to complete transaction: {e}")
            elif "0x1771" in str(e):
                raise ExceededSlippageThresholdError(f"Exceeded slippage threshold: {e}")
            raise TransactionFailedError(e)
        
        raise TransactionFailedError("Transaction failed")


async def swap_spl_tokens(
    client: AsyncClient,
    sender_private_key: str,
    output_mint: Union[str, Keypair],
    input_token_amount: int,
    slippage: int,
    input_mint: str,
    swap_mode: str=SWAP_MODE  
) -> Tuple[Signature, Dict[str, Any]]:
    
    if isinstance(input_mint, Pubkey): input_mint = str(input_mint)
    if isinstance(output_mint, Pubkey): output_mint = str(output_mint)
    owner_keypair = Keypair.from_base58_string(p.sol_wallet_private_key)
    owner_public_key = owner_keypair.pubkey()
    
    # if input mint is SOL(WSOL), then the amount is multipleid by the LAMPORTS_PER_SOL (10^9)
    # else we get the decimal of the corresponding input mint and multiply by 10^decimal
    
    #Buy the SPL token
    if input_mint == SOL and output_mint != SOL:
        input_decimals = 9
        output_mint_pubkey = Pubkey.from_string(output_mint)
        supply_resp =  await client.get_token_supply(output_mint_pubkey, commitment=BANK_NOTE_COMMITMENT)
        output_decimals = json.loads(supply_resp.value.to_json())["decimals"]

    #Sell the SPL token
    elif input_mint != SOL and output_mint == SOL:
        output_decimals = 9
        input_mint_pubkey = Pubkey.from_string(input_mint)
        supply_resp =  await client.get_token_supply(input_mint_pubkey, commitment=BANK_NOTE_COMMITMENT)
        input_decimals = json.loads(supply_resp.value.to_json())["decimals"]
    
    else:
        raise Exception("We can only swap SOL pairs...")
    
    amount = math.ceil(input_token_amount * (10**input_decimals))
    priority_fee_lamports = math.ceil(PRIORITY_FEE_LAMPORTS * (10**output_decimals))
    
    #slippage is in BPS (Basis Points)
    slippage = SLIPPAGE
    
    txn, quote = await create_swap_txn(input_mint, output_mint, amount, swap_mode)
    
    txn_signature = await send_txn(
        client,
        txn=txn,
        signer=owner_keypair,
        max_retries=MAX_RETRIES
        confirmation_sleep_seconds=CONFRIMATION_SLEEP_SECONDS
    )
    
    quote["inAmount"] = quote["inAmount"] / (10**input_decimals)
    quote["outAmount"] = quote["outAmount"] / (10**output_decimals)
    
    return txn_signature, quote


    
    
    
    
        
    































































    

# def token_price(coin_address):

#     url = f"{BASE_URL}price?address={coin_address}"

#     headers = {"x-chain": "solana", "X-APi-KEY": p.birdEye_apiKey}

#     response = requests.get(url, headers=headers)

#     price_data = response.json()

#     if price_data['success']:
#         return price_data['data']['value']
#     else:
#         return None

# def get_sol_price_usd():
#     # Example using a public API - replace with your choice of API
#     response = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd')
#     data = response.json()
#     return data['solana']['usd']

# def calculate_lamports_for_dollar(dollar_amount):
#     sol_price = get_sol_price_usd()
#     sol_amount = dollar_amount / sol_price
#     lamports = sol_amount * 1_000_000_000
#     return int(lamports)

# def Buy(token, amount):
    
#     http_client = Client("https://api.mainnet-beta.solana.com")
    
#     token_pric = token_price(token)
    
#     logWithTimestamp("Getting the route for a swap")
#     quote = requests.get(f'https://quote-api.jup.ag/v6/quote?inputMint={SOL}&outputMint={token}&amount={amount}&slippage={SLIPPAGE}').json()

#     logWithTimestamp(quote)
    
#     logWithTimestamp("Getting the serialized transaction to swap")
    
#     txRes = requests.post("https://quote-api.jup.ag/v6/swap", headers={"Content-Type": "application/json"}, data=json.dumps({"quoteResponse": quote, "userPublicKey": p.sol_wallet_public_key})).json()
#     print(txRes)
    
#     logWithTimestamp("Deserializing the transaction")
#     swapTx = base64.b64decode(txRes['swapTransaction'])
#     tx1 = VersionedTransaction.from_bytes(swapTx)
#     tx2 = VersionedTransaction(tx1.message, [KEY])
    
#     logWithTimestamp("Executing the swap")
#     txId = http_client.send_raw_transaction(bytes(tx), TxOpts(skip_preflight=True)).value
#     logWithTimestamp(f"https://solscan.io/tx/{str(txId)}")
    
#     logWithTimestamp("Checking transaction status...")
#     get_transaction_details = http_client.confirm_transaction(tx_sig=Signature.from_string(str(txId)), sleep_seconds=1)
#     transaction_status = get_transaction_details.value[0].err

#     if transaction_status is None:
#         logWithTimestamp("Transaction SUCCESS!")
#     else:
#         logWithTimestamp(f"{RED}! Transaction FAILED!{RESET}")
    

# amount = calculate_lamports_for_dollar(1)
# print(f"Amount in lamports for $1: {amount}")
# Buy("8XethNffiUbgXEsjqJcPZzJYkCw2Q44fhPuMrZsNaZda", amount)
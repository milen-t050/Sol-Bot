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
from solders.transaction import Transaction as LegacyTransaction
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
PRIORITY_FEE_LAMPORTS = 5000
KEY = p.sol_wallet_private_key

SWAP_MODE = "ExactIn", "ExactOut"
JUPITER_QUOTE_ENDPOINT = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_ENDPOINT = "https://quote-api.jup.ag/v6/swap"

api_devnet = "https://api.devnet.solana.com"
api_mainnet = "https://api.mainnet-beta.solana.com"
MAX_RETRIES = 3
CONFRIMATION_SLEEP_SECONDS = 15 #12 worked sometimes, safe side 15
BANK_NOTE_COMMITMENT = "finalized"
AS_LEGACY_TRANSACTION = True

class ExceededSlippageThresholdError(Exception):
    """Exception raised when the slippage threshold for a transaction is exceeded."""
    pass

class TransactionFailedError(Exception):
    """Exception raised when a transaction fails to complete."""
    pass

class InsufficientFundsError(Exception):
    """Exception raised when there are not enough funds to perform a transaction."""
    pass

class RPCException(Exception):
    """Exception raised for RPC related errors."""
    pass

class UnconfirmedTxError(Exception):
    """Exception raised when a transaction remains unconfirmed past a certain threshold."""
    pass

class TransactionExpiredBlockheightExceededError(Exception):
    """Exception raised when a transaction is not confirmed before the last valid block height is exceeded."""
    pass


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
        "swapMode": swap_mode,
        "asLegacyTransaction": AS_LEGACY_TRANSACTION
    }
        
    async with httpx.AsyncClient() as client:
        response = await client.get(JUPITER_QUOTE_ENDPOINT, params=params)
    await client.aclose()
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(e)
    
    if "error" in data.keys():
        print(f"{CYAN}Error: {data['error']}{RESET}")
        
    logWithTimestamp(f"{PURPLE}Quote response fetched successfully")
    return data

async def fetch_swap_transaction(
    input_mint: str,
    output_mint: str, 
    amount: int,
    swap_mode: str=SWAP_MODE   
) -> Tuple[bytes, Dict[str, Any]]:

    quote_response = await fetch_quote_response(input_mint, output_mint, amount, swap_mode)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(JUPITER_SWAP_ENDPOINT, json={
            "quoteResponse": quote_response,
            "userPublicKey": p.sol_wallet_public_key,
            "wrapAndUnwrapSol" : True,
            "dynamicComputeUnitLimit": True,
            "prioritizationFeeLamports": PRIORITY_FEE_LAMPORTS,
            "asLegacyTransaction": AS_LEGACY_TRANSACTION,
        })
    
    await client.aclose()
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(e)
    
    if "error" in data.keys():
        print(f"{CYAN}Error: {data['error']}{RESET}")
     
    transaction_bytes = base64.b64decode(data['swapTransaction'])
    
    quote = {
        "inAmount": int(quote_response['inAmount']),
        "outAmount": int(quote_response['outAmount']),
        "priceImpactPct": float(quote_response['priceImpactPct']) # percentage
    }
    
    logWithTimestamp(f"{PURPLE}Swap transaction fetched successfully")
    
    return transaction_bytes, quote

async def create_swap_txn(
    input_mint: str,
    output_mint: str,
    amount: int,
    swap_mode: str=SWAP_MODE
) -> Tuple[Union[LegacyTransaction], Dict[str, Any]]:
    
    transaction_bytes, quote = await fetch_swap_transaction(input_mint, output_mint, amount, swap_mode)
    
    txn = LegacyTransaction.from_bytes(transaction_bytes)
    
    logWithTimestamp(f"{PURPLE}Transaction created successfully")
    
    return txn, quote

async def send_txn(
    client: AsyncClient,
    txn: Union[Transaction, LegacyTransaction],
    signer: Keypair,
    max_retries: int=MAX_RETRIES,
    confirmation_sleep_seconds: float=0.5
    ) -> Signature:
    
    txn = Transaction.from_solders(txn) if isinstance(txn, LegacyTransaction) else txn
    num_retires = 0
    while num_retires < max_retries:
        try:
            blockhash_resp = await client.get_latest_blockhash(commitment=BANK_NOTE_COMMITMENT)
            recent_blockhash = blockhash_resp.value.blockhash
            last_valid_block_height = blockhash_resp.value.last_valid_block_height
            
            tx_opts = TxOpts(
                skip_preflight=True,
                preflight_commitment=BANK_NOTE_COMMITMENT,
                max_retries=max_retries
                             )
            
            txn_response = await client.send_transaction(txn, signer, recent_blockhash=recent_blockhash)
            txn_sig = txn_response.value
            
            await asyncio.sleep(confirmation_sleep_seconds)
            
            if txn_sig:
                confirmation_resp =  await client.get_transaction(
                    txn_sig,
                    commitment="confirmed",
                )
                
                confirmation_json_resp = json.loads(confirmation_resp.value.to_json())
                
                if confirmation_json_resp.get('value', {}).get('transaction', {}).get('meta', {}).get('status', {}) is None:
                    raise Exception(f"{CYAN}Transaction failed{RESET}")
                
                logWithTimestamp(f"{PURPLE}Transaction confirmed successfully")
                
                return txn_sig
        
        except (UnconfirmedTxError, TransactionExpiredBlockheightExceededError) as e:
            num_retires += 1
            continue
        
        except RPCException as e:
            if "Blockhash not found" in str(e):
                num_retires += 1
                continue
            elif "0x1" in str(e) and "insufficent" in str(e):
                raise InsufficientFundsError(f"{CYAN}Insufficent funds to complete transaction: {e}{RESET}")
            elif "0x1771" in str(e):
                raise ExceededSlippageThresholdError(f"{CYAN}Exceeded slippage threshold: {e}{RESET}")
            raise TransactionFailedError(e)
        
        raise TransactionFailedError(f"{CYAN}Transaction failed{RESET}")
    logWithTimestamp(f"{CYAN}Transaction failed")


async def swap_spl_tokens(
    client: AsyncClient,
    output_mint: Union[str, Keypair],
    input_token_amount: int,
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
        logWithTimestamp(f"{GREEN}Getting the route for a swap, we are buying the SPL token...")

    #Sell the SPL token
    elif input_mint != SOL and output_mint == SOL:
        output_decimals = 9
        input_mint_pubkey = Pubkey.from_string(input_mint)
        supply_resp =  await client.get_token_supply(input_mint_pubkey, commitment=BANK_NOTE_COMMITMENT)
        input_decimals = json.loads(supply_resp.value.to_json())["decimals"]
        logWithTimestamp(f"{RED}Getting the route for a swap, we are selling the SPL token...")
    
    else:
        raise Exception(f"{CYAN}We can only swap SOL pairs...")
    
    amount = math.ceil(input_token_amount * (10**input_decimals))
    
    #slippage is in BPS (Basis Points)
    slippage = SLIPPAGE
    
    txn, quote = await create_swap_txn(input_mint, output_mint, amount, swap_mode)
    
    txn_signature = await send_txn(
        client,
        txn=txn,
        signer=owner_keypair,
        max_retries=MAX_RETRIES,
        confirmation_sleep_seconds=CONFRIMATION_SLEEP_SECONDS
    )
    
    quote["inAmount"] = quote["inAmount"] / (10**input_decimals)
    quote["outAmount"] = quote["outAmount"] / (10**output_decimals)
    
    logWithTimestamp(f"{BLUE}InAmount: {quote['inAmount']}, OutAmount: {quote['outAmount']}, Price Impact: {quote['priceImpactPct']}%{RESET}")
    
    return txn_signature, quote

async def main(
    intput_mint: str,
    input_token_amount: float,
    output_mint: str,
    swap_mode: str=SWAP_MODE  
):
    
    async with AsyncClient(p.http_provider) as client:
        txn_signature, quote = await swap_spl_tokens(client, output_mint, input_token_amount, intput_mint, swap_mode)
        logWithTimestamp(f"{BLUE}Transaction completed successfully")
        
# example use case for sell asyncio.run(main("8XethNffiUbgXEsjqJcPZzJYkCw2Q44fhPuMrZsNaZda", 7220, SOL, "ExactIn"))  
# example use case for buy asyncio.run(main(SOL, 0.0001, "8XethNffiUbgXEsjqJcPZzJYkCw2Q44fhPuMrZsNaZda", "ExactOut"))
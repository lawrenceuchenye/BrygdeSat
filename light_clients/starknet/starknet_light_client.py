import asyncio
from starknet_py.net.full_node_client import FullNodeClient
from dotenv import load_dotenv
import os

load_dotenv()

client = FullNodeClient(node_url=os.getenv("INFURA_STARKNET_RPC"))

async def get_starknet_proof():
    # The address you want to prove (must be a Starknet address)
    target_tx_hash ="0x11d1eaeb358c04a4c5f82ff60249eb1e923b220400b8dda8bd34442057ec073"
    
    # Starknet uses 'get_proof' which returns the state commitment
    # instead of the Ethereum-style eth_getProof
    # Fetch the transaction detailstx_details
    tx_details = await client.get_transaction(target_tx_hash)
    tx_receipt = await client.get_transaction_receipt(target_tx_hash)
    
    # Get the signature and block numbersignature
    signature = tx_details.signature  # List of field elementsblock_number
    block_number = tx_receipt.block_number
    print(f"Starknet Tx Hash Sign: {signature} Block number:{block_number}")

asyncio.run(get_starknet_proof())

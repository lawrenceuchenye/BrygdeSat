import asyncio
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.utils import compute_hash_on_elements
from poseidon_py.poseidon_hash import poseidon_hash

from dotenv import load_dotenv
import os

load_dotenv()

client = FullNodeClient(node_url=os.getenv("INFURA_STARKNET_RPC"))

async def get_siblings(block, target_tx_hash):
    # 1. Create the Leaves (Level 0)
    # Starknet Leaf = Poseidon(Transaction Hash, Poseidon Hash of Signature)
    leaves = []
    target_idx = -1
    
    for i, tx in enumerate(block.transactions):
        # Hash the signature array
        sig_hash = compute_hash_on_elements(tx.signature)
        # Combine with TX hash
        leaf =poseidon_hash(tx.hash, sig_hash)
        leaves.append(leaf)
        
        if hex(tx.hash) == target_tx_hash:
            target_idx = i
    
    if target_idx == -1:
        raise Exception("Transaction not found in this block!")

    print(leaves,target_idx)

    # 2. Generate the 64 Siblings
    siblings = []
    current_level = leaves
    idx = target_idx

    for _ in range(64):
        # Determine if your sibling is to the left or right
        # Even index = you are left, sibling is right (idx + 1)
        # Odd index = you are right, sibling is left (idx - 1)
        sib_idx = idx + 1 if idx % 2 == 0 else idx - 1
        
        # If sibling exists in this block, take it. Otherwise, use 0.
        if sib_idx < len(current_level):
            siblings.append(current_level[sib_idx])
        else:
            siblings.append(0)
        
        # Move up one level: pair up nodes and hash them
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i+1] if i+1 < len(current_level) else 0
            next_level.append(poseidon_hash(left, right))
        
        current_level = next_level
        idx //= 2 # Parent index is half of current index

    return siblings

# To use it in your main function:
# siblings = await get_siblings(block, target_tx_hash)
# print([hex(s) for s in siblings])

async def get_starknet_proof():
    # The address you want to prove (must be a Starknet address)
    target_tx_hash ="0x76900fba6a8c736d276ee2a3efc74aa85bd753a26ae26275e4f2c5b9839e837"
    
    # Starknet uses 'get_proof' which returns the state commitment
    # instead of the Ethereum-style eth_getProof
    # Fetch the transaction detailstx_details
    tx_details = await client.get_transaction(target_tx_hash)
    tx_receipt = await client.get_transaction_receipt(target_tx_hash)
    
    # Get the signature and block numbersignature
    signature = tx_details.signature  # List of field elementsblock_number
    block_number = tx_receipt.block_number
    block = await client.get_block_with_txs(block_number=block_number)

    print(await get_siblings(block,target_tx_hash))
    #print(f"Blocki tx root: {block.transactions}")
    
asyncio.run(get_starknet_proof())

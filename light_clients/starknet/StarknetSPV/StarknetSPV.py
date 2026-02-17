from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.utils import compute_hash_on_elements

from starkware.cairo.lang.compiler.cairo_compile import compile_cairo
from starkware.cairo.lang.compiler.program import Program
from poseidon_py.poseidon_hash import poseidon_hash
from starkware.cairo.lang.vm.cairo_runner import CairoRunner
from starkware.cairo.lang.vm.relocatable import RelocatableValue

import os
import subprocess
import json

from web3 import Web3
import asyncio

class StarknetSPV:
    def __init__(self,StarknetNode_APIKEY=None,EthereumNode_APIKEY=None):
        self.starknetnode_apikey=StarknetNode_APIKEY
        self.ethereumnode_apikey=EthereumNode_APIKEY
        self.signature=None
        self.block_number=None
        self.block=None
        self.state_root=None
        self.client=None
        self.transaction_commitment=None
        self.execution_traces=[]

    async def pullData(self,tx_hash):
        self.client = FullNodeClient(node_url=self.starknetnode_apikey)
        tx_details = await self.client.get_transaction(tx_hash)
        tx_receipt = await self.client.get_transaction_receipt(tx_hash)

        self.signature = tx_details.signature 
        self.block_number = tx_receipt.block_number
        self.block = await self.client.get_block_with_txs(block_number=self.block_number)
        self.state_root=self.block.new_root
        self.transaction_commitment=self.block.transaction_commitment
        current_dir = os.path.dirname(os.path.abspath(__file__))
        state_transition_file_path=os.path.join(current_dir,"state_transition.cairo")
        output_path = os.path.join(current_dir, "state_transition.json")

        subprocess.run([
            "cairo-compile",
            state_transition_file_path,
            "--output",
            output_path,
            "--proof_mode"
         ], check=True)
        
    def generate_cairo_trace(self):
          current_dir = os.path.dirname(os.path.abspath(__file__))
          trace_file = os.path.join(current_dir, "trace.bin")
          memory_file = os.path.join(current_dir, "memory.bin")
         
           
          # Create input JSON
          input_json_path = os.path.join(current_dir, "input.json")
          with open(input_json_path, "w") as f:
            json.dump({ "program_input":[hex(self.block.parent_hash), hex(self.block.new_root)]}, f)

          subprocess.run([
           "cairo-run",
           f"--program={os.path.join(current_dir,'state_transition.json')}",
           "--layout=starknet_with_keccak",
           f"--trace_file={trace_file}",
           f"--program_input={input_json_path}",
           f"--memory_file={memory_file}",
           f"--air_public_input=StarknetSPV/public_input.json",
           "--proof_mode"
          ], check=True)

          return trace_file, memory_file

    async def verify(self,anchor_contract):
        print(self.block)

    async def verifysibs(self):
        for tx in self.block.transactions:
            print(tx,"\n")
        #print(self.block.transaction_commitment)


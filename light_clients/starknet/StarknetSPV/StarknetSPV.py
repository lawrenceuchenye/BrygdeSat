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
       
        
    async def gen_execution_trace(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        program = compile_cairo(
        open(os.path.join(current_dir,"state_transition.cairo")).read(),
        prime=3618502788666131106986593281521497120414687020801267626233049500247285301249,     
        cairo_path=["/home/lawuche/brygdesat/light_clients/starknet/lib/python3.10/site-packages/starkware/cairo/common"],
      )
        
        input_data = {
        "prev_root": self.block.parent_hash, # or previous state root
        "new_root": self.block.new_root
        }

        # 2. Initialize the runner
        # proof_mode=True is required for generating a trace a prover can userunner
        runner = CairoRunner(program, layout="starknet", proof_mode=True)
        runner.initialize_segments()
    
        # This automatically places the 'implicit arguments' (builtin pointers) 
        # into the first cells of Segment 1 (1:0, 1:1, 1:2)
        runner.initialize_main_entrypoint()
        runner.initialize_vm(hint_locals={}, static_locals={})

        # 3. Inject Block Data into Memory
        # We must start at index 3 because 0, 1, and 2 are occupied by builtin pointers
        n_builtins = 5 
        data_address = runner.execution_base + n_builtins
    
        # Convert hex strings to integers
        prev_root_int = int(self.block.parent_hash, 16) if isinstance(self.block.parent_hash,str) else int(self.block.parent_hash)
        new_root_int = int(self.block.new_root, 16) if isinstance(self.block.new_root,str) else int(self.block.new_root)

        stack_ptr = runner.initialize_main_entrypoint()

        memory = runner.vm.run_context.memory
        memory[data_address] = prev_root_int
        memory[data_address + 1] = new_root_int

        runner.vm.run_context.pc = runner.program_base + program.get_label("main")
        runner.vm.run_context.fp = data_address
        runner.vm.run_context.ap = data_address + 2

        runner.vm.run_context.pc = runner.program_base + program.get_label("__start__")
    
        end_pc = runner.program_base + program.get_label("__end__")
        runner.run_until_pc(end_pc)

        # 2. PAD STEPS: Ensure we hit the minimum requirement (e.g., 32 or 64)
        # Some layouts require even more, but let's target 64 to be safe.
        MIN_STEPS = 2048
        while runner.vm.run_context.pc == end_pc and runner.vm.current_step < MIN_STEPS:
           runner.vm_step()
        runner.end_run()
        runner.finalize_segments()
        runner.relocate()

        with open("trace.bin", "wb") as f:
          runner.execution_trace.serialize(f)
    
        with open("memory.bin", "wb") as f:
          runner.relocated_memory.serialize(f)

        print(f"Successfully generated trace for block {self.block.block_number}")
        return "trace.bin", "memory.bin" 
     
    def generate_cairo_trace(self):
          current_dir = os.path.dirname(os.path.abspath(__file__))
          trace_file = os.path.join(current_dir, "trace.bin")
          memory_file = os.path.join(current_dir, "memory.bin")
         
           
          # Create input JSON
          input_json_path = os.path.join(current_dir, "input.json")
          with open(input_json_path, "w") as f:
              json.dump([hex(self.block.parent_hash), hex(self.block.new_root)], f)

          subprocess.run([
           "cairo-run",
           f"--program={os.path.join(current_dir,'state_transition.json')}",
           "--layout=starknet_with_keccak",
           f"--trace_file={trace_file}",
           f"--program_input={input_json_path}",
           f"--memory_file={memory_file}",
           "--proof_mode"
          ], check=True)

          return trace_file, memory_file

    async def verify(self,anchor_contract):
        print(self.block)

    async def verifysibs(self):
        for tx in self.block.transactions:
            print(tx,"\n")
        #print(self.block.transaction_commitment)


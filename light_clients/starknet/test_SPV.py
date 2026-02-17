import asyncio
from dotenv import load_dotenv
import os

from StarknetSPV.StarknetSPV import StarknetSPV

load_dotenv()

apikey=os.getenv("ALCHEMY_STARKNET_RPC")


spv=StarknetSPV(StarknetNode_APIKEY=apikey)
asyncio.run(spv.pullData("0x634172e2014e92089e0e3abea83454bb98d53368bd7bb359d907e104abcd392"))

print(spv.generate_cairo_trace())


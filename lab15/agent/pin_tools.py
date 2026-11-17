"""Створює agent/tool_manifest.json із довіреного сервера (хеші описів інструментів)."""
import asyncio, os, sys, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
import policy as P
from agent import Agent
async def main():
    a = Agent(secure=False, role="admin")
    async with a.connect():
        man = P.pin(a.tools.values())
    json.dump(man, open(P.ROOT + "/agent/tool_manifest.json", "w"), indent=1); print(man)
asyncio.run(main())

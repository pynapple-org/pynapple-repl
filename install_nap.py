import micropip
import asyncio

async def install_nap():
    await micropip.install("https://pynapple-org.github.io/pynapple-repl/files/pynapple-0.8.5-py3-none-any.whl")

asyncio.run(install_nap())


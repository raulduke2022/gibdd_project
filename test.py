import asyncio
import aiohttp
link = 'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/diagnostic?vin=XW8AC2NH3MK139916&checkType=restricted&captchaWord=31233&captchaToken=BFTbvxe7S3vu6rccU/v/QA05MKcjGEwstsmXsKNYd30='

HEADERS = {
    "User-Agent": 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36',
    "Accept": "application/json"
}


async def get(session):
    async with session.post(link) as resp:
        return await resp.json()


async def main():
    connector = aiohttp.TCPConnector(limit_per_host=1)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        tasks = []
        for i in range(5):
           tasks.append(asyncio.create_task(get(session)))
        result = await asyncio.gather(*tasks)
        print(result)


asyncio.run(main())
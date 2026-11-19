import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(verify=False, timeout=30, follow_redirects=True) as c:
        r = await c.get("https://hnrss.org/frontpage")
        print("status:", r.status_code, "len:", len(r.text))

asyncio.run(main())

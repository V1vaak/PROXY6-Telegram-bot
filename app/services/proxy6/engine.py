from config import PROXY_API_KEY

from app.services.proxy6.client import AsyncProxy6


proxy_client = AsyncProxy6(PROXY_API_KEY)

async def on_startup():
    await proxy_client.__aenter__()
    print('Proxy6 client STARTED')

async def on_shutdown():
    await proxy_client.close()
    print('Proxy6 client CLOSED')
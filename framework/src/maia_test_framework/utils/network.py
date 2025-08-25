import time
import httpx
import asyncio

from maia_test_framework.logging_config import get_logger

logger = get_logger(__name__)

async def wait_for_service(host: str, timeout=60):
    """Waits for a service at the given host to be available."""
    logger.info(f"Waiting for service at {host} to be available...")
    start_time = time.time()
    url = f"{host}/"
    while time.time() - start_time < timeout:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                if response.status_code == 200:
                    logger.info(f"Service at {host} is available.")
                    return
        except httpx.ConnectError:
            await asyncio.sleep(1)
    raise TimeoutError(f"Service at {host} not available after {timeout} seconds.")

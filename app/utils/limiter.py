from slowapi import Limiter
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

def get_store_only_key(request: Request) -> str:
    """
    Tenant-only Key for ALL requests (StoreID only)
    Limits the total consumption of a single merchant's quota, 
    regardless of origin IP or client.
    """
    # Extract store_id from path parameters
    store_id = request.path_params.get("store_id", "global")
    return store_id

# Initialize Limiter with the store-only key function
limiter = Limiter(key_func=get_store_only_key)

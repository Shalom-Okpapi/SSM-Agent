import time
import requests
from settings import REQUEST_TIMEOUT, MAX_RETRIES

def request_with_retry(method: str, url: str, **kwargs):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.request(
                method,
                url,
                timeout=REQUEST_TIMEOUT,
                **kwargs
            )
            return resp
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * attempt)
    raise last_error

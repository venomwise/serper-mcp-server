import os
import ssl
import logging
import time
from typing import Dict, Any
import certifi
import aiohttp
from pydantic import BaseModel
from .enums import SerperTools
from .schemas import WebpageRequest

SERPER_API_KEY = str.strip(os.getenv("SERPER_API_KEY", ""))
AIOHTTP_TIMEOUT = int(os.getenv("AIOHTTP_TIMEOUT", "15"))
LOG_PAYLOAD_LIMIT = int(os.getenv("SERPER_LOG_PAYLOAD_LIMIT", "200"))

logger = logging.getLogger(__name__)


async def google(tool: SerperTools, request: BaseModel) -> Dict[str, Any]:
    uri_path = tool.value.split("_")[-1]
    url = f"https://google.serper.dev/{uri_path}"
    logger.debug("准备调用 Google Serper 接口：%s", url)
    return await fetch_json(url, request)


async def scape(request: WebpageRequest) -> Dict[str, Any]:
    url = "https://scrape.serper.dev"
    logger.debug("准备调用网页抓取接口：%s", url)
    return await fetch_json(url, request)


def _summarize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, str) and len(value) > LOG_PAYLOAD_LIMIT:
            summary[key] = f"{value[:LOG_PAYLOAD_LIMIT]}...(已截断)"
        else:
            summary[key] = value
    return summary


async def fetch_json(url: str, request: BaseModel) -> Dict[str, Any]:
    payload = request.model_dump(exclude_none=True)
    payload_summary = _summarize_payload(payload)
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    timeout = aiohttp.ClientTimeout(total=AIOHTTP_TIMEOUT)
    start_time = time.monotonic()
    logger.debug("发起请求：%s，超时：%ss，参数：%s", url, AIOHTTP_TIMEOUT, payload_summary)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status >= 400:
                    elapsed_ms = (time.monotonic() - start_time) * 1000
                    logger.warning("请求失败：%s，状态码：%s，耗时：%.1fms", url, response.status, elapsed_ms)
                    response.raise_for_status()

                data = await response.json()
                elapsed_ms = (time.monotonic() - start_time) * 1000
                logger.debug("请求成功：%s，状态码：%s，耗时：%.1fms", url, response.status, elapsed_ms)
                return data
    except Exception:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.exception("请求异常：%s，耗时：%.1fms", url, elapsed_ms)
        raise

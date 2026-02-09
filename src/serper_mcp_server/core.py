import os
import ssl
import logging
import time
import asyncio
from typing import Dict, Any, List
import certifi
import aiohttp
from pydantic import BaseModel
from .enums import SerperTools
from .schemas import WebpageRequest, MultiRegionSearchRequest, REGION_CONFIGS

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


async def _search_single_region(
    session: aiohttp.ClientSession,
    gl: str,
    hl: str,
    query: str,
    num: str,
    tbs: str | None,
) -> Dict[str, Any]:
    """执行单个地区的搜索请求"""
    url = "https://google.serper.dev/search"
    payload: Dict[str, Any] = {"q": query, "gl": gl, "hl": hl, "num": num}
    if tbs:
        payload["tbs"] = tbs

    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    start_time = time.monotonic()
    try:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status >= 400:
                elapsed_ms = (time.monotonic() - start_time) * 1000
                logger.warning("地区 %s 搜索失败，状态码：%s，耗时：%.1fms", gl, response.status, elapsed_ms)
                return {"error": f"HTTP {response.status}", "gl": gl, "hl": hl}

            data = await response.json()
            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.debug("地区 %s 搜索成功，耗时：%.1fms", gl, elapsed_ms)
            return {"gl": gl, "hl": hl, "query": query, **data}
    except Exception as e:
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.exception("地区 %s 搜索异常，耗时：%.1fms", gl, elapsed_ms)
        return {"error": str(e), "gl": gl, "hl": hl}


async def google_multi_region(request: MultiRegionSearchRequest) -> Dict[str, Any]:
    """并行执行多地区搜索"""
    regions = REGION_CONFIGS.get(request.preset, [])
    if not regions:
        return {"error": f"Unknown preset: {request.preset}"}

    logger.debug("开始多地区搜索，预设：%s，地区数：%d", request.preset, len(regions))

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=AIOHTTP_TIMEOUT)

    translations = request.translations or {}
    results: Dict[str, Any] = {}
    failed_regions: List[str] = []

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for region in regions:
            gl = region["gl"]
            hl = region["hl"]
            # 优先使用翻译，否则使用原始查询
            query = translations.get(hl, request.q)
            tasks.append(_search_single_region(session, gl, hl, query, request.num, request.tbs))

        responses = await asyncio.gather(*tasks)

        for region, response in zip(regions, responses):
            gl = region["gl"]
            if "error" in response:
                failed_regions.append(gl)
            results[gl] = response

    return {
        "query": request.q,
        "preset": request.preset,
        "results": results,
        "metadata": {
            "total_regions": len(regions),
            "successful_regions": len(regions) - len(failed_regions),
            "failed_regions": failed_regions,
        },
    }

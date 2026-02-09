from typing import Any, List, Sequence
import json
import logging

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

load_dotenv()

from .core import google, scape, SERPER_API_KEY
from .enums import SerperTools
from .schemas import (
    SearchRequest,
    MapsRequest,
    ReviewsRequest,
    ShoppingRequest,
    LensRequest,
    AutocorrectRequest,
    PatentsRequest,
    WebpageRequest
)

server = Server("Serper")
logger = logging.getLogger(__name__)

google_request_map = {
    SerperTools.GOOGLE_SEARCH: SearchRequest,
    SerperTools.GOOGLE_SEARCH_IMAGES: SearchRequest,
    SerperTools.GOOGLE_SEARCH_VIDEOS: SearchRequest,
    SerperTools.GOOGLE_SEARCH_PLACES: AutocorrectRequest,
    SerperTools.GOOGLE_SEARCH_MAPS: MapsRequest,
    SerperTools.GOOGLE_SEARCH_REVIEWS: ReviewsRequest,
    SerperTools.GOOGLE_SEARCH_NEWS: SearchRequest,
    SerperTools.GOOGLE_SEARCH_SHOPPING: ShoppingRequest,
    SerperTools.GOOGLE_SEARCH_LENS: LensRequest,
    SerperTools.GOOGLE_SEARCH_SCHOLAR: AutocorrectRequest,
    SerperTools.GOOGLE_SEARCH_PATENTS: PatentsRequest,
    SerperTools.GOOGLE_SEARCH_AUTOCOMPLETE: AutocorrectRequest,
}


@server.list_tools()
async def list_tools() -> List[Tool]:
    logger.debug("开始生成工具列表")
    tools = []

    for k, v in google_request_map.items():
        tools.append(
            Tool(
                name=k.value,
                description="Search Google for results",
                inputSchema=v.model_json_schema(),
            ),
        )

    tools.append(Tool(
        name=SerperTools.WEBPAGE_SCRAPE,
        description="Scrape webpage by url",
        inputSchema=WebpageRequest.model_json_schema(),
    ))

    logger.debug("工具列表生成完成，数量：%d", len(tools))
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    logger.debug("开始调用工具：%s", name)
    logger.debug("工具参数：%s", arguments)
    if not SERPER_API_KEY:
        logger.warning("SERPER_API_KEY 为空，拒绝处理请求")
        return [TextContent(text=f"SERPER_API_KEY is empty!", type="text")]

    try:
        if name == SerperTools.WEBPAGE_SCRAPE.value:
            logger.debug("识别为网页抓取工具")
            request = WebpageRequest(**arguments)
            result = await scape(request)
            logger.debug("网页抓取完成")
            return [TextContent(text=json.dumps(result, indent=2), type="text")]

        if not SerperTools.has_value(name):
            logger.warning("未找到对应工具：%s", name)
            raise ValueError(f"Tool {name} not found")

        tool = SerperTools(name)
        request = google_request_map[tool](**arguments)
        logger.debug("准备调用 Serper 搜索接口：%s", tool.value)
        result = await google(tool, request)
        logger.debug("Serper 搜索接口返回成功")
        return [TextContent(text=json.dumps(result, indent=2), type="text")]
    except Exception as e:
        logger.exception("工具调用失败：%s", name)
        return [TextContent(text=f"Error: {str(e)}", type="text")]


async def main():
    logger.info("Serper MCP 服务器启动")
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)

from typing import Any, List, Sequence
import json
import logging

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

load_dotenv()

from .core import google, scape, google_multi_region, SERPER_API_KEY
from .enums import SerperTools
from .schemas import (
    SearchRequest,
    MapsRequest,
    ReviewsRequest,
    ShoppingRequest,
    LensRequest,
    AutocorrectRequest,
    PatentsRequest,
    WebpageRequest,
    MultiRegionSearchRequest,
    AutoSearchRequest,
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

# 意图到工具的映射关系
INTENT_TO_TOOL_MAP = {
    "general": SerperTools.GOOGLE_SEARCH_MULTI_REGION,  # 强制使用多地区搜索
    "images": SerperTools.GOOGLE_SEARCH_IMAGES,
    "videos": SerperTools.GOOGLE_SEARCH_VIDEOS,
    "news": SerperTools.GOOGLE_SEARCH_MULTI_REGION,  # 强制使用多地区搜索
    "maps": SerperTools.GOOGLE_SEARCH_MAPS,
    "places": SerperTools.GOOGLE_SEARCH_PLACES,
    "shopping": SerperTools.GOOGLE_SEARCH_SHOPPING,
    "scholar": SerperTools.GOOGLE_SEARCH_SCHOLAR,
    "patents": SerperTools.GOOGLE_SEARCH_PATENTS,
    "reviews": SerperTools.GOOGLE_SEARCH_REVIEWS,
    "lens": SerperTools.GOOGLE_SEARCH_LENS,
    "autocomplete": SerperTools.GOOGLE_SEARCH_AUTOCOMPLETE,
    "multi_region": SerperTools.GOOGLE_SEARCH_MULTI_REGION,
}


@server.list_tools()
async def list_tools() -> List[Tool]:
    logger.debug("开始生成工具列表")
    tools = []

    # 只暴露 google_search_auto 工具，作为所有搜索功能的统一入口
    tools.append(Tool(
        name=SerperTools.GOOGLE_SEARCH_AUTO,
        description="Automatically route Google search queries to the appropriate search tool based on intent. Supports all search types including general, images, videos, news, maps, places, shopping, scholar, patents, reviews, lens, autocomplete, and multi-region searches.",
        inputSchema=AutoSearchRequest.model_json_schema(),
    ))

    # 保留网页抓取工具，因为它不是搜索功能
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
        if name == SerperTools.GOOGLE_SEARCH_AUTO.value:
            logger.debug("识别为自动路由搜索工具")
            auto_request = AutoSearchRequest(**arguments)

            # 根据意图映射到具体工具
            target_tool = INTENT_TO_TOOL_MAP.get(auto_request.intent)
            if not target_tool:
                logger.warning("未找到对应的意图工具：%s", auto_request.intent)
                raise ValueError(f"Intent {auto_request.intent} not supported")

            logger.debug("路由到工具：%s", target_tool.value)

            # 处理特殊工具的参数转换
            if target_tool == SerperTools.GOOGLE_SEARCH_MULTI_REGION:
                # 多地区搜索需要特殊处理
                # 为 general 和 news intent 使用中美双地区预设
                if auto_request.intent in ["general", "news"]:
                    preset = "us_cn_dual"
                else:
                    preset = "global"  # 其他情况使用全球预设

                multi_region_args = {
                    "q": auto_request.q,
                    "preset": preset,
                    "num": auto_request.num,
                    "translations": auto_request.translations,  # 现在是必需参数
                }
                if auto_request.tbs:
                    multi_region_args["tbs"] = auto_request.tbs

                request = MultiRegionSearchRequest(**multi_region_args)
                result = await google_multi_region(request)
                logger.debug("多地区搜索路由完成，使用预设：%s", preset)
                return [TextContent(text=json.dumps(result, indent=2), type="text")]

            # 构建目标工具的请求参数
            target_request_class = google_request_map[target_tool]
            target_args = {"q": auto_request.q}

            # 根据目标工具类型添加相应参数
            if hasattr(target_request_class.model_fields, 'gl') and auto_request.gl:
                target_args["gl"] = auto_request.gl
            if hasattr(target_request_class.model_fields, 'hl') and auto_request.hl:
                target_args["hl"] = auto_request.hl
            if hasattr(target_request_class.model_fields, 'location') and auto_request.location:
                target_args["location"] = auto_request.location
            if hasattr(target_request_class.model_fields, 'num') and auto_request.num:
                target_args["num"] = auto_request.num
            if hasattr(target_request_class.model_fields, 'page') and auto_request.page:
                target_args["page"] = auto_request.page
            if hasattr(target_request_class.model_fields, 'tbs') and auto_request.tbs:
                target_args["tbs"] = auto_request.tbs

            # 为 AutocorrectRequest 类型添加默认的 autocorrect 参数
            if target_request_class in [AutocorrectRequest]:
                target_args["autocorrect"] = "true"

            request = target_request_class(**target_args)
            logger.debug("准备调用路由后的 Serper 搜索接口：%s", target_tool.value)
            result = await google(target_tool, request)
            logger.debug("路由搜索接口返回成功")
            return [TextContent(text=json.dumps(result, indent=2), type="text")]

        if name == SerperTools.WEBPAGE_SCRAPE.value:
            logger.debug("识别为网页抓取工具")
            request = WebpageRequest(**arguments)
            result = await scape(request)
            logger.debug("网页抓取完成")
            return [TextContent(text=json.dumps(result, indent=2), type="text")]

        if name == SerperTools.GOOGLE_SEARCH_MULTI_REGION.value:
            logger.debug("识别为多地区搜索工具")
            request = MultiRegionSearchRequest(**arguments)
            result = await google_multi_region(request)
            logger.debug("多地区搜索完成")
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

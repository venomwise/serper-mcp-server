from typing import Optional
from pydantic import BaseModel, Field

from .enums import ReviewSortBy

# 多地区搜索预设配置
REGION_CONFIGS = {
    "asia": [
        {"gl": "cn", "hl": "zh-CN"},
        {"gl": "jp", "hl": "ja"},
        {"gl": "kr", "hl": "ko"},
        {"gl": "sg", "hl": "en"},
        {"gl": "in", "hl": "en"},
    ],
    "europe": [
        {"gl": "uk", "hl": "en"},
        {"gl": "de", "hl": "de"},
        {"gl": "fr", "hl": "fr"},
        {"gl": "it", "hl": "it"},
        {"gl": "es", "hl": "es"},
    ],
    "americas": [
        {"gl": "us", "hl": "en"},
        {"gl": "ca", "hl": "en"},
        {"gl": "br", "hl": "pt-BR"},
        {"gl": "mx", "hl": "es"},
        {"gl": "ar", "hl": "es"},
    ],
    "global": [
        {"gl": "us", "hl": "en"},
        {"gl": "cn", "hl": "zh-CN"},
        {"gl": "uk", "hl": "en"},
        {"gl": "de", "hl": "de"},
        {"gl": "jp", "hl": "ja"},
    ],
    "us_cn_dual": [  # 新增中美双地区预设
        {"gl": "us", "hl": "en"},
        {"gl": "cn", "hl": "zh-CN"},
    ],
}


class BaseRequest(BaseModel):
    q: str = Field(..., description="The query to search for")
    gl: Optional[str] = Field(
        None, description="The country to search in, e.g. us, uk, ca, au, etc."
    )
    location: Optional[str] = Field(
        None, description="The location to search in, e.g. San Francisco, CA, USA"
    )
    hl: Optional[str] = Field(
        None, description="The language to search in, e.g. en, es, fr, de, etc."
    )
    page: Optional[str] = Field(
        "1",
        pattern=r"^[1-9]\d*$",
        description="The page number to return, first page is 1 (integer value as string)",
    )


class SearchRequest(BaseRequest):
    tbs: Optional[str] = Field(
        None, description="The time period to search in, e.g. d, w, m, y"
    )
    num: str = Field(
        "10",
        pattern=r"^([1-9]|[1-9]\d|100)$",
        description="The number of results to return, max is 100 (integer value as string)",
    )


class AutocorrectRequest(BaseRequest):
    autocorrect: Optional[str] = Field(
        "true",
        pattern=r"^(true|false)$",
        description="Automatically correct (boolean value as string: 'true' or 'false')",
    )


class MapsRequest(BaseModel):
    q: str = Field(..., description="The query to search for")
    ll: Optional[str] = Field(None, description="The GPS position & zoom level")
    placeId: Optional[str] = Field(None, description="The place ID to search in")
    cid: Optional[str] = Field(None, description="The CID to search in")
    gl: Optional[str] = Field(
        None, description="The country to search in, e.g. us, uk, ca, au, etc."
    )
    hl: Optional[str] = Field(
        None, description="The language to search in, e.g. en, es, fr, de, etc."
    )
    page: Optional[str] = Field(
        "1",
        pattern=r"^[1-9]\d*$",
        description="The page number to return, first page is 1 (integer value as string)",
    )


class ReviewsRequest(BaseModel):
    fid: str = Field(..., description="The FID")
    cid: Optional[str] = Field(None, description="The CID to search in")
    placeId: Optional[str] = Field(None, description="The place ID to search in")
    sortBy: Optional[str] = Field(
        "mostRelevant",
        pattern=r"^(mostRelevant|newest|highestRating|lowestRating)$",
        description="The sort order to use (enum value as string: 'mostRelevant', 'newest', 'highestRating', 'lowestRating')",
    )
    topicId: Optional[str] = Field(None, description="The topic ID to search in")
    nextPageToken: Optional[str] = Field(None, description="The next page token to use")
    gl: Optional[str] = Field(
        None, description="The country to search in, e.g. us, uk, ca, au, etc."
    )
    hl: Optional[str] = Field(
        None, description="The language to search in, e.g. en, es, fr, de, etc."
    )


class ShoppingRequest(BaseRequest):
    autocorrect: Optional[str] = Field(
        "true",
        pattern=r"^(true|false)$",
        description="Automatically correct (boolean value as string: 'true' or 'false')",
    )
    num: str = Field(
        "10",
        pattern=r"^([1-9]|[1-9]\d|100)$",
        description="The number of results to return, max is 100 (integer value as string)",
    )


class LensRequest(BaseModel):
    url: str = Field(..., description="The url to search")
    gl: Optional[str] = Field(
        None, description="The country to search in, e.g. us, uk, ca, au, etc."
    )
    hl: Optional[str] = Field(
        None, description="The language to search in, e.g. en, es, fr, de, etc."
    )


class PatentsRequest(BaseModel):
    q: str = Field(..., description="The query to search for")
    num: str = Field(
        "10",
        pattern=r"^([1-9]|[1-9]\d|100)$",
        description="The number of results to return, max is 100 (integer value as string)",
    )
    page: Optional[str] = Field(
        "1",
        pattern=r"^[1-9]\d*$",
        description="The page number to return, first page is 1 (integer value as string)",
    )


class WebpageRequest(BaseModel):
    url: str = Field(..., description="The url to scrape")
    includeMarkdown: Optional[str] = Field(
        "false",
        pattern=r"^(true|false)$",
        description="Include markdown in the response (boolean value as string: 'true' or 'false')",
    )


class MultiRegionSearchRequest(BaseModel):
    q: str = Field(..., description="The query to search for (used as default for regions without translations)")
    preset: str = Field(
        ...,
        pattern=r"^(asia|europe|americas|global|us_cn_dual)$",
        description="Preset region group: asia, europe, americas, global, or us_cn_dual",
    )
    translations: dict[str, str] = Field(
        ...,
        description="Required translations mapping language code to translated query, e.g. {'zh-CN': '人工智能', 'ja': '人工知能'}",
    )
    num: str = Field(
        "10",
        pattern=r"^([1-9]|[1-9]\d|100)$",
        description="The number of results to return per region, max is 100 (integer value as string)",
    )
    tbs: Optional[str] = Field(
        None, description="The time period to search in, e.g. d, w, m, y"
    )


class AutoSearchRequest(BaseModel):
    q: str = Field(..., description="The query to search for")
    intent: str = Field(
        "general",
        pattern=r"^(general|images|videos|news|maps|places|shopping|scholar|patents|reviews|lens|autocomplete|multi_region)$",
        description="Search intent to determine which tool to route to. Options: general, images, videos, news, maps, places, shopping, scholar, patents, reviews, lens, autocomplete, multi_region",
    )
    gl: Optional[str] = Field(
        None, description="The country to search in, e.g. us, uk, ca, au, etc."
    )
    hl: Optional[str] = Field(
        None, description="The language to search in, e.g. en, es, fr, de, etc."
    )
    location: Optional[str] = Field(
        None, description="The location to search in, e.g. San Francisco, CA, USA"
    )
    num: str = Field(
        "10",
        pattern=r"^([1-9]|[1-9]\d|100)$",
        description="The number of results to return, max is 100 (integer value as string)",
    )
    page: Optional[str] = Field(
        "1",
        pattern=r"^[1-9]\d*$",
        description="The page number to return, first page is 1 (integer value as string)",
    )
    tbs: Optional[str] = Field(
        None, description="The time period to search in, e.g. d, w, m, y"
    )
    translations: dict[str, str] = Field(
        ...,
        description="Required translations mapping language code to translated query for multi-region searches, e.g. {'zh-CN': '7年Java高级开发工程师平均薪资', 'en': '7 years Java senior developer average salary', 'de': '7 Jahre Java Senior-Entwickler Durchschnittsgehalt', 'ja': '7年Javaシニア開発者平均給与'}",
    )

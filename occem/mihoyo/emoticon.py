import os

import aiohttp
from pydantic import BaseModel

from occem.constants import TEMP_PATH

from .helper import ImageInfo, download_img

all = ["refresh_emoticon", "get_emoticon_path"]


class EmoticonItem(BaseModel):
    id: int
    name: str
    icon: str
    """url: gif | png"""
    sort_order: int
    static_icon: str
    """url: png"""
    updated_at: int
    """时间戳"""
    is_available: bool
    status: str
    """"""
    keywords: list


class EmoticonPack(BaseModel):
    id: int
    name: str
    """表情包合集名"""
    icon: str
    sort_order: int
    num: int
    """合集中表情包数量"""
    status: str
    """draft, published, ..."""
    list: list[EmoticonItem]
    updated_at: int
    """时间戳"""
    is_available: bool


class EmoticonData(BaseModel):
    list: list[EmoticonPack]


EMOTICON_PATH = os.path.join(TEMP_PATH, "mihoyo", "emotcion")


def parse_emoticon_data(emoticon_data: EmoticonData):
    emoticon_list: dict[str, ImageInfo] = {}
    for pack in emoticon_data.list:
        if pack.status != "published":
            continue
        if not pack.is_available:
            continue

        for emoticon in pack.list:
            if not emoticon.is_available:
                continue

            if emoticon.static_icon:
                img_type = os.path.splitext(emoticon.static_icon)[1]

                path = os.path.join(EMOTICON_PATH, emoticon.name + img_type)
                emoticon_item: ImageInfo = {
                    "name": emoticon.name,
                    "type": img_type,
                    "url": emoticon.static_icon,
                    "path": path,
                }
            elif emoticon.icon:
                img_type = os.path.splitext(emoticon.icon)[1]

                path = os.path.join(EMOTICON_PATH, emoticon.name + img_type)
                emoticon_item: ImageInfo = {
                    "name": emoticon.name,
                    "type": img_type,
                    "url": emoticon.icon,
                    "path": path,
                }
            else:
                raise f"Unfount emoticon icon {emoticon.name}"
            emoticon_list[emoticon_item["name"]] = emoticon_item
    return emoticon_list


async def fetch_emoticon_list():
    """获取最新表情包列表"""
    async with aiohttp.ClientSession() as session:
        url = "https://bbs-api-static.miyoushe.com/misc/api/emoticon_set"
        params = {"gids": 2}
        async with session.get(url, params=params) as resp:
            data = await resp.json()

    return parse_emoticon_data(EmoticonData(**data["data"]))


async def refresh_emoticon():
    emoticon_list = await fetch_emoticon_list()
    if not os.path.exists(EMOTICON_PATH):
        os.makedirs(EMOTICON_PATH)
    async with aiohttp.ClientSession() as session:
        await download_img(session, emoticon_list)
    return emoticon_list

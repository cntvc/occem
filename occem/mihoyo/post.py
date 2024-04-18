import json
import os
import re
from base64 import b64encode

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel

from occem.constants import ROOT_PATH, TEMP_PATH

from .emoticon import refresh_emoticon
from .helper import ImageInfo, download_img, url_to_image_info

__all__ = ["fetch_post", "PostData"]

MIHOYO_PATH = os.path.join(TEMP_PATH, "mihoyo")

IMG_PATH = os.path.join(MIHOYO_PATH, "img")


class Collection(BaseModel):
    prev_post_id: int
    next_post_id: int
    collection_id: int
    cur: int
    total: int
    collection_title: str
    prev_post_game_id: int
    next_post_game_id: int
    prev_post_view_type: int
    next_post_view_type: int


class Post(BaseModel):
    game_id: int
    post_id: int
    f_forum_id: int
    uid: int
    subject: str
    content: str
    cover: str
    view_type: int
    created_at: int
    images: list[str]


class User(BaseModel):
    uid: int
    nickname: str
    introduce: str


class Image(BaseModel):
    url: str
    height: int
    width: int
    format: str
    size: int
    crop: object = None
    is_user_set_cover: bool
    image_id: int
    entity_type: str
    entity_id: int
    is_deleted: bool


class PostData(BaseModel):
    post: Post
    collection: Collection
    user: User


async def fetch_post(post_id: int):
    url = "https://bbs-api.miyoushe.com/post/wapi/getPostFull"
    async with aiohttp.ClientSession() as session:
        params = {"post_id": post_id}
        header = {
            "Referer": "https://www.miyoushe.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        async with session.get(url, headers=header, params=params) as resp:
            data = await resp.json()
            if data["retcode"] != 0:
                raise Exception(data["message"])
            data = data["data"]

            return PostData(**data["post"])


async def _handle_post_img(post_content: str):
    soup = BeautifulSoup(post_content, "html.parser")
    img_tags = soup.find_all("img")

    if not os.path.exists(IMG_PATH):
        os.makedirs(IMG_PATH)

    async with aiohttp.ClientSession() as session:
        img_list = {}
        for img_tag in img_tags:
            img_item = url_to_image_info(img_tag["src"], IMG_PATH)
            img_list[img_item["name"]] = img_item
        await download_img(session, img_list)

    for img_tag in img_tags:
        img_item = url_to_image_info(img_tag["src"], IMG_PATH)

        if not os.path.exists(img_item["path"]):
            await download_img(session, {img_item["name"]: img_item})
        with open(img_item["path"], "rb") as f:
            data = f.read()
        img_tag["src"] = f"data:image/png;base64,{b64encode(data).decode()}"

    return soup.prettify()


async def _handle_emoticon(post_content: str, emoticon_list: dict[str, ImageInfo]):
    def replace_emoticon(match: re.Match):
        name = match.group(0)
        name = name[2:-1]

        with open(emoticon_list[name]["path"], "rb") as f:
            data = f.read()

        return f""" <img src="data:image/png;base64,{b64encode(data).decode()}" alt="{name}"> """

    return re.subn(r"(_\(.*?\))", replace_emoticon, post_content)


async def save_post(post_id: int):
    post_data = await fetch_post(post_id)

    content = await _handle_post_img(post_data.post.content)
    emoticon_list = await refresh_emoticon()
    with open(os.path.join(MIHOYO_PATH, "emoticon.json"), "w") as f:
        f.write(json.dumps(emoticon_list, indent=4))
    content, count = await _handle_emoticon(content, emoticon_list)

    dir_path = os.path.join(ROOT_PATH, str(post_data.user.uid))
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    path = os.path.join(ROOT_PATH, str(post_data.user.uid), post_data.post.subject + ".html")
    # TODO 添加 css 样式以及其他信息，包括作者，时间、合集等
    with open(path, "w") as f:
        f.write(content)

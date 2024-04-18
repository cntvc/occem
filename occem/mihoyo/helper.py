import asyncio
import os
from typing import TypedDict

import aiohttp

__all__ = ["ImageInfo", "download_img", "url_to_image_info"]


class ImageInfo(TypedDict):
    name: str
    type: str
    path: str
    """本地文件路径"""
    url: str


def url_to_image_info(url: str, path: str) -> ImageInfo:
    name = os.path.basename(url)
    img_type = os.path.splitext(name)[1]
    path = os.path.join(path, name)

    img_item: ImageInfo = dict(name=name, type=img_type[1:], path=path, url=url)
    return img_item


async def download_img(session: aiohttp.ClientSession, img_list: dict[str, ImageInfo]):
    async def download_one(session: aiohttp.ClientSession, image: ImageInfo):
        if os.path.exists(image["path"]):
            return
        async with session.get(image["url"]) as resp:
            if resp.status != 200:
                raise f"Download image failed, {image}"

            data = await resp.read()
            with open(image["path"], "wb") as f:
                f.write(data)

    tasks = []
    for _, img in img_list.items():
        task = asyncio.create_task(download_one(session, img))
        tasks.append(task)
    await asyncio.gather(*tasks)

import logging

import dateparser

from catalog.common import *
from catalog.models import *

from .igdb import search_igdb_by_3p_url

_logger = logging.getLogger(__name__)


@SiteManager.register
class Steam(AbstractSite):
    SITE_NAME = SiteName.Steam
    ID_TYPE = IdType.Steam
    URL_PATTERNS = [r"\w+://store\.steampowered\.com/app/(\d+)"]
    WIKI_PROPERTY_ID = "?"
    DEFAULT_MODEL = Game

    @classmethod
    def id_to_url(cls, id_value):
        return "https://store.steampowered.com/app/" + str(id_value)

    def scrape(self):
        i = search_igdb_by_3p_url(self.url)
        pd = i.scrape() if i else ResourceContent()

        headers = BasicDownloader.headers.copy()
        headers["Host"] = "store.steampowered.com"
        headers["Cookie"] = "wants_mature_content=1; birthtime=754700401;"
        content = BasicDownloader(self.url, headers=headers).download().html()

        title = self.query_str(content, "//div[@class='apphub_AppName']/text()")
        developer = content.xpath("//div[@id='developers_list']/a/text()")
        publisher = content.xpath(
            "//div[@class='glance_ctn']//div[@class='dev_row'][2]//a/text()"
        )
        dts = self.query_str(
            content, "//div[@class='release_date']/div[@class='date']/text()"
        )
        dt = dateparser.parse(dts.replace(" ", "")) if dts else None
        release_date = dt.strftime("%Y-%m-%d") if dt else None

        genre = content.xpath(
            "//div[@class='details_block']/b[2]/following-sibling::a/text()"
        )
        platform = ["PC"]
        try:
            brief = self.query_str(
                content, "//div[@class='game_description_snippet']/text()"
            )
        except:
            brief = ""
        # try Steam images if no image from IGDB
        if pd.cover_image is None:
            pd.metadata["cover_image_url"] = self.query_str(
                content, "//img[@class='game_header_image_full']/@src"
            ).replace("header.jpg", "library_600x900.jpg")
            (
                pd.cover_image,
                pd.cover_image_extention,
            ) = BasicImageDownloader.download_image(
                pd.metadata["cover_image_url"], self.url
            )
        if pd.cover_image is None:
            pd.metadata["cover_image_url"] = self.query_str(
                content, "//img[@class='game_header_image_full']/@src"
            )
            (
                pd.cover_image,
                pd.cover_image_extention,
            ) = BasicImageDownloader.download_image(
                pd.metadata["cover_image_url"], self.url
            )
        # merge data from IGDB, use localized Steam data if available
        d = {
            "developer": developer,
            "publisher": publisher,
            "release_date": release_date,
            "genre": genre,
            "platform": platform,
        }
        d.update(pd.metadata)
        pd.metadata = d
        if title:
            pd.metadata["title"] = title
        if brief:
            pd.metadata["brief"] = brief
        return pd

from datetime import datetime

from requests import get
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag

from image_scraper.models import ImagesSource, Image
from image_scraper.scrapers.scraper import Scraper


class Bs4Scraper(Scraper):
    """Scans websites for images and returns data about them."""

    def get_images_data(self, image_source: ImagesSource) -> set[Image]:
        """The method that starts the synchronization process.

        Args:
            image_source: the ImagesSource object. Contains website data.

        Returns: set containing dicts with images data:
            - image source (image page),
            - url_address (src from image object),
            - title (alt from image object)."""
        html_dom = self._get_html_dom(image_source.current_url_address)
        return self.prepare_image_objects(
            image_source.domain, html_dom.select("." + image_source.container_class)
        )

    @staticmethod
    def _get_html_dom(url_address: str) -> BeautifulSoup:
        """Convert string containing URL address into Response object,
        and then convert it into BeautifulSoup object.

        Args:
            url_address: string containing URL of scraped website.

        Returns: BeautifulSoup object containing HTML DOM."""
        request = get(url_address)
        return BeautifulSoup(request.text, "html.parser")

    def prepare_image_objects(
        self, domain: str, image_holders: ResultSet
    ) -> set[Image]:
        """Iterates over ResultSet of image holders and add images into a set.

        Args:
            domain: string containing a domain of the scraped website.
            image_holders: ResultSet object containing the images' data.

        Returns: set containing the Image objects"""
        images = set()

        for div in image_holders:
            image = self._find_image_data(div, domain)
            if image:
                images.add(image)
        return images

    def _find_image_data(self, div: Tag, domain: str) -> Image | None:
        """Searches the Tag object for image-related data: source link, image source,
        and image description (alt).

        Args:
            div: Tag object containing a div with image.
            domain: string containing a domain of the scraped website.

        Returns: Image object based on the supplied div or None (if the required data
            cannot be found or the image source does not have the extension)."""
        image = div.find("img")
        try:
            image_source = self.add_domain_into_url_address(
                domain, div.find("a")["href"]
            )
            image_src = self.add_domain_into_url_address(domain, image["src"])
            if image_src[-4] == "." or image_src[-5] == ".":
                return Image(
                    source=image_source,
                    url_address=image_src,
                    title=image["alt"],
                    created_at=datetime.now(),
                )
            return None
        except TypeError:
            return None
        except KeyError:
            return None

    def find_next_page(
        self,
        current_url_address: str,
        domain: str,
        pagination_class: str,
        scraped_urls: set[str],
    ) -> tuple[str, set[str]]:
        """Search the HTML DOM for the next page URL address.

        Args:
            current_url_address: string containing URL address of the website to scan
            for the next page.
            domain: string containing domain and protocol of the website to scan for
                the next page.
            pagination_class: string containing class of div or section element
                containing pagination URLs.
            scraped_urls: to avoid duplicates, it is required to provide previously
                scanned URLs.

        Returns: tuple containing the next URL address, and set of scraped URLs."""
        scraped_urls.add(current_url_address)
        html_dom = self._get_html_dom(current_url_address)
        pagination_div = html_dom.select_one("." + pagination_class)

        next_url = self.add_domain_into_url_address(
            domain,
            pagination_div.find("a")["href"],
        )
        next_url_index = 0

        while not self._is_this_really_the_next_page(domain, next_url, scraped_urls):
            scraped_urls.add(next_url)
            next_url_index += 1
            if next_url_index > 5:
                raise IndexError("Couldn't find the URL of the next subpage.")
            next_url = self.add_domain_into_url_address(
                domain,
                pagination_div.find_all("a")[next_url_index]["href"],
            )

        return next_url, scraped_urls

    @staticmethod
    def add_domain_into_url_address(domain: str, item_url: str) -> str:
        """Adds domain if not present in URL address and deletes double slashes.

        Args:
            domain: string containing a domain of the scraped website.
            item_url: URL address there the domain may be missing.

        Returns: string containing correct URL address."""
        item_url = item_url.split("?")[0]
        if domain in item_url:
            return item_url
        elif "https://" in item_url or "http://" in item_url:
            return item_url
        item_url.replace("//", "/")
        if item_url[0] == "/":
            item_url = item_url[1:]
        return str(domain + item_url)

    @staticmethod
    def _is_this_really_the_next_page(
        domain: str, new_url: str, scraped_urls: set[str]
    ) -> bool:
        """Return True if new_url is a valid URL address and has not been scraped
            before.

        Args:
            domain: string containing a domain of the scraped website.
            new_url: string containing the URL address to check.
            scraped_urls: set of previously checked URL addresses."""
        if new_url in scraped_urls:
            return False
        elif new_url == domain + "#" or new_url == "#":
            return False
        else:
            try:
                return True if int(new_url[-1]) > 1 else False
            except ValueError:
                return False

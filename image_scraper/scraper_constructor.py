from image_scraper.src.core import ImageScraper
from image_scraper.src.scrapers.bs4_scraper import Bs4Scraper


SCRAPERS = {
    "bs4": Bs4Scraper(),
}


def create_image_scraper(
    website_url: str,
    container_class: str,
    pagination_class: str,
    pages_to_scan: int,
    scraper: str = "bs4",
) -> ImageScraper:
    """Constructor for the ImageScraper object. Imports scrapers and delivers them to
    ImageScraper based on the information in the scraper variable.

    Args:
        website_url: the URL address of website to scan.
        container_class: a class of div or section element containing image
        pagination_class: a class of div or section element containing pagination
            URLs.
        pages_to_scan: how many pages should be scraped.
        scraper: tool to be used.

    Returns: the ImageScraper object."""
    if scraper in SCRAPERS:
        return ImageScraper(
            website_url=website_url,
            container_class=container_class,
            pagination_class=pagination_class,
            pages_to_scan=pages_to_scan,
            scraper=SCRAPERS[scraper],
        )
    else:
        raise NameError("This tool is not supported.")

import csv
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://quotes.toscrape.com/"


@dataclass
class Quote:
    """
    A data class representing a quote.

    Attributes:
        text (str): The text of the quote.
        author (str): The author of the quote.
        tags (list[str]): A list of tags associated with the quote.
    """
    text: str
    author: str
    tags: list[str]


def parse_single_quote(quote_soup: BeautifulSoup, author_bios: dict) -> Quote:
    """
    Parses a single quote from the BeautifulSoup object and retrieves
    the author's biography.

    Args:
        quote_soup (BeautifulSoup): A BeautifulSoup object containing the
                                    quote HTML.
        author_bios (dict): A dictionary to cache author biographies.

    Returns:
        Quote: An instance of the Quote dataclass containing the quote's
               text, author, and tags.
    """
    text = quote_soup.select_one(".text").get_text()
    author = quote_soup.select_one(".author").get_text()
    tags = [tag.get_text() for tag in quote_soup.select(".tags .tag")]
    author_url = BASE_URL + quote_soup.select_one(".author + a")["href"]

    if author not in author_bios:
        author_bios[author] = get_author_bio(author_url)

    return Quote(text=text, author=author, tags=tags)


def get_single_page_quotes(
        page: BeautifulSoup,
        author_bios: dict
) -> list[Quote]:
    """
    Parses all quotes from a single page of quotes.

    Args:
        page (BeautifulSoup): A BeautifulSoup object containing the page
                              HTML.
        author_bios (dict): A dictionary to cache author biographies.

    Returns:
        list[Quote]: A list of Quote objects parsed from the page.
    """
    quotes = page.select(".quote")
    return [parse_single_quote(quote_soup, author_bios)
            for quote_soup in quotes]


def get_quotes() -> (list[Quote], dict):
    """
    Retrieves quotes from all pages of the website with pagination.

    The function iterates through the pages of the website until it
    encounters a page without quotes or a 404 error, indicating there
    are no more pages to retrieve.

    Returns:
        list[Quote]: A list of Quote objects parsed from all pages of
                     quotes.
        dict: A dictionary containing authors and their biographies.
    """
    all_quotes = []
    author_bios = {}
    page_number = 1

    while True:
        response = requests.get(f"{BASE_URL}page/{page_number}/")

        if response.status_code == 404:
            break

        page = BeautifulSoup(response.content, "html.parser")
        quotes_on_page = get_single_page_quotes(page, author_bios)

        if not quotes_on_page:
            break

        all_quotes.extend(quotes_on_page)
        page_number += 1

    return all_quotes, author_bios


def get_author_bio(author_url: str) -> str:
    """
    Retrieves the biography of an author from the author's page.

    Args:
        author_url (str): The URL of the author's page.

    Returns:
        str: The biography of the author.
    """
    response = requests.get(author_url)
    if response.status_code != 200:
        return "Biography not available."

    page = BeautifulSoup(response.content, "html.parser")
    bio = page.select_one(".author-details .author-description")
    return bio.get_text(strip=True) if bio else "Biography not available."


def write_quotes_to_csv(quotes: list[Quote], filename: str) -> None:
    """
    Writes the quotes to a CSV file.

    Args:
        quotes (list[Quote]): A list of Quote objects to be written to
                              the CSV.
        filename (str): The name of the CSV file to write the quotes to.
    """
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Text", "Author", "Tags"])
        for quote in quotes:
            writer.writerow([quote.text, quote.author, ", ".join(quote.tags)])


def write_authors_to_csv(author_bios: dict, filename: str) -> None:
    """
    Writes the authors' biographies to a CSV file.

    Args:
        author_bios (dict): A dictionary containing authors and their
                            biographies.
        filename (str): The name of the CSV file to write the authors'
                        biographies to.
    """
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Author", "Biography"])
        for author, bio in author_bios.items():
            writer.writerow([author, bio])


def main(quotes_csv_path: str, authors_csv_path: str) -> None:
    """
    Main function to get quotes and write them to CSV files.

    Args:
        quotes_csv_path (str): The path to the output quotes CSV file.
        authors_csv_path (str): The path to the output authors CSV file.
    """
    quotes, author_bios = get_quotes()
    write_quotes_to_csv(quotes, quotes_csv_path)
    write_authors_to_csv(author_bios, authors_csv_path)


if __name__ == "__main__":
    main("quotes.csv", "authors.csv")

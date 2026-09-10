"""
Web scraping commands for Veni AI.

/scrape - Scrape a web page
/pdf - Extract text from a PDF
"""

from typing import List, Optional

from rich.panel import Panel

from veni.commands.base import BaseCommand, console


class ScrapeCommand(BaseCommand):
    """Scrape a web page and extract content."""

    @property
    def name(self) -> str:
        return "/scrape"

    @property
    def description(self) -> str:
        return "Scrape a web page and extract its text content."

    @property
    def usage(self) -> str:
        return "/scrape <url>"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Usage: /scrape <url>")
            return None
        url = args[0]
        try:
            from veni.web_scraper import WebScraper

            scraper = WebScraper()
            result = scraper.scrape_page(url)
            if result:
                title = result.title or "Untitled"
                text = result.text[:2000] if result.text else "No text extracted."
                console.print(
                    Panel(
                        f"Title: {title}\nURL: {url}\n\n{text}",
                        title="Scraped Content",
                        border_style="cyan",
                    )
                )
            else:
                self.show_error(f"Failed to scrape: {url}")
        except Exception as e:
            self.show_error(f"Scrape error: {e}")
        return None


class PdfCommand(BaseCommand):
    """Extract text from a PDF URL."""

    @property
    def name(self) -> str:
        return "/pdf"

    @property
    def description(self) -> str:
        return "Extract text content from a PDF URL."

    @property
    def usage(self) -> str:
        return "/pdf <pdf_url>"

    def execute(self, args: List[str]) -> Optional[str]:
        if not args:
            self.show_error("Usage: /pdf <pdf_url>")
            return None
        url = args[0]
        try:
            from veni.web_scraper import WebScraper

            scraper = WebScraper()
            result = scraper.extract_pdf(url)
            if result:
                title = result.title or "Untitled PDF"
                text = result.text[:3000] if result.text else "No text extracted."
                console.print(
                    Panel(
                        f"Title: {title}\nURL: {url}\n\n{text}",
                        title="PDF Content",
                        border_style="magenta",
                    )
                )
            else:
                self.show_error(f"Failed to extract PDF: {url}")
        except Exception as e:
            self.show_error(f"PDF extraction error: {e}")
        return None

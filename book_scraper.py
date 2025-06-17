import click
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from readability import Document
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
import weasyprint
import time
import markdown

class BookScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_chapters(self, url):
        """Extract chapter links from a book's main page"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Common patterns for chapter links
            chapter_links = []
            
            # Try different selectors based on common book site patterns
            selectors = [
                'a[href*="chapter"]',
                'a[href*="ch-"]', 
                'a[href*="/ch/"]',
                '.chapter-link a',
                '.chapter a',
                '.toc a',
                '.table-of-contents a'
            ]
            
            for selector in selectors:
                links = soup.select(selector)
                if links:
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(url, href)
                            chapter_links.append(full_url)
                    break
            
            # Fallback: look for any links that might be chapters
            if not chapter_links:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href')
                    text = link.get_text().lower()
                    if any(word in text for word in ['chapter', 'ch.', 'part']) and href:
                        full_url = urljoin(url, href)
                        chapter_links.append(full_url)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_chapters = []
            for link in chapter_links:
                if link not in seen:
                    seen.add(link)
                    unique_chapters.append(link)
            
            return unique_chapters
            
        except Exception as e:
            click.echo(f"Error fetching chapters: {e}")
            return []
    
    def get_chapter_text(self, url):
        """Extract clean chapter content from a URL"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # First try with readability
            try:
                # Make sure we pass text content, not bytes
                doc = Document(response.text)
                clean_html = doc.summary()
            except Exception as readability_error:
                click.echo(f"Readability failed, using fallback method: {readability_error}")
                # Fallback: use BeautifulSoup to extract content
                clean_html = self._extract_content_fallback(response.text, url)
            
            # Convert to markdown while preserving formatting
            markdown_content = md(
                clean_html, 
                heading_style="ATX",
                bullets="-",
                strip=['script', 'style']
            )
            
            # Clean up the markdown
            markdown_content = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_content)
            markdown_content = markdown_content.strip()
            
            return markdown_content
            
        except Exception as e:
            click.echo(f"Error fetching chapter from {url}: {e}")
            return ""
    
    def _extract_content_fallback(self, html_content, url):
        """Fallback content extraction using BeautifulSoup"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()
        
        # Try common content selectors
        content_selectors = [
            '.entry-content',
            '.post-content', 
            '.chapter-content',
            '.content',
            'article',
            '.text-content',
            '[class*="content"]',
            'main',
            '.post',
            '.entry'
        ]
        
        content_element = None
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                # Find the one with the most text
                content_element = max(elements, key=lambda x: len(x.get_text()))
                break
        
        # If no specific content found, try to find the largest text block
        if not content_element:
            # Look for divs or paragraphs with substantial text
            all_elements = soup.find_all(['div', 'section', 'article'])
            if all_elements:
                content_element = max(all_elements, key=lambda x: len(x.get_text()))
        
        # Last resort: use body content
        if not content_element:
            content_element = soup.find('body') or soup
        
        # Clean up the selected content
        if content_element:
            # Remove navigation and menu elements within content
            for unwanted in content_element.find_all(['nav', 'menu', '.navigation', '.menu', '.sidebar']):
                unwanted.decompose()
            
            return str(content_element)
        
        return html_content
    
    def combine_to_pdf(self, chapters_dir, output_file):
        """Combine markdown chapters into a PDF"""
        chapters_path = Path(chapters_dir)
        
        if not chapters_path.exists():
            raise click.ClickException(f"Chapters directory '{chapters_dir}' not found")
        
        # Get all markdown files sorted by name
        md_files = sorted(chapters_path.glob("chapter-*.md"))
        
        if not md_files:
            raise click.ClickException(f"No chapter files found in '{chapters_dir}'")
        
        # Combine all markdown content
        combined_content = []
        
        for md_file in md_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                combined_content.append(content)
                combined_content.append("\n\n---\n\n")  # Page break separator
        
        full_markdown = '\n'.join(combined_content)
        
        # Convert markdown to HTML with styling
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @font-face {{
                    font-family: 'Arial';
                    src: url('fonts/Arial.ttf') format('truetype');
                    font-weight: normal;
                    font-style: normal;
                }}
                @font-face {{
                    font-family: 'Arial';
                    src: url('fonts/Arial-Italic.ttf') format('truetype');
                    font-weight: normal;
                    font-style: italic;
                }}
                @font-face {{
                    font-family: 'Arial';
                    src: url('fonts/Arial-Bold.ttf') format('truetype');
                    font-weight: bold;
                    font-style: normal;
                }}
                @font-face {{
                    font-family: 'Arial';
                    src: url('fonts/Arial-Bold-Italic.ttf') format('truetype');
                    font-weight: bold;
                    font-style: italic;
                }}
                body {{
                    font-family: 'Arial', sans-serif;
                    font-size: 12pt;
                    line-height: 1.5;
                    max-width: 800px;
                    margin: 40px auto;
                    padding: 0 40px;
                    color: #333;
                    text-align: justify;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #000;
                    margin-top: 2em;
                    margin-bottom: 1em;
                    text-align: center;
                    font-weight: bold;
                    font-family: 'Arial', sans-serif;
                }}
                h1 {{
                    font-size: 1.8em;
                    margin-bottom: 2em;
                    border-bottom: none;
                    padding-bottom: 0;
                }}
                p {{
                    margin-bottom: 0.8em;
                    text-indent: 1.5em;
                }}
                h1 + p, h2 + p, h3 + p {{
                    text-indent: 0;
                }}
                hr {{
                    page-break-before: always;
                    border: none;
                    height: 0;
                }}
                blockquote {{
                    border-left: 4px solid #bdc3c7;
                    margin: 1em 0;
                    padding-left: 1em;
                    font-style: italic;
                }}
                code {{
                    background-color: #f8f9fa;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
                pre {{
                    background-color: #f8f9fa;
                    padding: 1em;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
            </style>
        </head>
        <body>
        {self._markdown_to_html(full_markdown)}
        </body>
        </html>
        """
        
        # Generate PDF
        base_url = Path.cwd().as_uri() + '/'
        weasyprint.HTML(string=html_content, base_url=base_url).write_pdf(output_file)
        
    def _markdown_to_html(self, markdown_text):
        """Convert markdown to HTML"""
        md_processor = markdown.Markdown(extensions=['extra', 'codehilite'])
        return md_processor.convert(markdown_text)

@click.group()
def cli():
    """A CLI tool for scraping web books and converting them to various formats."""
    pass

@cli.command()
@click.argument('url')
@click.option('--output', '-o', default='chapters.txt', help='Output file for chapter links')
def get_chapters(url, output):
    """Extract chapter links from a book URL"""
    scraper = BookScraper()
    
    click.echo(f"Fetching chapters from: {url}")
    chapters = scraper.get_chapters(url)
    
    if not chapters:
        raise click.ClickException("No chapters found!")
    
    with open(output, 'w') as f:
        for chapter in chapters:
            f.write(f"{chapter}\n")
    
    click.echo(f"Found {len(chapters)} chapters, saved to {output}")

@cli.command()
@click.argument('chapters_file')
@click.option('--output-dir', '-d', default='chapters', help='Output directory for chapter files')
def get_chapter_text(chapters_file, output_dir):
    """Download chapter content from a list of URLs"""
    scraper = BookScraper()
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Read chapter URLs
    with open(chapters_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    click.echo(f"Downloading {len(urls)} chapters...")
    
    for i, url in enumerate(urls, 1):
        click.echo(f"Downloading chapter {i}/{len(urls)}: {url}")
        
        content = scraper.get_chapter_text(url)
        
        if content:
            chapter_file = output_path / f"chapter-{i:03d}.md"
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(f"# Chapter {i}\n\n")
                f.write(content)
            
            click.echo(f"  Saved to {chapter_file}")
        else:
            click.echo(f"  Failed to download chapter {i}")
        
        # Be nice to the server
        time.sleep(1)
    
    click.echo(f"Chapter download complete! Files saved in '{output_dir}'")

@cli.command()
@click.argument('chapters_dir')
@click.argument('output_file')
def combine_book(chapters_dir, output_file):
    """Combine chapter files into a PDF"""
    scraper = BookScraper()
    
    click.echo(f"Combining chapters from '{chapters_dir}' into '{output_file}'")
    
    try:
        scraper.combine_to_pdf(chapters_dir, output_file)
        click.echo(f"PDF created successfully: {output_file}")
    except Exception as e:
        raise click.ClickException(f"Failed to create PDF: {e}")

if __name__ == '__main__':
    cli() 
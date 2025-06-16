# Book Scraper & PDF Generator

A command-line tool to scrape web-based books, extract chapter content, and combine them into a beautifully formatted PDF.

## Features

- 🔍 **Smart Chapter Detection**: Automatically finds chapter links using multiple detection strategies
- 📖 **Clean Content Extraction**: Uses readability algorithms to extract main content without page clutter  
- 📄 **Professional PDF Generation**: Creates well-formatted PDFs with proper typography
- 🤖 **Rate Limited**: Respectful to servers with built-in delays
- 🛡️ **Error Handling**: Robust error handling for reliable operation

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

1. **Install uv** (if you haven't already):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

   Or create a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

## Usage

The tool provides three main commands that work in sequence:

### 1. Extract Chapter Links

```bash
python book_scraper.py get-chapters "https://example.com/book-url"
```

**Options:**
- `--output, -o`: Specify output file (default: `chapters.txt`)

**Example:**
```bash
python book_scraper.py get-chapters "https://example.com/my-book" --output my_book_chapters.txt
```

### 2. Download Chapter Content

```bash
python book_scraper.py get-chapter-text chapters.txt
```

**Options:**
- `--output-dir, -d`: Specify output directory (default: `chapters`)

**Example:**
```bash
python book_scraper.py get-chapter-text my_book_chapters.txt --output-dir my_book_content
```

### 3. Combine into PDF

```bash
python book_scraper.py combine-book chapters/ my_book.pdf
```

**Example:**
```bash
python book_scraper.py combine-book my_book_content final_book.pdf
```

## Complete Workflow Example

```bash
# 1. Extract chapter links
python book_scraper.py get-chapters "https://example.com/book"

# 2. Download all chapters  
python book_scraper.py get-chapter-text chapters.txt

# 3. Create final PDF
python book_scraper.py combine-book chapters my_complete_book.pdf
```

## How It Works

### Chapter Detection
The tool uses multiple strategies to find chapter links:
- CSS selectors for common patterns (`chapter`, `ch-`, `/ch/`)
- Common class names (`.chapter-link`, `.toc`, etc.)
- Fallback text-based detection for links containing "chapter", "ch.", or "part"

### Content Extraction
- Uses the `readability-lxml` library to extract main content
- Strips navigation, ads, and other page clutter
- Converts HTML to clean Markdown format
- Preserves formatting and structure

### PDF Generation
- Converts Markdown to styled HTML
- Uses professional typography (Georgia serif font)
- Includes proper spacing, headings, and page breaks
- Generates high-quality PDFs with `weasyprint`

## Dependencies

- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast XML/HTML parser  
- `markdownify` - HTML to Markdown conversion
- `readability-lxml` - Content extraction
- `weasyprint` - PDF generation
- `click` - Command-line interface
- `markdown` - Markdown processing

## Troubleshooting

### WeasyPrint Issues
If you encounter issues with WeasyPrint (PDF generation), you may need to install system dependencies:

**macOS:**
```bash
brew install pango libffi
```

**Ubuntu/Debian:**
```bash
sudo apt-get install build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

### Chapter Detection Issues
If the tool doesn't find chapters automatically:
1. Inspect the book's webpage HTML structure
2. Look for chapter link patterns
3. Modify the `selectors` list in `get_chapters()` method

### Content Extraction Issues  
If chapter content is not extracted properly:
1. Check if the site requires JavaScript (this tool works with static HTML)
2. The site might have anti-scraping measures
3. Try adjusting the readability extraction parameters

## Contributing

Feel free to submit issues or pull requests to improve chapter detection patterns or add new features!

## Legal Note

This tool is for personal use only. Please respect website terms of service and copyright laws. Only scrape content you have permission to access and use. 
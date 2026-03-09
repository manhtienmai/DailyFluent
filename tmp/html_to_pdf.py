"""Convert HTML worksheet to PDF using Playwright."""
import asyncio
from pathlib import Path

async def main():
    from playwright.async_api import async_playwright
    
    html_path = Path(__file__).parent / "vocab_worksheet.html"
    pdf_path = Path(__file__).parent / "Vocabulary_Worksheet_Traditional_Crafts.pdf"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"file:///{html_path.as_posix()}")
        await page.pdf(
            path=str(pdf_path),
            format="A4",
            margin={"top": "12mm", "bottom": "12mm", "left": "15mm", "right": "15mm"},
            print_background=True,
        )
        await browser.close()
    
    print(f"PDF saved to: {pdf_path}")

asyncio.run(main())

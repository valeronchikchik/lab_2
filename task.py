"""
Лабораторна робота: автоматизований збір даних з динамічної вебсторінки.

Обрана сторінка (контент підвантажується JavaScript-ом):
https://quotes.toscrape.com/js/

Інструмент: Playwright (sync API).
Результат: quotes.csv та quotes.json
"""

import csv
import json
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

START_URL = "https://quotes.toscrape.com/js/"
CSV_FILE = "quotes.csv"
JSON_FILE = "quotes.json"
TIMEOUT_MS = 10_000


def parse_quotes(page, page_number):
    """Зчитує всі цитати з поточної сторінки (після того, як JS їх відрендерив)."""
    rows = []
    for block in page.locator("div.quote").all():
        rows.append(
            {
                "page": page_number,
                "text": block.locator("span.text").inner_text(),
                "author": block.locator("small.author").inner_text(),
                "tags": ", ".join(block.locator("a.tag").all_inner_texts()),
            }
        )
    return rows


def scrape():
    all_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = START_URL
        page_number = 1

        while url:
            print(f"Сторінка {page_number}: {url}")
            page.goto(url)

            # Явне очікування: цитати з'являються лише після виконання JavaScript
            try:
                page.wait_for_selector("div.quote", timeout=TIMEOUT_MS)
            except PlaywrightTimeout:
                print("Елементи не з'явилися за відведений час, зупиняюсь.")
                break

            all_rows.extend(parse_quotes(page, page_number))

            # Пагінація: шукаємо посилання «Next»
            next_link = page.locator("li.next > a")
            if next_link.count() > 0:
                url = urljoin(url, next_link.get_attribute("href"))
                page_number += 1
            else:
                url = None

        browser.close()

    return all_rows


def save_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["page", "text", "author", "tags"])
        writer.writeheader()
        writer.writerows(rows)


def save_json(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    data = scrape()
    print(f"Зібрано записів: {len(data)}")
    save_csv(data, CSV_FILE)
    save_json(data, JSON_FILE)
    print(f"Збережено: {CSV_FILE}, {JSON_FILE}")
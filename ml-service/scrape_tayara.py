"""
Scraper: tayara.tn vehicles
Output: C:/Users/MSI/Desktop/deals-analyzer/ml-service/data/tayara.csv

HOW IT WORKS:
- Listing page: real URLs are /item/voitures/... — grabs all of them
- Detail page: content is mostly in the description text + h1 title + structured fields
- Pages 1 to MAX_PAGES
"""

import asyncio
import csv
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

OUTPUT_PATH = r"C:\Users\MSI\Desktop\deals-analyzer\ml-service\data\tayara.csv"
BASE_URL = "https://www.tayara.tn/listing/c/v%C3%A9hicules/?page={}"
MAX_PAGES = 40

FIELDNAMES = [
    "brand", "model", "year", "fuel", "mileage_km", "transmission",
    "fiscal_power", "engine_cc", "body_style", "car_condition", "trim_level",
    "seats", "doors", "condition", "price", "recorded_at",
    "seats_num", "doors_num", "engine_cc_num", "mileage_num",
    "car_age", "mileage_per_year", "depreciation_zone", "model_group",
    "title", "location", "listing_url"
]

KNOWN_BRANDS = [
    "renault", "peugeot", "volkswagen", "toyota", "hyundai", "kia",
    "mercedes", "mercedes-benz", "bmw", "audi", "ford", "fiat", "seat",
    "opel", "citroen", "citroën", "dacia", "nissan", "honda", "mazda",
    "suzuki", "skoda", "mitsubishi", "chevrolet", "land rover", "jeep",
    "volvo", "lexus", "subaru", "porsche", "mini", "alfa romeo", "lancia",
    "cupra", "haval", "chery", "mg", "geely", "byd", "infiniti",
]


def current_year():
    return datetime.now().year


def extract_int(text):
    if not text:
        return ""
    nums = re.findall(r"\d+", str(text).replace("\xa0", "").replace(" ", "").replace(",", ""))
    return nums[0] if nums else ""


def compute_derived(data):
    try:
        year = float(data.get("year", "") or 0)
        if year > 1990:
            age = current_year() - year
            data["car_age"] = str(int(age))
            mileage_str = data.get("mileage_num", "") or data.get("mileage_km", "")
            if mileage_str:
                mileage = float(re.sub(r"[^\d]", "", str(mileage_str)) or 0)
                data["mileage_num"] = str(int(mileage))
                if age > 0:
                    mpy = mileage / age
                    data["mileage_per_year"] = f"{mpy:.0f}"
                    data["depreciation_zone"] = (
                        "low" if mpy < 10000 else
                        "normal" if mpy < 20000 else
                        "high"
                    )
    except (ValueError, ZeroDivisionError):
        pass
    return data


def make_model_group(brand, model):
    parts = (str(brand) + " " + str(model)).lower().split()
    return " ".join(parts[:3])


def parse_brand_model(title):
    t = title.lower()
    for b in sorted(KNOWN_BRANDS, key=len, reverse=True):
        if b in t:
            brand = b.replace("-benz", "").strip()
            after = t.split(b, 1)[-1].strip(" -,:")
            model_words = [w for w in after.split()[:4] if len(w) > 1]
            model = " ".join(model_words[:3]).strip("- ,")
            return brand, model
    return "", ""


async def get_listing_urls(page, page_num):
    url = BASE_URL.format(page_num)
    print(f"  Loading: {url}")
    try:
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        # Wait for item links to appear
        await page.wait_for_selector("a[href*='/item/']", timeout=15000)
    except PlaywrightTimeout:
        print(f"  [warn] Timeout/no results on page {page_num}")
        return []

    all_links = await page.eval_on_selector_all(
        "a[href*='/item/']",
        "els => els.map(e => e.href)"
    )

    detail_links = []
    seen = set()
    for link in all_links:
        # Real item pages: /item/voitures/... (not images or media)
        if re.search(r"tayara\.tn/item/voitures/", link):
            clean = link.split("?")[0]
            if clean not in seen and not clean.endswith("/item/voitures/"):
                seen.add(clean)
                detail_links.append(clean)

    print(f"  Found {len(detail_links)} listings")
    return detail_links


async def scrape_detail(page, url):
    data = {f: "" for f in FIELDNAMES}
    data["listing_url"] = url
    data["recorded_at"] = datetime.now().strftime("%Y-%m")
    data["condition"] = "used"
    data["trim_level"] = "standard"

    # Extract location from URL: /item/voitures/GOVERNORATE/CITY/...
    url_parts = url.rstrip("/").split("/")
    if len(url_parts) >= 7:
        data["location"] = url_parts[5].replace("-", " ").title()

    try:
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        await page.wait_for_timeout(1500)
    except PlaywrightTimeout:
        print(f"    [warn] Timeout: {url}")
        return None

    try:
        body_text = await page.inner_text("body")
    except Exception:
        return None

    # ── Title ──
    try:
        h1 = await page.query_selector("h1")
        if h1:
            title = (await h1.text_content()).strip()
            # Clean emoji/symbols from title
            title = re.sub(r"[^\w\s\-\'\./]", "", title).strip()
            data["title"] = title
            brand, model = parse_brand_model(title)
            data["brand"] = brand
            data["model"] = model
            data["model_group"] = make_model_group(brand, model)
    except Exception:
        pass

    # ── Price — Tayara shows "XXXXDT" format ──
    price_match = re.search(r"([\d][\d\s\xa0]{2,8})\s*DT", body_text)
    if price_match:
        data["price"] = re.sub(r"[^\d]", "", price_match.group(1))

    # ── Parse everything from the description text ──
    body_lower = body_text.lower()

    # Year
    # Look for "année : 2022" or "2022" standalone
    year_match = re.search(r"ann[eé]e\s*[:\-]?\s*(20[01]\d|199\d)", body_lower)
    if year_match:
        data["year"] = year_match.group(1)
    else:
        # Find all 4-digit years and pick most frequent / first reasonable one
        years = re.findall(r"\b(199\d|200\d|201\d|202[0-5])\b", body_text)
        if years:
            from collections import Counter
            data["year"] = Counter(years).most_common(1)[0][0]

    # Mileage
    km_match = re.search(r"([\d][\d\s]{1,6})\s*(?:000\s*)?km", body_lower)
    if km_match:
        raw = re.sub(r"\s", "", km_match.group(0).replace("km", ""))
        # Handle "40 000 km" → 40000, "40 milles" handled below
        data["mileage_km"] = re.sub(r"[^\d]", "", raw)
        data["mileage_num"] = data["mileage_km"]

    # "milles" → multiply by 1000
    milles_match = re.search(r"(\d+)\s*milles?\b", body_lower)
    if milles_match and not data["mileage_km"]:
        data["mileage_km"] = str(int(milles_match.group(1)) * 1000)
        data["mileage_num"] = data["mileage_km"]

    # Fuel
    if "essence" in body_lower:       data["fuel"] = "gasoline"
    elif "diesel" in body_lower or "gasoil" in body_lower or "mazzout" in body_lower:
        data["fuel"] = "diesel"
    elif "électrique" in body_lower or "electrique" in body_lower:
        data["fuel"] = "electric"
    elif "hybride" in body_lower:     data["fuel"] = "hybrid"
    elif "gpl" in body_lower:         data["fuel"] = "gpl"

    # Transmission
    if "automatique" in body_lower:   data["transmission"] = "automatic"
    elif "manuelle" in body_lower or "manuel" in body_lower:
        data["transmission"] = "manual"

    # Fiscal power — "5 cv" or "5 chevaux"
    fp = re.search(r"(\d+)\s*(?:cv|chevaux)\b", body_lower)
    if fp:
        data["fiscal_power"] = f"{fp.group(1)}cv"

    # Engine CC
    cc_match = re.search(r"(\d[\d\s]*)\s*cm[³3]", body_lower)
    if cc_match:
        data["engine_cc"] = re.sub(r"\s", "", cc_match.group(1))
        data["engine_cc_num"] = data["engine_cc"]

    # Engine size in L (e.g. "1.6 L", "2.0L")
    if not data["engine_cc"]:
        l_match = re.search(r"(\d+[.,]\d+)\s*l\b", body_lower)
        if l_match:
            try:
                cc_approx = int(float(l_match.group(1).replace(",", ".")) * 1000)
                data["engine_cc"] = str(cc_approx)
                data["engine_cc_num"] = data["engine_cc"]
            except ValueError:
                pass

    # Condition
    if "neuf" in body_lower:
        data["car_condition"] = "new"
    elif "très bon" in body_lower:
        data["car_condition"] = "very good"
    elif "bon état" in body_lower or "bien entretenu" in body_lower:
        data["car_condition"] = "good"

    # Body style
    for style_fr, style_en in [
        ("citadine", "hatchback"), ("berline", "sedan"), ("suv", "suv"),
        ("break", "estate"), ("coupé", "coupe"), ("cabriolet", "convertible"),
        ("monospace", "minivan"), ("pick up", "pickup"), ("utilitaire", "utility"),
        ("compacte", "compact"),
    ]:
        if style_fr in body_lower:
            data["body_style"] = style_en
            break

    # Seats/doors from structured lines
    seats_match = re.search(r"(\d)\s*places?\b", body_lower)
    if seats_match:
        n = seats_match.group(1)
        data["seats_num"] = n
        data["seats"] = f"{n} seats"

    doors_match = re.search(r"(\d)\s*portes?\b", body_lower)
    if doors_match:
        n = doors_match.group(1)
        data["doors_num"] = n
        data["doors"] = f"{n} doors"

    data = compute_derived(data)
    return data


async def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    collected = []
    seen_urls = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            locale="fr-TN",
        )
        list_page = await context.new_page()
        detail_page = await context.new_page()

        consecutive_empty = 0

        for page_num in range(1, MAX_PAGES + 1):
            print(f"\n[Page {page_num}/{MAX_PAGES}] — {len(collected)} collected so far")
            urls = await get_listing_urls(list_page, page_num)

            if not urls:
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    print("  3 empty pages in a row — stopping early.")
                    break
                continue

            consecutive_empty = 0
            new_urls = [u for u in urls if u not in seen_urls]
            seen_urls.update(new_urls)

            if not new_urls:
                print("  No new URLs on this page")
                continue

            for url in new_urls:
                print(f"    [{len(collected)+1}] {url}")
                result = await scrape_detail(detail_page, url)
                if result:
                    collected.append(result)
                await asyncio.sleep(0.5)

            await asyncio.sleep(1.0)

        await browser.close()

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(collected)

    print(f"\n✅ Done — {len(collected)} cars saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
"""
Scraper: automobile.tn/fr/occasion
Output: C:/Users/MSI/Desktop/deals-analyzer/ml-service/data/automobile.csv

KEY FIXES vs previous versions:
- Correct URL pattern: /fr/occasion for page 1, /fr/occasion/2 for page 2, etc.
- Correct selector: a.occasions-item  (confirmed working from previous scraper)
- Single page object (no two-page setup that caused "context closed" error)
- Visits each detail page for full specs + Prix équitable
"""

import asyncio
import csv
import re
import os
import random
from datetime import datetime
from playwright.async_api import async_playwright

OUTPUT_PATH = r"C:\Users\MSI\Desktop\deals-analyzer\ml-service\data\automobile.csv"
BASE_URL = "https://www.automobile.tn/fr/occasion"
MAX_PAGES = 7      # 30 pages × ~20 cars = ~600 cars
TARGET_CARS = 90

FIELDNAMES = [
    "brand", "model", "year", "fuel", "mileage_km", "transmission",
    "fiscal_power", "engine_cc", "body_style", "car_condition", "trim_level",
    "seats", "doors", "condition", "price", "recorded_at",
    "seats_num", "doors_num", "engine_cc_num", "mileage_num",
    "car_age", "mileage_per_year", "depreciation_zone", "model_group",
    "price_rating", "color_ext", "color_int", "previous_owners",
    "listing_date", "governorate", "listing_url",
]


def current_year():
    return datetime.now().year

def clean_int(text):
    return re.sub(r"[^\d]", "", str(text or "")) or ""

def compute_derived(data):
    try:
        year = float(data.get("year") or 0)
        if year > 1990:
            age = current_year() - year
            data["car_age"] = str(int(age))
            km = clean_int(data.get("mileage_km") or data.get("mileage_num") or "")
            if km:
                data["mileage_num"] = km
                if age > 0:
                    mpy = float(km) / age
                    data["mileage_per_year"] = f"{mpy:.0f}"
                    data["depreciation_zone"] = (
                        "low" if mpy < 10000 else
                        "normal" if mpy < 20000 else "high"
                    )
    except (ValueError, ZeroDivisionError):
        pass
    return data

def make_model_group(brand, model):
    return " ".join((str(brand) + " " + str(model)).lower().split()[:3])

def parse_detail_text(body_text, url=""):
    data = {f: "" for f in FIELDNAMES}
    data["listing_url"] = url
    data["recorded_at"] = datetime.now().strftime("%Y-%m")
    data["condition"] = "used"
    data["trim_level"] = "standard"

    # brand/model from URL as initial fallback
    m = re.search(r"/fr/occasion/([^/]+)/([^/]+)/(\d+)", url)
    if m:
        data["brand"] = m.group(1).replace("-", " ").lower()
        data["model"] = m.group(2).replace("-", " ").lower()
        data["model_group"] = make_model_group(data["brand"], data["model"])

    # Price
    pm = re.search(r"Prix demandé\s*\n\s*([\d][\d\s\xa0]*)\s*DT", body_text)
    if not pm:
        pm = re.search(r"([\d][\d\s\xa0]{3,9})\s*DT", body_text)
    if pm:
        data["price"] = clean_int(pm.group(1))

    # Price rating
    for rating in ["Très bon prix", "Bon prix", "Prix équitable",
                   "Prix élevé", "Prix très élevé", "Aucune évaluation"]:
        if rating in body_text:
            data["price_rating"] = rating
            break

    # Parse label / value pairs
    lines = [l.strip() for l in body_text.split("\n") if l.strip()]
    i = 0
    while i < len(lines) - 1:
        raw = lines[i]
        label = raw.lower()
        val = lines[i + 1].strip()

        if not val or len(raw) > 55 or raw.startswith(("http", "[", "©")):
            i += 1
            continue

        hit = True
        if label == "kilométrage":
            data["mileage_km"] = clean_int(val)
            data["mileage_num"] = data["mileage_km"]
        elif "mise en circulation" in label:
            y = re.search(r"\b(19|20)\d{2}\b", val)
            data["year"] = y.group() if y else ""
        elif label == "énergie":
            v = val.lower()
            data["fuel"] = (
                "gasoline" if "essence" in v else
                "diesel"   if "diesel"  in v else
                "electric" if "électrique" in v else
                "hybrid"   if "hybride" in v else
                "gpl"      if "gpl" in v else v
            )
        elif "boite vitesse" in label or "boîte" in label:
            data["transmission"] = "automatic" if "automatique" in val.lower() else "manual"
        elif "puissance fiscale" in label:
            data["fiscal_power"] = val.strip()
        elif label == "carrosserie":
            data["body_style"] = val.lower().strip()
        elif "état général" in label:
            v = val.lower()
            data["car_condition"] = (
                "new"       if "neuf"     in v else
                "very good" if "très bon" in v else
                "good"      if "bon"      in v else v.strip()
            )
        elif "anciens propriétaires" in label:
            data["previous_owners"] = val.strip()
        elif "date de l'annonce" in label:
            data["listing_date"] = val.strip()
        elif "gouvernorat" in label:
            data["governorate"] = val.strip()
        elif label == "marque":
            data["brand"] = val.lower().strip()
        elif label == "modèle":
            data["model"] = val.lower().strip()
            data["model_group"] = make_model_group(data["brand"], data["model"])
        elif "couleur extérieure" in label:
            data["color_ext"] = val.strip()
        elif "couleur intérieure" in label:
            data["color_int"] = val.strip()
        elif "nombre de places" in label:
            n = clean_int(val)
            data["seats_num"] = n
            data["seats"] = f"{n} seats" if n else ""
        elif "nombre de portes" in label:
            n = clean_int(val)
            data["doors_num"] = n
            data["doors"] = f"{n} doors" if n else ""
        elif label == "cylindrée":
            cc = re.search(r"(\d+)", val)
            if cc:
                data["engine_cc"] = cc.group(1)
                data["engine_cc_num"] = cc.group(1)
        else:
            hit = False

        i += 2 if hit else 1

    return compute_derived(data)


def save(collected):
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(collected)


async def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    collected = []
    seen_urls = set()
    car_links = []  # <--- FIX 1: Initialize early to prevent UnboundLocalError

    async with async_playwright() as p:
        # FIX 2: Added stealth arguments to bypass bot detection
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        # Completely hide the 'webdriver' property
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = await context.new_page()

        print("=== STEP 1: Collecting listing URLs ===")
        
        for page_num in range(1, MAX_PAGES + 1):
            if len(car_links) >= TARGET_CARS:
                break
                
            url = BASE_URL if page_num == 1 else f"{BASE_URL}/{page_num}"
            print(f"[Listing page {page_num}] {url}")

            try:
                # FIX 3: Wait for a broader selector or just wait 5 seconds for safety
                await page.goto(url, wait_until="load", timeout=90000)
                await asyncio.sleep(5) # Give it time to bypass any "Checking browser" screen

                # Use a broader selector for the links
                links = await page.eval_on_selector_all(
                    "a[href*='/fr/occasion/']", 
                    "elements => elements.map(e => e.href)"
                )
                
                detail_links = [l.split("?")[0] for l in links if re.search(r'/\d+$', l)]
                
                if not detail_links:
                    print("  [warn] No links found on this page. Taking screenshot.")
                    await page.screenshot(path=f"debug_error_page_{page_num}.png")
                
                new_links = [l for l in detail_links if l not in seen_urls]
                seen_urls.update(new_links)
                car_links = list(seen_urls)

                print(f"  Found {len(new_links)} new links. Total: {len(car_links)}")

            except Exception as e:
                print(f"  [error] Skipping page {page_num} due to: {e}")
                continue

            await asyncio.sleep(random.uniform(2, 4))

        print(f"\nTotal unique car URLs gathered: {len(car_links)}")

        # ── STEP 2: Scrape each detail page ───────────────────────────────
        if not car_links:
            print("❌ No links to scrape. Exiting.")
            await browser.close()
            return

        print("\n=== STEP 2: Scraping detail pages ===")
        # ... (Rest of your detail scraping logic here)

        for index, link in enumerate(car_links):
            if len(collected) >= TARGET_CARS:
                break

            print(f"[{index+1}/{len(car_links)}] {link}")

            try:
                await page.goto(link, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(0.8, 1.8))
                raw_text = await page.inner_text("body")
                clean_text = "\n".join(
                    line.strip() for line in raw_text.split("\n") if line.strip()
                )
            except Exception as e:
                print(f"  [error] {e}")
                continue

            result = parse_detail_text(clean_text, link)
            if result:
                collected.append(result)

            # Checkpoint every 50
            if len(collected) % 50 == 0 and len(collected) > 0:
                save(collected)
                print(f"  💾 Checkpoint saved: {len(collected)} cars")

            await asyncio.sleep(random.uniform(0.5, 1.5))

        await browser.close()

    save(collected)
    print(f"\n✅ Done — {len(collected)} cars saved to:\n   {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
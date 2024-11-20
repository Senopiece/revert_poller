import argparse
import csv
from datetime import datetime
import os
from time import sleep
from playwright.sync_api import sync_playwright


def scrape(url, headless=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        page.goto(url)

        page.wait_for_selector("div.loading-text")
        page.wait_for_selector(
            "div.loading-text",
            state="detached",
        )

        # Turn on USD ref val everywhere
        position_list = page.locator("//div[contains(@class, 'postion-list')]")
        open_lp_positions_section = position_list.locator(
            "//div[contains(@class, 'flex flex-col gap-6') and descendant::h1[contains(@class, 'text-white text-lg md:text-xl font-bold leading-loose')]]"
        )
        position_ref_vals = open_lp_positions_section.locator(
            "//span[contains(text(),'ref val')]/following-sibling::span[contains(text(),'HOLD')]"
        )
        for _ in range(position_ref_vals.count()):
            position_ref_vals.nth(0).click()

            usd_selector = "//a[contains(@class, 'opt-item')]/div[@class='opt-title' and text()='USD']"
            page.wait_for_selector(usd_selector)
            usd_element = page.locator(usd_selector)
            usd_element.first.click()
            page.wait_for_selector(usd_selector, state="detached")

        # Scrap values
        pairs = {}
        open_lp_positions_containers = open_lp_positions_section.locator(
            "//div[contains(@class, 'flex w-full border rounded-lgg')]"
        )
        for i in range(open_lp_positions_containers.count()):
            container = open_lp_positions_containers.nth(i)

            pair = (
                container.locator(
                    "//span[contains(@class, 'group-visited:text-white')]"
                )
                .text_content()
                .replace("/", "-")
            )

            def value(key):
                return container.locator(
                    f"//div[contains(text(), '{key}')]/following-sibling::div"
                ).text_content()

            pairs[pair] = {
                "pooled_assets": float(value("pooled assets").replace("$", "")),
                "total_PnL": float(value("total PnL").replace("$", "")),
                "total_APR": float(value("total APR")[:-1]),
                "fee_APR": float(value("fee APR")[:-1]),
                "uncollected_fees": float(value("uncollected fees").replace("$", "")),
            }

        browser.close()

    return pairs


def ensure_dir_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_to_csv(filepath, data):
    file_exists = os.path.isfile(filepath)
    with open(filepath, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(
                [
                    "Time",
                    "Pooled Assets $",
                    "Total PnL $",
                    "Total APR %",
                    "Fee APR %",
                    "Uncollected Fees $",
                ]
            )  # Header
        writer.writerow(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render a webpage and save its content."
    )
    parser.add_argument(
        "--results_dir",
        type=str,
        default="charts",
        help="Where to store the result csvs.",
    )
    parser.add_argument(
        "--account",
        type=str,
        help="Account to look at",
    )
    parser.add_argument(
        "--poll_interval",
        type=float,
        required=True,
        help="Poll interval in minutes.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run the browser in non-headless mode for debugging.",
    )
    args = parser.parse_args()

    print("Script started")

    while True:
        print("Scraping...")
        pairs = scrape(
            f"https://revert.finance/#/account/{args.account}",
            headless=not args.debug,
        )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for pair, data in pairs.items():
            filepath = os.path.join(args.results_dir, f"{pair}.csv")
            ensure_dir_exists(args.results_dir)
            write_to_csv(filepath, [now, *data.values()])

        print(f"Scraped a new record at {now}")

        sleep(args.poll_interval * 60)

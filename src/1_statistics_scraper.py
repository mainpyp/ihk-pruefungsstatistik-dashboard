import re
from playwright.sync_api import Playwright, sync_playwright, expect
from playwright.sync_api import Page
import shutil
import tqdm
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/xls_data")
IHK_WEBSITE = "https://pes.ihk.de/"


def download_xls(page: Page, berufe_folder: str, name: str) -> None:
    """Download an Excel file from the page if available.

    Args:
        page: The Playwright page object.
        berufe_folder: The folder path to save the Excel file.
        name: The name to use for the saved Excel file.
    """
    # check if file already exists, if it does, return
    excel_file_path = os.path.join(berufe_folder, f"{name}.xls")
    if os.path.exists(excel_file_path):
        print(f"Excel file already exists: {excel_file_path}")
        return

    page.wait_for_timeout(1_000)

    # locate the download button (href contains "Excel")
    excel_download_locator = page.locator("a[href*='Excel']")
    if excel_download_locator.count() > 0:  # if something is found
        excel_download_locator.click()

        # store the download object in download_info
        with page.expect_download() as download_info:
            excel_download_locator.click()
        # get the download object
        download = download_info.value
        # save the file to the correct path
        download.save_as(excel_file_path)
        print(f"Excel file saved to: {excel_file_path}")
    else:
        print(f"No Excel download found for {name}")


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(IHK_WEBSITE)

    termine_locator = page.locator("select[name='termin']")
    # Get all the option values, 20234, 20232 -> 20094, 20092
    all_termine = termine_locator.locator("option").evaluate_all(
        "options => options.map(option => option.value)"
    )

    # termine = ["20234", "20232"]
    termine = ["20232"]
    assert set(termine).issubset(
        set(all_termine)
    ), "termine must be a subset of all_termine"

    # filter for termine
    print(f"Termine to iterate through: {termine}")
    # Iterate over all options and select them
    for option_termin in tqdm.tqdm(termine, desc="Termine"):

        termin_folder = os.path.join(DATA_PATH, option_termin)
        if not os.path.exists(termin_folder):
            print(f"Creating termin folder: {termin_folder}")
            os.makedirs(termin_folder)

        termine_locator.select_option(option_termin)
        page.wait_for_load_state("networkidle")

        berufe_locator = page.locator("select.berufe")
        berufe_options_locators = berufe_locator.locator("option").all()
        berufe_options_names = [
            option.text_content().strip() for option in berufe_options_locators
        ]
        berufe_options_ids = [
            option.get_attribute("value").strip() for option in berufe_options_locators
        ]

        # berufe tha Dastin is interested in
        selected_berufe = [
            # "Fachinformatiker/Fachinformatikerin Fachrichtung: Anwendungsentwicklung", # DONE
            # "Fachinformatiker/Fachinformatikerin Fachrichtung: Daten- und Prozessanalyse", # DONE
            # "Fachinformatiker/Fachinformatikerin Fachrichtung: Digitale Vernetzung", # DONE
            # "Fachinformatiker/Fachinformatikerin Fachrichtung: Systemintegration", # DONE
            # "Fachinformatiker/-in Fachrichtung: Anwendungsentwicklung", # Warum (hat nur 56 Teilnehmer)
            # "Fachinformatiker/-in Fachrichtung: Systemintegration", # Warum (hat nur 56 Teilnehmer)
            "Kaufmann / Kauffrau im E-Commerce", 
            # "Kaufmann / Kauffrau für Marketingkommunikation",
            # "Kaufmann / Kauffrau für Büromanagement",
            # "Kaufmann / Kauffrau für Dialogmarketing",
        ]

        interesting_berufe: list[tuple[str, str]] = [
            (beruf_name, beruf_id)
            for beruf_name, beruf_id in zip(berufe_options_names, berufe_options_ids)
            if beruf_name in selected_berufe
        ]

        print(f"Interesting Berufe: {interesting_berufe}")

        for beruf_name, beruf_id in tqdm.tqdm(interesting_berufe, desc="Berufe"):
            page.wait_for_load_state("networkidle")
            beruf_page = f"https://pes.ihk.de/Auswertung.cfm?Beruf={beruf_id}"

            berufe_folder = os.path.join(
                termin_folder,
                beruf_name.replace("/", "").replace(" ", "-").replace("--", "-"),
            )

            if not os.path.exists(berufe_folder):
                print(f"Creating Berufe Folder {berufe_folder}")
                os.makedirs(berufe_folder)

            # Store the current URL instead of the page object
            start_url = page.url

            page.goto(beruf_page)

            # the standorte are stored in select element with name pm1
            standorte_locator = page.locator("select[name='pm1']")
            standorte_locator.click()
            standorte_options = standorte_locator.locator("option").all()
            page.wait_for_load_state("networkidle")

            print(f"PM1 options count: {len(standorte_options)}")

            # str is the name of the standort
            standorte_names: list[str] = [
                option.text_content().strip() for option in standorte_options
            ]

            # Find the index of the delimiter "IHK-Standort" ("--------IHK-Standort--------")
            # because IHK Standorte are stored below this delimiter
            ihk_index = next(
                (
                    i
                    for i, standort_name in enumerate(standorte_names)
                    if "IHK-Standort" in standort_name
                ),
                None,
            )
            # Extract the IHK Standorte from the list of options, starting from the index after the delimiter
            ihk_standort_options = standorte_options[ihk_index + 1 :]
            ihk_standort_names = [
                option.text_content().strip() for option in ihk_standort_options
            ]

            # download excel for bundesweit before downloading for each standort
            download_xls(page, berufe_folder, "bundesweit")

            for standort_name in ihk_standort_names:
                standorte_locator.select_option(standort_name)
                page.wait_for_load_state("networkidle")
                download_xls(page, berufe_folder, standort_name)

            # Navigate back to the starting URL for the current Beruf
            try:
                page.goto(start_url)
                page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"Error navigating back: {e}")
                # If navigation fails, reload the start page
                page.reload()
                page.wait_for_load_state("networkidle")
                # Reselect the current termin
                termine_locator.select_option(option_termin)
                page.wait_for_load_state("networkidle")

            for _ in tqdm.tqdm(range(4), desc="Waiting for networkidle"):
                # halbe sekunde warten
                page.wait_for_timeout(500)

    browser.close()


with sync_playwright() as playwright:
    run(playwright)

import argparse
import os
import glob
import tqdm

from berufe import berufe_list
from playwright.sync_api import (
    Playwright,
    sync_playwright,
    Page,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--semesters",
        nargs="+",
        required=True,
        help="Semester(s) to consider. Format 20232, 20234 (2 for Summer, 4 for Winter)",
    )
    parser.add_argument(
        "--berufe",
        choices=["all", "custom"],
        required=True,
        help="Choose 'all' for all berufe or 'custom' to specify a custom list. The custom list can be edited in berufe.py",
    )
    return parser.parse_args()


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

    

    # locate the download button (href contains "Excel")
    print("Before locator")
    excel_download_locator = page.locator("a[href*='Excel']")
    print(f"After locator {excel_file_path}")
    excel_download_locator.count()
    print("excel_download_locator.count() is working")
    print(f"Download count: {excel_download_locator.count()}")
    if excel_download_locator.count() > 0:  # if something is found
        print("In count")
        excel_download_locator.click()
        print("After click")
        page.wait_for_timeout(1_000)
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


def run(playwright: Playwright, args: argparse.Namespace) -> None:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(IHK_WEBSITE)

    termine_locator = page.locator("select[name='termin']")
    # Get all the option values, 20234, 20232 -> 20094, 20092
    all_semester = termine_locator.locator("option").evaluate_all(
        "options => options.map(option => option.value)"
    )

    # termine = ["20234", "20232"]
    if args.semesters[0] == "all":
        semesters = all_semester
    else:
        semesters = args.semesters

    assert set(semesters).issubset(
        set(all_semester)
    ), f"termine must be a subset of all_termine. \nAvailable semesters: {all_semester}\nProvided semesters: {semesters}"

    # filter for termine
    print(f"Getting information for: {semesters}")
    # Save the current state
    current_state = {
        "url": page.url,
        "semester": termine_locator.evaluate("el => el.value"),
        "berufe": (
            berufe_locator.evaluate("el => el.value")
            if "berufe_locator" in locals()
            else None
        ),
    }

    # Function to restore the state
    def restore_state(page, state):
        page.goto(state["url"])
        page.wait_for_load_state("networkidle")
        termine_locator = page.locator("select[name='termin']")
        termine_locator.select_option(state["semester"])
        page.wait_for_load_state("networkidle")
        if state["berufe"]:
            berufe_locator = page.locator("select.berufe")
            berufe_locator.select_option(state["berufe"])
            page.wait_for_load_state("networkidle")

    # You can now use restore_state(page, current_state) to return to this point
    # Iterate over all options and select them
    for option_semester in tqdm.tqdm(semesters, desc="Termine"):

        termin_folder = os.path.join(DATA_PATH, option_semester)
        if not os.path.exists(termin_folder):
            print(f"Creating termin folder: {termin_folder}")
            os.makedirs(termin_folder)

        termine_locator.select_option(option_semester)
        page.wait_for_load_state("networkidle")

        berufe_locator = page.locator("select.berufe")
        berufe_options_locators = berufe_locator.locator("option").all()
        berufe_options_names = [
            option.text_content().strip() for option in berufe_options_locators
        ]
        berufe_options_ids = [
            option.get_attribute("value").strip() for option in berufe_options_locators
        ]

        if args.berufe == "all":
            selected_berufe = (
                berufe_options_names
                if input("Download all Berufe? (y/n)") == "y"
                else exit("Aborted. Start Again.")
            )
        else:
            selected_berufe = berufe_list

        # list of the names and the ids. Ids are used in the URL for the respective beruf
        name_id_berufe_list: list[tuple[str, str]] = [
            (beruf_name, beruf_id)
            for beruf_name, beruf_id in zip(berufe_options_names, berufe_options_ids)
            if beruf_name in selected_berufe
        ]

        print(f"Interesting Berufe: {name_id_berufe_list}")

        for beruf_name, beruf_id in tqdm.tqdm(name_id_berufe_list, desc="Berufe"):
            page.wait_for_load_state("networkidle")
            beruf_page = f"https://pes.ihk.de/Auswertung.cfm?Beruf={beruf_id}"

            # Create the folder for the Beruf
            berufe_folder = os.path.join(
                termin_folder,
                beruf_name.replace("/", "").replace(" ", "-").replace("--", "-"),
            )
            if not os.path.exists(berufe_folder):
                print(f"Creating Berufe Folder {berufe_folder}")
                os.makedirs(berufe_folder)

            # Store the current URL instead of the page object
            berufe_overview_url = page.url

            # Go to the Beruf Page
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
                existing_standorte_paths = glob.glob(berufe_folder + "/*")
                # get the Standort name from the file path (Berlin, Arnsberg, etc.)
                existing_standorte = [
                    standort_path.split("/")[-1].replace(".xls", "")
                    for standort_path in existing_standorte_paths
                ]

                if standort_name in existing_standorte:
                    print(f"Standort {standort_name} already in {berufe_folder}")
                    continue

                standorte_locator.select_option(standort_name)
                page.wait_for_load_state("networkidle")
                download_xls(page, berufe_folder, standort_name)

            # Navigate back to the starting URL for the current Beruf
            try:
                page.goto(berufe_overview_url)
                page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"Error navigating back: {e}")
                # If navigation fails, reload the start page
                page.reload()
                page.wait_for_load_state("networkidle")
                # Reselect the current termin
                termine_locator.select_option(option_semester)
                page.wait_for_load_state("networkidle")

            for _ in tqdm.tqdm(range(4), desc="Waiting for networkidle"):
                # halbe sekunde warten
                page.wait_for_timeout(500)

            restore_state(page, current_state)

    browser.close()


with sync_playwright() as playwright:
    args = parse_args()
    run(playwright, args)

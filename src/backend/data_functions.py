import glob
import os
import pandas as pd

CSV_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "csv_data")


def get_all_semesters() -> list[str]:
    """
    Get all semesters from the CSV_DATA_PATH.
    """
    all_semesters = glob.glob(os.path.join(CSV_DATA_PATH, "*"))
    return [os.path.basename(semester) for semester in all_semesters]


def get_berufe_for_semester(semester: str) -> pd.DataFrame:
    """
    Get the berufe data for a given semester.
    """
    all_berufe_folders = glob.glob(os.path.join(CSV_DATA_PATH, semester, "*"))
    berufe = [os.path.basename(folder) for folder in all_berufe_folders]

    return berufe


def get_dataframe(semester: str, beruf: str) -> pd.DataFrame:
    """
    Get the berufsstatistik data for a given semester and beruf.
    """
    return pd.read_csv(os.path.join(CSV_DATA_PATH, semester, beruf))


def get_berufsstatistik_data():

    return CSV_DATA_PATH

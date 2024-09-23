import pandas as pd
import glob
import os


def parse_dataframe(path: str) -> pd.DataFrame:
    df = pd.read_html(path)
    # Concatenate all dataframes in the list along the columns axis, using inner join to handle missing data
    parsed_df = pd.concat(df, axis=1, join='inner')
    # Set the column names to the values in the second row
    parsed_df.columns = parsed_df.iloc[1]
    # Drop the first two rows and remove the last column in one call
    parsed_df = parsed_df.iloc[2:, :-1]
    # Set the column names to the values in the first row
    parsed_df.columns = parsed_df.iloc[0]
    # Drop the first row as it's now redundant
    parsed_df = parsed_df.iloc[1:]
    # Prepend 'Index' to the column names to create a clear index column
    parsed_df.columns = ["Index"] + parsed_df.columns.tolist()[1:]
    # Set 'Index' as the index of the dataframe
    parsed_df.set_index("Index", inplace=True)
    # Transpose the dataframe to change the orientation of the data
    parsed_df = parsed_df.T
    # Rename a column to correct a typo in the name
    parsed_df.rename(columns={"ï¿½ Gesamtpunktzahl": "Gesamtpunktzahl"}, inplace=True)
    # Find the index of a specific column to use as a reference
    last_index = parsed_df.columns.get_loc("Note 6 in Prozent")
    # Extract column names after the reference column to use as modules
    modules = parsed_df.columns.tolist()[last_index + 1:]
    # Select only columns up to and including the reference column
    parsed_df = parsed_df.iloc[:, :last_index+1]
    # Add a new column 'modules' with the same list of modules for each row
    parsed_df["modules"] = [modules] * len(parsed_df)
    # Concatenate the new dataframe to the full dataframe, using 'Standort' as the index
    parsed_df["Standort"] = parsed_df.index
    return parsed_df


def run(path_to_all_semesters: str):
    # get all xls files in the xls_data folder
    # e.g. ../data/xls_data/20234/
    all_semesters = glob.glob(path_to_all_semesters + "*")

    # iterate over all semesters
    for semester in all_semesters:
        # get all berufe in the semester
        all_berufe = glob.glob(semester + "/*")
        
        for path_to_beruf in all_berufe:
            # dataframes for all standorte in the beruf
            full_df = pd.DataFrame()
            # get all xls files 
            all_standorte_xls = glob.glob(path_to_beruf + "/*.xls")
            
            # parse each standort xls file and concatenate to full dataframe
            for path in all_standorte_xls:
                parsed_df = parse_dataframe(path)
                full_df = pd.concat([full_df, parsed_df], ignore_index=True)

            # drop duplicates (bundesweit)
            full_df = full_df.drop_duplicates(subset=full_df.columns.difference(['modules']))

            # clean standort column so the names are uniform -> e.g. IHK zu/für Buxtehude will just be Buxtehude 
            full_df["Standort"] = full_df["Standort"].str.replace("IHK zu ", "").str.replace("IHK für ", "").str.replace("IHK", "").str.replace("  ", " ").str.strip()
                
            # set standort as index and sort by name
            full_df.set_index("Standort", inplace=True)
            full_df.sort_index(inplace=True)

            # fill na with 0 so it can be plotted
            full_df = full_df.fillna(0)
            
            # get year and beruf name from path
            year, beruf_name = path_to_beruf.split("/")[-2:]
            print(f"{year}/{beruf_name}")
            
            # create output folder
            output_folder = f"../data/csv_data/{year}/"
            if not os.path.exists(output_folder):
                print(f"Creating folder {output_folder}")
                os.makedirs(output_folder)

            output_path = f"{output_folder}/{beruf_name}.csv"
            full_df.to_csv(output_path)
            print(f"Saved to {output_path}")

if __name__ == "__main__":
    path_to_all_semesters = os.path.join(os.path.dirname(__file__), "../data/xls_data/")
    print(f"Converting all xls files in {path_to_all_semesters} to csv files in {path_to_all_semesters}/../csv_data/")
    run(path_to_all_semesters)
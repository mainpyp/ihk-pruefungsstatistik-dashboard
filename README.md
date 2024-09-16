# ihk-pruefungsstatistik-dashboard

This is a repository containing all the extracted data from the IHK Prüfungsstatistik Dashboard: <https://pes.ihk.de/Berufsauswahl.cfm>

> Under Construction

### This is the workflow

1. First download the xls files from the IHK website using the `statistics_scraper.py` script.
This creates a folder for each semester (20234, 20232, ...) (4 is winter, 2 is summer semester) and each folder contains one folder for each Beruf. Each Beruf folder contains a file for one IHK Standort.
2. Because the xls files are not valid html or xls, we need to fix them using the `fix_xls_files.py` script.
These files are now stored in the `html_data` folder and the folder structure is the same as in the `xls_data` folder.
3. Then we convert the html files to csv files using the `convert_html_to_csv.py` script.
These files are now stored in the `csv_data` folder and the folder structure is the same as in the `html_data` folder.
4. Now we have the data in a format that can be used to create the statistics. This is done with the `plot_statistics.ipynb` notebook.
Plots are stored in the `plots` folder.
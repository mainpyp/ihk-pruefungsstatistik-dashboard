""" The exported xls files from the IHK website are not valid html because a <html> and <body> tag is missing.
This script adds the missing tags to the files and saves them as html files.
"""

import glob
import os

# setup paths and get all xls files in the xls data folder
input_path = os.path.join(os.path.dirname(__file__), "../data/xls_data/")
all_files = glob.glob(input_path + "**/*.xls", recursive=True)
print(f"Found {len(all_files)} files")


for file in all_files:

    # load the file, replace invalid characters because (of course) they are not valid utf-8
    with open(file, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # setup output file path
    html_output_file = file.replace("xls", "html")
    output_dir = os.path.dirname(html_output_file)
    if not os.path.exists(output_dir):
        print(f"Creating directory {output_dir}")
        os.makedirs(output_dir)

    # write the content to the output file by adding <html><body> at the beginning
    with open(html_output_file, "w", encoding="utf-8") as f:
        f.write("<html><body>" + content)

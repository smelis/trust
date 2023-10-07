import json
import os


def combine_files_into_array(path):
    """
    Load all the PostAnalysis from each processed file in the directory into a single array.
    """
    all_post_analyses = []

    # Get all the processed files
    processed_files = get_processed_files()

    for file in processed_files:
        with open(file, 'r') as f:
            # Load data from file
            post_analysis_data = json.load(f)
            all_post_analyses.extend(post_analysis_data)

    # Save the combined data into a new JSON file
    with open(f'{path}/combined_post_analysis.json', 'w') as out_file:
        json.dump(all_post_analyses, out_file, indent=4)

    print(f"Combined data saved to combined_post_analysis.json")


def get_processed_files(path):
    if os.path.exists("processed_files.log"):
        with open("processed_files.log", "r") as log_file:
            return [os.path.join(path, line.strip()) for line in log_file.readlines()]
    return []


if __name__ == "__main__":
    combine_files_into_array(path='D:/data/tilburguniversity/inge/trust')

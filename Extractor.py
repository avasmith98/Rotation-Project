import os
import gzip
import shutil

# Define the source and destination paths
source_path = r"C:\Users\anmbh\OneDrive\Documents\PhD\Embedding_Project\Pubmed_2024_Baseline"
destination_path = r"C:\Users\anmbh\OneDrive\Documents\PhD\Embedding_Project\Extracted"

# Create the destination directory if it doesn't exist
os.makedirs(destination_path, exist_ok=True)

# Function to extract a .gz file
def extract_gz_file(source_file, destination_file):
    with gzip.open(source_file, 'rb') as f_in:
        with open(destination_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

# Loop through all files in the source directory
for i in range(1, 1220):
    file_name = f"pubmed24n{i:04d}.xml.gz"
    source_file_path = os.path.join(source_path, file_name)
    
    if os.path.exists(source_file_path):
        destination_file_name = f"pubmed24n{i:04d}.xml"
        destination_file_path = os.path.join(destination_path, destination_file_name)
        
        print(f"Extracting {file_name} to {destination_file_path}...")
        try:
            extract_gz_file(source_file_path, destination_file_path)
            print(f"Successfully extracted {file_name}.\n")
        except Exception as e:
            print(f"Error extracting {file_name}: {e}\n")
    else:
        print(f"File not found: {source_file_path}\n")

print("Extraction process completed.")

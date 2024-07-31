import hashlib
import os

# Define the base path and filename pattern
base_path = r"C:\Users\anmbh\OneDrive\Documents\PhD\Embedding_Project\Pubmed_2024_Baseline"
file_pattern = "pubmed24n{:04d}.xml.gz"
md5_file_pattern = "pubmed24n{:04d}.xml.gz.md5"

# Function to calculate MD5 checksum
def calculate_md5(file_path, chunk_size=4096):
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error calculating MD5 for {file_path}: {e}")
        return None

# List to keep track of corrupted files
corrupted_files = []

# Loop through all files
for i in range(1, 1220):
    file_name = file_pattern.format(i)
    md5_file_name = md5_file_pattern.format(i)
    
    file_path = os.path.join(base_path, file_name)
    md5_file_path = os.path.join(base_path, md5_file_name)
    
    # Read the expected MD5 checksum from the .md5 file
    if os.path.exists(md5_file_path):
        try:
            with open(md5_file_path, 'r') as md5_file:
                md5_contents = md5_file.read().strip()
                expected_md5 = md5_contents.split('=')[1].strip() if '=' in md5_contents else md5_contents.split()[0].strip()
        except Exception as e:
            print(f"Error reading MD5 file {md5_file_path}: {e}")
            continue
    else:
        print(f"MD5 file not found: {md5_file_path}")
        continue
    
    # Calculate the MD5 checksum of the downloaded file
    if os.path.exists(file_path):
        calculated_md5 = calculate_md5(file_path)
        if calculated_md5 is None:
            continue
    else:
        print(f"File not found: {file_path}")
        continue
    
    # Print the checksum comparison for each file
    print(f"File: {file_name}")
    print(f"Expected MD5: {expected_md5}")
    print(f"Calculated MD5: {calculated_md5}")
    
    # Compare the checksums and log if they don't match
    if calculated_md5 != expected_md5:
        print(f"The file {file_name} is corrupted. Checksums do not match.\n")
        corrupted_files.append(file_name)
    else:
        print("The file is valid. Checksums match.\n")

# Print summary of corrupted files
if corrupted_files:
    print("Summary of corrupted files:")
    for file in corrupted_files:
        print(f"- {file}")
else:
    print("All files are valid. Checksums match.")

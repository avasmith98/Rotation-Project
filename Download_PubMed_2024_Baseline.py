import ftplib
import os

def download_files_from_ftp(ftp_url, ftp_dir, local_dir):
    ftp = ftplib.FTP(ftp_url)
    ftp.login()

    ftp.cwd(ftp_dir)
    filenames = ftp.nlst()  # List of files in the directory

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    for filename in filenames:
        local_filepath = os.path.join(local_dir, filename)
        if os.path.exists(local_filepath):
            print(f"Already exists, skipping: {filename}")
            continue

        with open(local_filepath, 'wb') as file:
            try:
                ftp.retrbinary(f"RETR {filename}", file.write)
                print(f"Downloaded: {filename}")
            except ftplib.error_perm as e:
                print(f"Failed to download {filename}: {e}")
                os.remove(local_filepath)

    ftp.quit()
    print("All files downloaded.")

# FTP details
ftp_url = "ftp.ncbi.nlm.nih.gov"
ftp_dir = "/pubmed/baseline/"
local_dir = r"C:\Users\anmbh\OneDrive\Documents\PhD\Embedding_Project\Pubmed_2024_Baseline"

# Start download
download_files_from_ftp(ftp_url, ftp_dir, local_dir)

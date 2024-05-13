#Automating the Variant Analysis Workflow: Adapted from "How to find information for a variant updated Spring 2024"

import datetime
import requests
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
from urllib.parse import quote

# Constants
gene_symbol = "EGFR"
hgvs_cdna_transcript_id = "NM_005228.3:c.2648T>C"
hgvs_cdna_transcript_id_truncated = "NM_005228"

def print_header(gene_symbol = gene_symbol):
    print(f"Variant Analysis Report: {gene_symbol}")
    print(f"Report generated on {datetime.date.today().strftime("%B %d, %Y")}") 

def send_request(url, headers=None, params=None):
    """Helper function to send HTTP requests and handle errors."""
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"Failed to retrieve data from {url}: {e}")
        return None

def get_cytogenetic_band(gene_symbol = gene_symbol):
    """Retrieves the cytogenetic band location for the gene."""
    search_url = f'https://api.genome.ucsc.edu/search?search={gene_symbol}&genome=hg38'
    search_response = requests.get(search_url)
    search_data = search_response.json()

    try:
        for match in search_data['positionMatches'][0]['matches']:
            if gene_symbol in match['posName'] and 'ENST' in match['hgFindMatches']:
                position = match['position']
                chrom, pos_range = position.split(':')
                start, end = pos_range.split('-')

                track_url = f'https://api.genome.ucsc.edu/getData/track?track=cytoBand;genome=hg38;chrom={chrom};start={start};end={end}'
                track_response = requests.get(track_url)
                track_data = track_response.json()

                cytogenetic_band = track_data.get('cytoBand', 'Band not found')
                chromosome = cytogenetic_band[0]['chrom'][3:]  
                cytoband = cytogenetic_band[0]['name']        
                cytogenetic_band = chromosome + cytoband            
                print(f"Cytogenetic band: {cytogenetic_band}")
                break

    except (IndexError, KeyError) as e:
        print(f"Error handling API response: {e}")
        return "Gene symbol not found or data incomplete."

def get_ensembl_gene_id(gene_symbol = gene_symbol):
    """Retrieve Ensembl ID using gene symbol from Ensembl API."""
    url = f"https://rest.ensembl.org/lookup/symbol/homo_sapiens/{gene_symbol}"
    headers = {"Content-Type": "application/json"}
    response = send_request(url, headers)
    if response:
        ensembl_gene_id = response.json().get("id")
        return ensembl_gene_id
    return None

def get_high_protein_expression(ensembl_gene_id):
    """Extract tissues with high protein levels from the Human Protein Atlas."""
    url = f"https://www.proteinatlas.org/{ensembl_gene_id}.xml"
    response = send_request(url)
    high_protein_expression = []
    if response:
        root = ET.fromstring(response.content)
        for data in root.findall(".//data"):
            tissue = data.find('tissue')
            levels = data.findall('level[@type="expression"]')
            if tissue is not None and any(level.text.strip().lower() == "high" for level in levels):
                high_protein_expression.append(tissue.text)
                high_protein_expression_string = ', '.join(high_protein_expression)
    print("High protein expression:", high_protein_expression_string.lower())

def get_ensembl_transcript_id(hgvs_cdna_transcript_id_truncated = hgvs_cdna_transcript_id_truncated):
    """Retrieve Ensembl transcript ID using RefSeq transcript ID."""
    url = f"https://rest.ensembl.org/xrefs/symbol/homo_sapiens/{hgvs_cdna_transcript_id_truncated}?external_db=RefSeq_mRNA"
    headers = {"Content-Type": "application/json"}
    response = send_request(url, headers)
    if response:
        data = response.json()
        for entry in data:
            if entry['type'] == 'transcript':
                return entry['id']
    return None

def get_grch38_variant_position(hgvs_cdna_transcript_id = hgvs_cdna_transcript_id):
    """Fetch chromosome information from NCBI for a given RefSeq variant transcript ID."""
    encoded_identifier = hgvs_cdna_transcript_id.replace(':', '%3A').replace('>', '%3E')
    url = f"https://www.ncbi.nlm.nih.gov/snp/?term={encoded_identifier}"
    response = send_request(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        dt_tags = soup.find_all('dt')
        for dt in dt_tags:
            if dt.text.strip() == "Chromosome:":
                dd_tag = dt.find_next('dd')
                entries = dd_tag.decode_contents().split('<br/>')
                for entry in entries:
                    if "GRCh38" in entry:
                        entry_clean = BeautifulSoup(entry, 'html.parser').text.strip()
                        parts = entry_clean.split('\n')
                        if len(parts) > 1 and "GRCh38" in parts[1]:
                            variant_position = parts[0].split(':')[1]
                            return int(variant_position)
    return "GRCh38 chromosome information not found"

def get_transcript_details_and_ensembl_protein_id(ensembl_transcript_id, variant_position):
    """Retrieve detailed information for a given Ensembl transcript ID."""
    url = f"https://rest.ensembl.org/lookup/id/{ensembl_transcript_id}?expand=1"
    headers = {"Content-Type": "application/json"}
    response = send_request(url, headers)
    if response:
        data = response.json()
        transcript_length = data.get('length', 'Transcript Length not available')
        translation = data.get('Translation', {})
        translation_length = translation.get('length', 'Translation length not available')
        total_exons = len(data['Exon']) if 'Exon' in data else 0
        coding_exons = sum(1 for exon in data['Exon'] if exon['start'] <= translation.get('end', 0) and exon['end'] >= translation.get('start', float('inf')))
        exon_number = next((index for index, exon in enumerate(data.get('Exon', []), start=1) if exon['start'] <= variant_position <= exon['end']), None)
        ensembl_protein_id = data['Translation']['id']
        print(f"Transcript length: {transcript_length}")
        print(f"Translation length: {translation_length}")
        print(f"Total number of exons: {total_exons}")
        print(f"Number of coding exons: {coding_exons}")
        print(f"Variant location: exon {exon_number} of {coding_exons}")
        return ensembl_protein_id
    else:
        print("Failed to retrieve transcript details.")

def get_protein_domains(ensembl_protein_id):
    """Get protein domains for a given Ensembl protein ID."""
    url = f"https://rest.ensembl.org/overlap/translation/{ensembl_protein_id}"
    headers = {"Content-Type": "application/json"}
    response = send_request(url, headers)
    if response:
        domains = response.json()
        print("Protein Domain(s):")
        for domain in domains:
            if domain.get('type') in ['Pfam', 'Smart']:
                print(f"Source: {domain['type']}, Description: {domain.get('description', 'No description available')}, Start: {domain['start']}, End: {domain['end']}")
    else:
        print("Failed to retrieve protein domains.")

def get_rsID(hgvs_cdna_transcript_id = hgvs_cdna_transcript_id):
    """Get rsID from NCBI for a given RefSeq variant transcript ID."""
    url = "https://www.ncbi.nlm.nih.gov/snp/"
    params = {'term': hgvs_cdna_transcript_id}
    response = send_request(url, params=params)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        rsid_link = soup.find('a', href=lambda href: href and '/snp/rs' in href)
        if rsid_link:
            rsID = rsid_link.text.strip()
            return rsID
    return "rsID not found"

def get_clinvar_data(rsID):
    """Extract data from ClinVar for a given rsID."""
    url = f"https://www.ncbi.nlm.nih.gov/clinvar/?term={rsID}"
    response = send_request(url)
    extracted_data = []
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        correct_table = tables[4]  # Table 4 has the submissions germline data
        rows = correct_table.find_all('tr')
        extracted_data = []
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 5:  
                classification_info = cells[0].text.strip()
                condition_info = cells[2].text.strip()
                more_info = cells[4].text.strip()
                if "(more)" in more_info:
                    more_info_parts = more_info.split("(more)")
                    if len(more_info_parts) > 1:
                        more_info = more_info_parts[1].strip()
                if "(less)" in more_info:
                        more_info = more_info.replace("(less)", "").strip()
                extracted_data.append({
                    'Variant classification': classification_info,
                    'Variant condition': condition_info,
                    'Variant more info': more_info
                })
        
    if extracted_data:
        for data in extracted_data:
            for key, value in data.items():
                value = ' '.join(value.split())
                print(f"{key}: {value}")
    else:
        print("No data extracted from the rows.")

# Run Program
print_header()
cytogenetic_band = get_cytogenetic_band()
ensembl_gene_id = get_ensembl_gene_id()
get_high_protein_expression(ensembl_gene_id)
ensembl_transcript_id = get_ensembl_transcript_id()
variant_position = get_grch38_variant_position()
ensembl_protein_id = get_transcript_details_and_ensembl_protein_id(ensembl_transcript_id, variant_position)
get_protein_domains(ensembl_protein_id)
rsID = get_rsID()
get_clinvar_data(rsID)

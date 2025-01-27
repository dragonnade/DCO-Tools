from bs4 import BeautifulSoup
import pandas as pd
from urls import extract_iframe_url, get_archived_content, process_urls_from_csv
import re
import requests
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Dictionary to store project name to reference mappings during script execution
# This will store entries like: {'Project Name': {'reference': 'REF123', 'project_id': 'uuid'}}
project_mappings = {}

def get_project_info(soup):
    """
    Extract project name and applicant from the HTML.
    The project name from h1 will be used as a key for our mappings.
    """
    h1_tags = soup.find_all('h1')
    project_name = h1_tags[1].text.strip() if len(h1_tags) > 1 else ''
    applicant = soup.find('em').text.replace('by', '').strip()
    return project_name, applicant

def parse_document_entry(doc_div):
    """
    Parse a document entry div and extract all relevant information including the URL.
    """
    # Existing size extraction
    size_div = doc_div.find('div', string=re.compile('Size:'))
    filesize = size_div.find('strong').text.strip() if size_div else ''
    
    right_div = doc_div.find('div', class_='right')
    if not right_div:
        return None
    
    # Get document URL from the first anchor tag in right_div
    title_link = right_div.find('a')
    publishing_organization = title_link.text.strip() if title_link else ''
    # Extract the document URL - this is the new part
    document_url = title_link.get('href') if title_link else ''
    
    desc_div = right_div.find('div', class_=None)
    description = desc_div.text.strip() if desc_div else ''
    
    metadata_div = right_div.find('div', class_='document-metadata')
    if metadata_div:
        stage_info = metadata_div.find('div').text.strip()
        parts = stage_info.split(' > ')
        
        stage = parts[0]
        category = parts[-1]
        subcategory = ' > '.join(parts[1:-1]) if len(parts) > 2 else ''
        
        pub_date = metadata_div.find_all('div')[1].text.replace('Published:', '').strip()
    else:
        stage, category, subcategory, pub_date = '', '', '', ''

    return {
        'filesize': filesize,
        'publishing_organization': publishing_organization,
        'title': description or publishing_organization,
        'stage': stage,
        'subcategory': subcategory,
        'category': category,
        'publication_date': pub_date,
        'document_url': document_url  # Add the URL to the returned dictionary
    }

def save_to_supabase(documents):
    """
    Save documents to Supabase database.
    """
    for doc in documents:
        project_id = get_project_id(doc['project_name'])
        if not project_id:
            # Check our in-memory mapping first
            if doc['project_name'] in project_mappings:
                stored_reference = project_mappings[doc['project_name']]
                project_id = get_project_id(stored_reference)
            else:
                project_id = prompt_for_project_reference(doc['project_name'])
                if not project_id:
                    continue
        
        # Prepare document data for insertion
        doc_data = {
            'project_id': project_id,
            'publishing_organization': doc['publishing_organization'],
            'title': doc['title'],
            'filesize': doc['filesize'],
            'stage': doc['stage'],
            'subcategory': doc['subcategory'],
            'category': doc['category'],
            'publication_date': parse_date(doc['publication_date']),
            'applicant': doc['applicant'],
            'document_url': doc['document_url']  # Add URL to the database insert
        }
        
        try:
            supabase.table('old_documents').insert(doc_data).execute()
            print(f"Saved document: {doc['title']}")
        except Exception as e:
            print(f"Error saving document: {e}")

# def parse_document_entry(doc_div):
#     # Existing parsing logic remains the same
#     size_div = doc_div.find('div', string=re.compile('Size:'))
#     filesize = size_div.find('strong').text.strip() if size_div else ''
    
#     right_div = doc_div.find('div', class_='right')
#     if not right_div:
#         return None
        
#     title_link = right_div.find('a')
#     publishing_organization = title_link.text.strip() if title_link else ''
    
#     desc_div = right_div.find('div', class_=None)
#     description = desc_div.text.strip() if desc_div else ''
    
#     metadata_div = right_div.find('div', class_='document-metadata')
#     if metadata_div:
#         stage_info = metadata_div.find('div').text.strip()
#         parts = stage_info.split(' > ')
        
#         stage = parts[0]
#         category = parts[-1]
#         subcategory = ' > '.join(parts[1:-1]) if len(parts) > 2 else ''
        
#         pub_date = metadata_div.find_all('div')[1].text.replace('Published:', '').strip()
#     else:
#         stage, category, subcategory, pub_date = '', '', '', ''

#     return {
#         'filesize': filesize,
#         'publishing_organization': publishing_organization,
#         'title': description or publishing_organization,
#         'stage': stage,
#         'subcategory': subcategory,
#         'category': category,
#         'publication_date': pub_date
#     }

def get_project_id(project_name):
    """
    Look up project ID using our stored mapping if available.
    If we have a stored reference for this project name, use it to look up the ID.
    Otherwise, return None to trigger the prompt for a new reference.
    """
    # Check if we have a stored reference for this project name
    if project_name in project_mappings:
        stored_reference = project_mappings[project_name]
        try:
            # Look up the project ID using the stored reference
            result = supabase.table('projects').select('id').eq('reference', stored_reference).execute()
            if result.data and len(result.data) > 0:
                print(f"Using stored reference '{stored_reference}' for project: {project_name}")
                return result.data[0]['id']
        except Exception as e:
            print(f"Error looking up project: {e}")
    
    # If we don't have a stored mapping or the lookup failed, return None
    return None

def prompt_for_project_reference(project_name):
    """
    Ask user to provide correct project reference when not found.
    Stores the provided reference in our mappings dictionary for future use.
    """
    print(f"\nProject not found: {project_name}")
    while True:
        reference = input("Please enter the correct project reference number (or 'skip' to skip this document): ")
        if reference.lower() == 'skip':
            return None
        
        try:
            # Try to look up the project ID with the provided reference
            result = supabase.table('projects').select('id').eq('reference', reference).execute()
            if result.data and len(result.data) > 0:
                # Store the successful mapping for future use
                project_mappings[project_name] = reference
                print(f"Stored mapping: {project_name} -> {reference}")
                return result.data[0]['id']
            print("Project reference not found. Please try again.")
        except Exception as e:
            print(f"Error looking up project: {e}")

def parse_date(date_str):
    """
    Convert date string to ISO format for database storage.
    Handles multiple date formats and returns None if parsing fails.
    """
    date_formats = [
        '%d/%m/%Y',    # For format: 28/10/2015
        '%B %d, %Y',   # For format: October 28, 2015
        '%Y-%m-%d',    # For format: 2015-10-28
        '%d-%m-%Y',    # For format: 28-10-2015
    ]
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_str.strip(), date_format)
            return parsed_date.isoformat()
        except ValueError:
            continue
    
    print(f"Warning: Could not parse date '{date_str}' with any known format")
    return None

# def parse_date(date_str):
#     """
#     Convert date string to ISO format for database storage.
#     Returns None if parsing fails.
#     """
#     try:
#         # Add your date parsing logic here based on the input format
#         # This is a simple example - adjust according to your actual date format
#         parsed_date = datetime.strptime(date_str, '%B %d, %Y')
#         return parsed_date.isoformat()
#     except ValueError:
#         print(f"Warning: Could not parse date '{date_str}'")
#         return None

def save_to_supabase(documents):
    """
    Save documents to Supabase database.
    """
    for doc in documents:
        project_id = get_project_id(doc['project_name'])
        if not project_id:
            # Check our in-memory mapping first
            if doc['project_name'] in project_mappings:
                stored_reference = project_mappings[doc['project_name']]
                project_id = get_project_id(stored_reference)
            else:
                project_id = prompt_for_project_reference(doc['project_name'])
                if not project_id:
                    continue
        
        # Prepare document data for insertion
        doc_data = {
            'project_id': project_id,
            'publishing_organization': doc['publishing_organization'],
            'title': doc['title'],
            'filesize': doc['filesize'],
            'stage': doc['stage'],
            'subcategory': doc['subcategory'],
            'category': doc['category'],
            'publication_date': parse_date(doc['publication_date']),
            'applicant': doc['applicant'],
            'document_url': doc['document_url']  # Add URL to the database insert
        }
        
        try:
            supabase.table('old_documents').insert(doc_data).execute()
            print(f"Saved document: {doc['title']}")
        except Exception as e:
            print(f"Error saving document: {e}")

def extract_documents(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    project_name, applicant = get_project_info(soup)
    
    document_bodies = soup.find_all('div', class_='document-body')
    documents = []
    for doc_div in document_bodies:
        doc_info = parse_document_entry(doc_div)
        if doc_info:
            doc_info['project_name'] = project_name
            doc_info['applicant'] = applicant
            documents.append(doc_info)
    
    return documents

def process_urls_from_csv(csv_path, url_column):
    """
    Reads URLs from a CSV file and processes each one to extract iframe content.
    
    Parameters:
    csv_path (str): Path to the CSV file containing URLs
    url_column (str): Name of the column containing the URLs
    """
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Process each URL
    for index, row in df.iterrows():
        try:
            # Get the initial webpage
            initial_response = requests.get(row[url_column], headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            initial_response.raise_for_status()

            html_content = get_archived_content(row[url_column])
            print(f"Successfully accessed  content for URL #{index + 1}")
            # print("-" * 50)

            documents = extract_documents(html_content)
            save_to_supabase(documents)
            
            # Optional: Print out all mappings at the end for reference
            print("\nProject mappings used in this session:")
            for name, reference in project_mappings.items():
                print(f"{name} -> {reference}")
            
            # return (document_url)
                
        except Exception as e:
            print(f"Error processing URL {row[url_column]}: {str(e)}")

def main():
    """
    Main function to process the HTML file and save documents to Supabase.
    The project_mappings dictionary will persist throughout this execution.
    """

    csv_path = 'urls.csv'
    url_column_name = 'url'

    process_urls_from_csv(csv_path, url_column_name)

    print("All urls processed.")


    # Define the URL we want to fetch
    # url = "https://webarchive.nationalarchives.gov.uk/ukgwa/20151202234545/http://infrastructure.planninginspectorate.gov.uk/projects/eastern/rookery-south-energy-from-waste-generating-station/?ipcsection=docs"

    # Make the HTTP request and get the response
    # response = requests.get(url)

    # # Ensure we're using UTF-8 encoding, just like in your original code
    # response.encoding = 'utf-8'

    # # Get the HTML content from the response
    # iframe_content = response.text

    # real_url = get_archived_content(iframe_content)

    # real_response = requests.get(real_url)
    # real_response.encoding = 'utf-8'

    # html_content = get_archived_content(url)

    # print("Hi: ", html_content)



if __name__ == "__main__":
    main()
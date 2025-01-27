import requests
from bs4 import BeautifulSoup as BS
import os
from docx import Document
import re
import sys
import time
from random import uniform

if len(sys.argv) < 3:
    print('Usage: %s Projectnumber "Project Name" NumberofPagesofReps (default is 50)' % sys.argv[0])
    sys.exit()

PrjNum = sys.argv[1]
PrjName = sys.argv[2]
PagesofReps = 50
if(len(sys.argv) == 4):
    PagesofReps = int(sys.argv[3])

# Setup session and headers
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# # Set initial cookies
# cookies_data = {
#     'cookies_policy': '{"essential":true,"analytics":true}',
#     'cookies_preferences_set': 'true',
#     'cookie_banner_accepted': 'hide'
# }
# session.cookies.update(cookies_data)

def get_all_representation_urls():
    """Collect all representation URLs first"""
    all_urls = []
    
    for num in range(1, PagesofReps + 1):
        url = f"https://national-infrastructure-consenting.planninginspectorate.gov.uk/projects/{PrjNum}/representations?page={num}"
        page = session.get(url, headers=headers)
        soup = BS(page.content, "lxml")
        reps = soup.find_all("li", class_="ui-results__result", attrs={"data-cy": "representation"})
        
        if not reps:
            print(f"No representations found on page {num}, stopping collection")
            break
            
        for rep in reps:
            repid = rep.find("a")
            repurl = repid["href"]
            all_urls.append(repurl.split("representations/")[-1])
            
        print(f"Collected URLs from page {num}")
        # time.sleep(uniform(1.0, 2.0))  # Random delay between page requests
        
    return all_urls

def process_representation(rep_id):
    """Process a single representation"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            RepUrl = f"https://national-infrastructure-consenting.planninginspectorate.gov.uk/projects/{PrjNum}/representations/{rep_id}"
            
            # Make request with delay
            time.sleep(uniform(0.1, 1.0))
            RepPage = session.get(RepUrl, headers=headers)
            
            if RepPage.status_code == 429:
                retry_count += 1
                wait_time = int(RepPage.headers.get('Retry-After', 10))
                print(f"Rate limited. Waiting {wait_time} seconds before retry {retry_count}/{max_retries}")
                time.sleep(wait_time)
                continue
                
            if RepPage.status_code != 200:
                print(f"Failed with status code: {RepPage.status_code}")
                return None
                
            soup2 = BS(RepPage.content, "lxml")
            
            # Get the main content - try to find the content after the cookie banner
            all_content_divs = soup2.find_all("div", class_="govuk-grid-column-two-thirds")
            repinfo = None
            
            for div in all_content_divs:
                if 'cookie-banner' not in str(div) and 'cookie_banner' not in str(div):
                    repinfo = div
                    break
            
            if repinfo is None:
                print(f"Could not find main content for representation {rep_id}")
                return None
            
            # Extract information
            heading = repinfo.find("h1", class_=["govuk-heading-l", "govuk-heading-s", "govuk-heading-m"])
            if not heading:
                print(f"Could not find heading for representation {rep_id}")
                return None
                
            Name = heading.text.strip()
            RR = repinfo.find("div", class_="pins-rte")
            if not RR:
                print(f"Could not find representation text for {rep_id}")
                return None
                
            RepText = RR.text.strip()
            newstring = re.sub("\s[0-9+]\)|\s[0-9+]\.","\n\g<0>",RepText)
            
            # Handle PDF attachments
            pdfinfo = soup2.find_all("p", class_="govuk-body")
            pdf_data = None
            
            if len(pdfinfo) > 0:
                links = soup2.find_all("a")
                for link in links:
                    if ('pdf' in link.get('href', '')):
                        if not os.path.exists(PrjName):
                            os.mkdir(PrjName)
                        
                        filelink = link.get('href')
                        newfilename = f"{Name}_{rep_id}_Relevant Representation.pdf"
                        
                        response = requests.get(filelink, stream=True)
                        with open(os.path.join(PrjName, newfilename), 'wb') as fd:
                            for chunk in response.iter_content(2000):
                                fd.write(chunk)
                        pdf_data = filelink
            
            return {
                'name': Name,
                'rep_id': rep_id,
                'text': newstring,
                'pdf_link': pdf_data
            }
            
        except Exception as e:
            print(f"Error processing representation {rep_id}: {str(e)}")
            retry_count += 1
            time.sleep(5)
    
    return None

def main():
    print("Collecting all representation URLs...")
    all_urls = get_all_representation_urls()
    print(f"Found {len(all_urls)} representations")
    
    # Setup document
    document = Document()
    table = document.add_table(rows=1, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Representee"
    hdr_cells[1].text = "Representation"
    
    # Process representations
    total_pdfs = 0
    for i, rep_id in enumerate(all_urls, 1):
        print(f"Processing representation {i} of {len(all_urls)}")
        result = process_representation(rep_id)
        
        if result:
            row_cells = table.add_row().cells
            
            repee = f"Rep No: {result['rep_id']}\n{result['name']}"
            repn = result['text']
            
            if result['pdf_link']:
                repn += f"\n\nPDF Attachment for {result['rep_id']} '{result['pdf_link']}'\n"
                total_pdfs += 1
            
            row_cells[0].text = repee
            row_cells[1].text = repn
    
    print("Saving into Word. This may take a couple of minutes...")
    document.save(f"{PrjNum}_{PrjName}_Table of Relevant Reps.docx")
    print(f"\n\nAll Complete. In total there were {total_pdfs} PDF files")

if __name__ == "__main__":
    main()
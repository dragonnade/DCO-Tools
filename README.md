# DCO-Tools
## Collection of DCO-related tools

### DCO Toolkit
Early proof of concept to confirm the usefulness of being able to trace precedent through the similarity of existing provisions.
Further development underway, with streamlining the comparison function the most successful new feature.

### Planning Inspectorate - Document URL Scraper
Scrapes the document links and metadata from the Planning Inspectorate project website (https://national-infrastructure-consenting.planninginspectorate.gov.uk/).
This is needed to allow more powerful filtering and search functionality than is currently provided by the Planning Inspectorate website.
There are plans for the Planning Inspectorate site to have an API (e.g. the all-projects csv file available here: https://national-infrastructure-consenting.planninginspectorate.gov.uk/project-search), however until this is provided, fragile web scraping is required.
Once the API is made available, the underlying infrastructure will be more reliable and this project will be more appropriate to be handed over for long-term support by the firm.


### National Archives - Document URL Scraper
Scrapes the document links and (with less accuracy) metadata from the old Planning Inspectorate website, as archived by the National Archives.
Required as the Planning Inspectorate removes documents from its website after 5 years, whilst clients will be relying on the documents for years to come.
These links are static, so with improvements to the metadata scraping, this can be easily maintained as a static database.

However, the National Archives website throws 403 errors resulting in a 404 page if you look at too many web pages in a short space of time (something like 10 pages within 10 minutes). This database needs a health warning so that the user doesn't think that everything is broken when the 403 error just needs to time out.

### Relevant Reps
Scrapes the content of relevant representations made on a project into a single word document, and downloads any .pdf files provided by parties making representations.
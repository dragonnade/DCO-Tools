A script to scrape the document URLs and associated metadata from the Planning Inspectorate Beta website.

Allows for robust filtering and searching for documents across multiple projects.

Runs on a Raspberry Pi. A check for new documents is run daily at 16:00 via a cron job. Also runs as a service, polling the Supabase database every 30 seconds for new projects added via the /docrequest page. Checks and updates the document list for the specified project.


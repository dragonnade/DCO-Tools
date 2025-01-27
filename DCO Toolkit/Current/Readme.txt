Continued development of XML extraction and similarity tracker elements.

legislation-parser.py:

Updates XMLDataExtractor.py.
Early efforts to improve the extraction of data from the legislation.gov.uk XML files.
Improved use of XML namespaces and early management of Schedules.

dco-similarity-matcher.py:
Updated from the original to use a locally hosted database for testing.

Implements pre-levenshtein tests to find candidates to run Levenshtein on, in order to minimise processing requirements and improve speed.

Word overlap - article must have a minimum shared word count
Hashing - to allow for identical provisions to be identified immediately
Categories - to allow (in theory) a preference for articles in the same category based on shared words in the article headings
Word count - article must be within a minimum/maximum distance in word count

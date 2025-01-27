Original script to extract the text from DCO articles and compare each article against all previous articles.

Uses xml files of the body of DCOs (no Schedules), and uses Levenshtein throughout. Returns only top 5 most-similar articles. No discretion about how many articles from each previous DCO, and no threshold of minimum similarity.

Results saved to pickled Pandas dataframe, then exported to a csv file. CSV file then processed using Excel PowerQuery.

The only processing of the article text is to remove the paragraph numbering and the Order title from provisions, so that the Order name does not count as a difference to otherwise identical articles.


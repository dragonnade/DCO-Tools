from XMLDataExtractor import parse_xml
import gc
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import pandas as pd
from bs4 import BeautifulSoup
import os
import heapq
import sys
from fuzzywuzzy import fuzz
import Levenshtein
import time

directory = 'newfolderomg'
# deadcell = 'long quotes break me'


def make_hyperlink(url):
    return '''=HYPERLINK("{url}","Link")'''
    # return f'=HYPERLINK("{url}","Link")'

def levenshtein_similarity(str1, str2):
    return Levenshtein.seqratio(str1, str2)
    # return fuzz.ratio(str1, str2)

files = []
for filename in (os.listdir(directory)):
    files.append(filename)
sorted_files = sorted(files, key=lambda x: (int(x.split('_')[0]), int(x.split('_')[1].split('.')[0])))

for filename in sorted_files:
    file = os.path.join(directory, filename)
    if os.path.isfile(file):
        
        df = parse_xml(file)
        # print(df.iloc[-1,4])


        df.to_pickle('new.pkl')
        del df

        
        # print("working...")

        Text = open("DCO_Similarity.csv", 'a', encoding='utf-8')

        data = []


        db = pd.read_pickle('base.pkl')
        newdf = pd.read_pickle('new.pkl')

        db.reset_index(drop=True, inplace=True)

        for idx, row in enumerate(newdf.itertuples(), start=0):
            # Get the top 5 most similar articles using Levenshtein similarity
            similar_indices = sorted(range(len(db['Text'])), key=lambda i: levenshtein_similarity(row.Text, db['Text'][i]), reverse=True)[:5]
            
            for i in similar_indices:
                similarity_score = levenshtein_similarity(row.Text, db['Text'][i])*100
                # print(similarity_score)

                if similarity_score >= 0:  # Customize the similarity threshold as needed (70 is used as an example)
                    print(
                        "{}%|{}|{}|{}|{}|{}|{}|{}|{}".format(
                            round(similarity_score),
                            row.Order,
                            row.Title,
                            row.Art,
                            db.loc[i, 'Art'],
                            db.loc[i, 'Title'],
                            db.loc[i, 'Order'],
                            row.Link,
                            db.loc[i, 'Link']
                        ),
                        file=Text
                    )
            print("Article", row.Art, row.Title, "complete...")
        
        print(row.Order, "Completed")

        Text.close()

        cat = pd.concat([db, newdf], ignore_index=True)
        cat.to_pickle('base.pkl')

        del newdf
        del db
        gc.collect()

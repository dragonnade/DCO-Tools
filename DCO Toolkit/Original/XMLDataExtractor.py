import re
import pandas as pd
import xml.etree.ElementTree as ET

def replace_strings(row):
    ordername = row['Order']
    textname = row['Text']
    # Replace occurrences of 'Order' in 'Text' with 'Text'
    replaced_text = text.replace(ordername, textname)
    return replaced_text

def extract_text(element):
    text_content = ""
    if element.text:
        text_content += element.text
    for child in element:
        child_text = extract_text(child)
        text_content += child_text
    if element.tail:
        text_content += element.tail
    return text_content.strip()

def assess_interpretation_text(element):
    interpretation_data = []
    namespace = {'ns0': 'http://www.legislation.gov.uk/namespaces/legislation',
                 'dc': 'http://purl.org/dc/elements/1.1/',
                 'ukm': 'http://www.legislation.gov.uk/namespaces/metadata'}

    # Check if the element's title is "Interpretation"
    if element.find('./ns0:Title', namespace).text.strip() == "Interpretation":
        # Extract all List Items under Unordered List Class="Definition"
        definition_list = element.find('.//ns0:UnorderedList[@Class="Definition"]', namespace)
        if definition_list is not None:
            list_items = definition_list.findall('.//ns0:ListItem', namespace)
            for item in list_items:
                # Extract text content of the List Item
                item_text = extract_text(item)
                interpretation_data.append(item_text)

    return interpretation_data

def parse_xml(xml_file):
    # Parse the XML data 
    tree = ET.parse(xml_file)
    root = tree.getroot()
    xml_root = root

    # Define the namespaces
    namespace = {'ns0': 'http://www.legislation.gov.uk/namespaces/legislation',
                 'dc': 'http://purl.org/dc/elements/1.1/',
                 'ukm': 'http://www.legislation.gov.uk/namespaces/metadata'}#,
                 #'ukm': 'http://www.legislation.gov.uk/namespaces/ukm'}
    xxx = {'ukm': 'http://www.legislation.gov.uk/namespaces/ukm'}

    # Initialize lists to store extracted data
    orders = []
    years = []
    numbers = []
    titles = []
    pnumbers = []
    text_contents = []

    # Iterate through P1 groups and extract required information
    for p1group in root.findall('.//ns0:P1group', namespace):
        order = root.find('.//dc:title', namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}).text.strip()
        orders.append(order)
        # print(order)


        
        # Extract ukm:Year and ukm:Number
        year = root.find('.//ukm:Year', namespace).get('Value')
        number = root.find('.//ukm:Number', namespace).get('Value')
        years.append(year)
        numbers.append(number)
        
        # Extract ns0:Title
        title = p1group.find('./ns0:Title', namespace).text.strip()
        titles.append(title)
        
        # Extract ns0:Pnumber
        pnumber = p1group.find('./ns0:P1/ns0:Pnumber', namespace).text.strip()
        pnumbers.append(pnumber)
        
        # Extract all ns0:Text elements and concatenate their text content
        text_elements = p1group.findall('.//ns0:Text', namespace)
        try:
            # text_content = ' '.join([extract_text(text_element) for text_element in text_elements])
            paragraphs = [extract_text(text_element) for text_element in text_elements]
            text_contents.append(paragraphs)
            # text_contents.append(text_content)
        except:
            text_contents.append("Failed")
            # print(text_contents)

    # Create a DataFrame from the extracted data
    data = {
        'Order': orders,
        'Year': years,
        'No.': numbers,
        'Title': titles,
        'Art': pnumbers,
        'Text': text_contents
    }

    df = pd.DataFrame(data)
    # print("Row: ", df.loc[43,'Text'])

    try:
        order_string = df.loc[1, 'Order'].strip()
        # Apply replacement to each paragraph in the array
        df['Text'] = df['Text'].apply(lambda x: [re.sub(re.escape(order_string), 'Order', p, flags=re.IGNORECASE) for p in x])
    except:
        print("No Order")

    # df['Paragraphs'] = [
    #     [{'Type': p.tag.split('}')[-1], 'Text': extract_text(p)}
    #     for p in element.findall('.//ns0:P2', namespace)]
    #     for element in xml_root.findall('.//ns0:P1group', namespace)
    # ]
    df['Link'] = 'https://www.legislation.gov.uk/uksi/' + df['Year'].astype(str) + '/' + df['No.'].astype(str) + '/article/' + df['Art'].astype(str) +'/made'
    df['UID'] = df['Year'].astype(str) + '_' + df['No.'].astype(str) + '_' + df['Art'].astype(str)

    # print("Another Row: ", df.loc[43,'Text'])

    # Return the DataFrame and the XML tree
    return df#, xml_root

    # for index, row in df.iterrows():
    # print(df.loc[0,'Text'])

    # Return the DataFrame
    # return df



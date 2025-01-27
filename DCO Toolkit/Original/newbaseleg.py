from XMLDataExtractor import parse_xml

file = "IpswichChord.xml"
df = parse_xml(file)


df.to_pickle('base.pkl')
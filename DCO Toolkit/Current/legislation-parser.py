# LegislationXMLParser.py

import xml.etree.ElementTree as ET
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@dataclass
class PartInfo:
    """Data class to hold Part information"""
    number: str
    title: str

@dataclass
class LegislationMetadata:
    """Data class to hold legislation metadata"""
    title: str
    year: int
    number: int
    created: Optional[str] = None
    valid: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    identifier: Optional[str] = None
    extent: List[str] = None
    current_part: Optional[PartInfo] = None
    
    def __post_init__(self):
        self.extent = self.extent or []

class LegislationParsingError(Exception):
    """Custom exception for legislation parsing errors"""
    pass

class ScheduleConfig:
    """Configuration for interactive schedule extraction"""
    def __init__(self):
        self.selected_schedules = {}  # Will store user selections for each schedule

    def add_schedule_selection(self, schedule_number: str, extract: bool):
        """Add user's selection for a specific schedule"""
        self.selected_schedules[schedule_number] = extract

class LegislationXMLParser:
    """Enhanced parser for legislation.gov.uk XML documents"""
    
    # Define namespaces as a class constant
    NAMESPACES = {
        'ns0': 'http://www.legislation.gov.uk/namespaces/legislation',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'ukm': 'http://www.legislation.gov.uk/namespaces/metadata',
        'dct': 'http://purl.org/dc/terms/',
        'metalex': 'http://www.metalex.eu/metalex/2008-05-02',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'xhv': 'http://www.w3.org/1999/xhtml/vocab#'
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content with robust character handling"""
        if not text:
            return ""
        if text is None:
            return ""
            
        # Define replacements using ASCII and Unicode codes
        replacements = {
            # Smart Quotes
            '\x93': '"',    # Windows "smart" opening quote
            '\x94': '"',    # Windows "smart" closing quote
            '\x91': "'",    # Windows "smart" opening single quote
            '\x92': "'",    # Windows "smart" closing single quote
            
            # Unicode quotes
            '\u2018': "'",  # Left single quotation mark
            '\u2019': "'",  # Right single quotation mark
            '\u201c': '"',  # Left double quotation mark
            '\u201d': '"',  # Right double quotation mark

            # Special characters
            'ô': 'o',       # o with circumflex
            '\u00F4': 'o',  # o with circumflex (Unicode)
            
            # Dashes
            '\x96': '-',    # Windows en-dash
            '\x97': '-',    # Windows em-dash
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
            '\u2015': '-',  # Horizontal bar
            
            # Other special characters
            '\x85': '...',  # Windows ellipsis
            '\u2026': '...', # Ellipsis
            '\x95': '•',    # Windows bullet
            '\u2022': '•',  # Bullet
            
            # Common HTML entities
            '&quot;': '"',
            '&apos;': "'",
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&ndash;': '-',
            '&mdash;': '-',
            '&hellip;': '...',
            
            # Spaces and whitespace
            '\xa0': ' ',    # Non-breaking space
            '\t': ' ',      # Tab
            '\r': ' ',      # Carriage return
            '\xA0': ' ',    # Another form of non-breaking space
        }
        
        # First, try to handle UTF-8 encoding issues
        try:
            # Try to encode then decode to catch any encoding issues
            text = text.encode('utf-8', 'ignore').decode('utf-8')
        except UnicodeError:
            # If that fails, try to force ASCII
            text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Apply all replacements
        for old, new in replacements.items():
            text = text.replace(old, new)

        # Instead of removing all non-ASCII characters, we'll preserve known Welsh characters
        welsh_chars = {'Ŵ', 'ŵ', 'Ŷ', 'ŷ', 'Ê', 'ê', 'Î', 'î', 'Ô', 'ô', 'Û', 'û', 'Á', 'á', 'É', 'é', 'Í', 'í', 'Ó', 'ó', 'Ú', 'ú', 'Ý', 'ý'}


        # Create a function to determine if a character should be kept
        def should_keep_char(char):
            return ord(char) < 128 or char in welsh_chars
        
        # Filter characters while preserving Welsh characters
        text = ''.join(char for char in text if should_keep_char(char))    

        # # Remove any remaining non-ASCII characters
        # text = ''.join(char for char in text if ord(char) < 128)
        
        # Normalize whitespace: collapse multiple spaces and trim
        text = ' '.join(text.split())
        # self.logger.info("Attempting to export cleaned text")
        return text.strip()

    def extract_text_content(self, element: ET.Element) -> str:
        """Extract text with proper encoding handling"""
        text = ""
        if element.text:
            text += self.clean_text(element.text)
        for child in element:
            child_text = self.extract_text_content(child)
            if child_text:
                text += " " + child_text
        if element.tail:
            text += self.clean_text(element.tail)
        return " ".join(text.split())

    def _get_text(self, element: ET.Element, xpath: str, default: str = '') -> str:
        """Safely extract text from an XML element using XPath"""
        try:
            found = element.find(xpath, self.NAMESPACES)
            # self.logger.info("Attempting to return found.text.strip from _get_text")
            return found.text.strip() if found is not None and found.text else default
        except AttributeError:
            return default

    def _get_spatial_extent(self, root: ET.Element) -> List[str]:
        """Extract geographical extent information"""
        extents = []
        extent_nodes = root.findall('.//dct:spatial', self.NAMESPACES)
        for node in extent_nodes:
            label = node.find('.//rdfs:label', self.NAMESPACES)
            if label is not None and label.text:
                # self.logger.info("Attempting to append label.text")
                extents.append(label.text.strip())
        return extents

    def extract_metadata(self, root: ET.Element) -> LegislationMetadata:
        """Extract comprehensive metadata with corrected year and number handling"""
        try:
            # Find the SecondaryMetadata section
            secondary_metadata = root.find('.//ukm:SecondaryMetadata', self.NAMESPACES)
            if secondary_metadata is None:
                raise LegislationParsingError("Required SecondaryMetadata section missing")
                
            # Extract year and number from their specific elements
            year_elem = secondary_metadata.find('ukm:Year', self.NAMESPACES)
            number_elem = secondary_metadata.find('ukm:Number', self.NAMESPACES)
            
            # Get the title from dc:title element
            title = self._get_text(root, './/dc:title')

            year = year_elem.get('Value') if year_elem is not None else None
            number = number_elem.get('Value') if number_elem is not None else None
            
            if not all([year, number]):
                raise LegislationParsingError("Required year or number fields missing")
                
            return LegislationMetadata(
                title=title,
                year=int(year),
                number=int(number),
                created=self._get_text(root, './/dct:created'),
                valid=self._get_text(root, './/dct:valid'),
                type=self._get_text(root, './/dct:type'),
                description=self._get_text(root, './/dct:description'),
                identifier=self._get_text(root, './/dct:identifier'),
                extent=self._get_spatial_extent(root)
            )
        except ValueError as e:
            raise LegislationParsingError(f"Error parsing metadata: {str(e)}")

    def extract_article_text(self, element: ET.Element) -> List[str]:
        """Extract article text content with proper handling of nested elements"""
        text_content = []
        
        for text_elem in element.findall('.//ns0:Text', self.NAMESPACES):
            # Get all text content including nested elements
            full_text = ''.join(text_elem.itertext())
            cleaned_text = self.clean_text(full_text)
            if cleaned_text:
                text_content.append(cleaned_text)
                
        return text_content

    def find_all_parts(self, element: ET.Element) -> List[ET.Element]:
        """
        Recursively find all Part elements in the XML tree.
        
        This method searches through the entire XML tree under the given element,
        looking for any elements that represent Parts. It handles cases where Parts
        might be nested at different levels in the XML hierarchy.
        
        Args:
            element: The XML element to search under
            
        Returns:
            A list of all Part elements found
        """
        parts = []
        # Handle the case where element might be None
        if element is None:
            return parts
            
        # Search through all children of this element
        for child in element:
            # Check if this element is a Part (handling namespaces)
            if '}Part' in child.tag:  # This handles both ns0:Part and other namespace prefixes
                parts.append(child)
            # Recursively search this child's children
            parts.extend(self.find_all_parts(child))
        
        return parts

    def _build_navigation_links(self, root: ET.Element) -> Dict[str, Dict[str, Optional[str]]]:
        """Build previous/next navigation links based on document structure"""
        navigation = {}
        sections = root.findall('.//ns0:P1group', self.NAMESPACES)
        
        for i, section in enumerate(sections):
            number = self._get_text(section, './/ns0:Pnumber')
            if number:
                navigation[number] = {
                    'prev': self._get_text(sections[i-1], './/ns0:Pnumber') if i > 0 else None,
                    'next': self._get_text(sections[i+1], './/ns0:Pnumber') if i < len(sections)-1 else None
                }
        
        return navigation

    def extract_version_information(self, root: ET.Element) -> Dict[str, Any]:
        """Extract version-specific information"""
        return {
            'version_date': self._get_text(root, './/dct:valid'),
            'previous_version': self._get_text(root, './/dct:replaces'),
            'next_version': self._get_text(root, './/dct:isReplacedBy'),
            'is_current': not bool(root.find('.//dct:isReplacedBy', self.NAMESPACES))
        }


    def _build_legislation_uri(self, metadata: LegislationMetadata) -> str:
        """
        Build the base URI for legislation without the 'made' suffix.
        
        The base URI should be in the format:
        https://www.legislation.gov.uk/uksi/YEAR/NUMBER
        
        This allows us to append specific paths and the 'made' suffix as needed.
        
        Args:
            metadata: Legislation metadata containing year and number
            
        Returns:
            Base URI string without 'made' suffix
        """
        base_uri = "https://www.legislation.gov.uk"
        return f"{base_uri}/uksi/{metadata.year}/{metadata.number}"

    def _generate_unique_id(self, metadata: LegislationMetadata) -> str:
        """Generate unique identifier following legislation.gov.uk patterns"""
        return f"{metadata.year}_{metadata.number}"


    def parse_xml(self, xml_file: str) -> pd.DataFrame:
        """Main parsing function with interactive schedule selection"""
        self.logger.info(f"Starting to parse {xml_file}")
        
        try:
            # Parse XML file with explicit encoding handling
            parser = ET.XMLParser(encoding="utf-8")
            # Force utf-8 reading of the file
            with open(xml_file, 'r', encoding='utf-8') as f:
                tree = ET.parse(f, parser=parser)
            root = tree.getroot()

            # Extract metadata with better error handling
            try:
                metadata = self.extract_metadata(root)
                self.logger.info("Metadata extracted successfully")
                print(f"Processing {metadata.title}")
            except LegislationParsingError as e:
                self.logger.error(f"Metadata extraction failed: {str(e)}")
                raise

            # Build base URI for legislation
            base_uri = self._build_legislation_uri(metadata)
            

            # First, identify all available schedules
            available_schedules = []
            for schedule in root.findall('.//ns0:Schedule', self.NAMESPACES):
                schedule_number = schedule.find('.//ns0:Number', self.NAMESPACES)
                schedule_title = schedule.find('.//ns0:Title', self.NAMESPACES)
                # print(schedule_number, "and", schedule_title)
                
                if schedule_number is not None and schedule_title is not None:

                    # # Log the elements themselves
                    # self.logger.info(f"Raw elements - Number: {schedule_number}, Title: {schedule_title}")
                    
                    # # Log their text content
                    # self.logger.info(f"Text content - Number: {schedule_number.text}, Title: {schedule_title.text}")

                    # # Log the type of each value
                    # self.logger.info(f"Types - Number text type: {type(schedule_number.text)}, Title text type: {type(schedule_title.text)}")


                    # For number, we need to handle both direct text and CommentaryRef cases
                    if schedule_number.text is not None:
                        # self.logger.info(f"Schedule_number.text is not none. Proceeding...")
                        number_text = schedule_number.text
                    else:
                        # self.logger.info(f"Schedule_number.text is none. Using itertext...")
                        # Try to get the full text including any nested content
                        number_text = ''.join(schedule_number.itertext())
                    
                    title_text = schedule_title.text

                    
                    
                    # Try to extract and log the text separately before cleaning
                    # number_text = schedule_number.text
                    # title_text = schedule_title.text
                    # self.logger.info(f"Raw text before cleaning - Number: '{number_text}', Title: '{title_text}'")

                    number = number_text.strip().replace('SCHEDULE ', '')
                    title = title_text.strip()
                    available_schedules.append((number, title))

            # Get user selection for each schedule
            schedule_config = ScheduleConfig()
            for number, title in available_schedules:
                while True:
                    response = input(f"\nExtract Schedule {number}: {title}? (Y/N): ").upper()
                    if response in ['Y', 'N']:
                        schedule_config.add_schedule_selection(number, response == 'Y')
                        break
                    print("Please enter Y or N")

            # Process articles with proper text cleaning
            articles_data = []
            body = root.find('.//ns0:Body', self.NAMESPACES)  # Find the main body section

            if body is None:
                self.logger.warning("No Body element found in XML")
                return pd.DataFrame()  # Return empty DataFrame if no body found
            
            p1groups = body.findall('.//ns0:P1group', self.NAMESPACES)
            self.logger.info(f"Found {len(p1groups)} articles")


            if body:
                for p1group in p1groups:
                    try:
                        # Try multiple XPath patterns to find the article number
                        article_number_elem = (
                            p1group.find('.//ns0:P1/ns0:Pnumber', self.NAMESPACES) or 
                            p1group.find('.//ns0:Pnumber', self.NAMESPACES)
                        )
                        # Add debug logging
                        if article_number_elem is None:
                            self.logger.debug(f"No article number found in P1group: {ET.tostring(p1group, encoding='unicode')[:200]}...")
                        # # More defensive text extraction
                        # article_number_elem = p1group.find('./ns0:P1/ns0:Pnumber', self.NAMESPACES)
                        article_art = self.clean_text(article_number_elem.text) if article_number_elem is not None else ''
                        
                        title_elem = p1group.find('./ns0:Title', self.NAMESPACES)
                        title = self.clean_text(title_elem.text) if title_elem is not None else ''
                        
                        article_data = {
                            'Order': self.clean_text(metadata.title),
                            'Year': metadata.year,
                            'No.': metadata.number,
                            'Title': title,
                            'Art': article_art,
                            'Text': [self.clean_text(text) for text in self.extract_article_text(p1group)],
                            'Schedule': None,
                            'Schedule_Name': None,
                            # 'Link': f"{base_uri}/article/{article_art}/made" if article_art else base_uri
                            'Link': f"{base_uri}/article/{article_art}/made" if article_art else f"{base_uri}/made"
                        }
                        articles_data.append(article_data)
                    except Exception as e:
                        self.logger.warning(f"Error processing P1group: {str(e)}")
                        continue

            # Process selected schedules
            # schedules = self.extract_schedules(root, schedule_config, base_uri)
            schedules = self.extract_schedules(root, schedule_config, base_uri)
            
            # Add schedule data if present
            for schedule in schedules:
                for content in schedule['content']:
                    schedule_data = {
                        'Order': self.clean_text(metadata.title),
                        'Year': metadata.year,
                        'No.': metadata.number,
                        'Title': content['title'],  # Just the section title without Schedule prefix
                        'Art': content['article_number'],  # Use the article number directly
                        'Text': content['text'],
                        'Schedule': schedule['number'],
                        'Schedule_Name': schedule['name'],  # Add the new schedule name column
                        'Part_Number': content.get('part_number'),
                        'Part_Title': content.get('part_title'),
                        'Link': content['Link']  # Now using the link generated during processing
                        # 'Link': f"{base_uri}/schedule/{schedule['number']}/made"
                    }
                    articles_data.append(schedule_data)

            self.logger.info(f"Processed {len(articles_data)} provisions")

            # Create DataFrame
            df = pd.DataFrame(articles_data)
            return df

        except Exception as e:
            raise LegislationParsingError(f"Unexpected error during parsing: {str(e)}")


    # def extract_schedules(self, root: ET.Element, config: ScheduleConfig) -> List[Dict]:
    #     """Extract schedules based on user selection"""
    #     try:
    #         schedules = []
            
    #         for schedule in root.findall('.//ns0:Schedule', self.NAMESPACES):
    #             try:
    #                 schedule_number = schedule.find('.//ns0:Number', self.NAMESPACES)
    #                 if schedule_number is None:
    #                     continue

    #                 # self.logger.info("Attempting to get number from schedule number")    
    #                 number = schedule_number.text.strip().replace('SCHEDULE ', '')
                    
    #                 # Skip if not selected
    #                 if number not in config.selected_schedules or not config.selected_schedules[number]:
    #                     continue
                    
    #                 # Extract schedule name from the Title element
    #                 schedule_title = self._get_text(schedule, './/ns0:Title')
                    
    #                 schedule_data = {
    #                     'number': number,
    #                     'name': schedule_title,  # Store the schedule name
    #                     'content': []
    #                 }
                    
    #                 # First, check if this Schedule has any Parts
    #                 # parts = schedule.findall('.//ns0:Part', self.NAMESPACES)

    #                 # Instead of using descendant axis (//) which can skip elements, use a more specific path
    #                 # parts = schedule.findall('./ns0:ScheduleBody/ns0:Part', self.NAMESPACES)
                    
    #                 # for part in schedule.findall('.//ns0:Part', self.NAMESPACES):
    #                 #     part_number = self._get_text(part, './/ns0:Number')
    #                 #     part_title = self._get_text(part, './/ns0:Title')
    #                 #     self.logger.info(f"Found Part: Number={part_number}, Title={part_title}")
    #                 #     # Also log the part's position in the XML tree
    #                 #     # parent = part.getparent()
    #                 #     # self.logger.info(f"Parent tag: {parent.tag if parent is not None else 'None'}")

    #                 schedule_body = schedule.find('.//ns0:ScheduleBody', self.NAMESPACES)

    #                 if schedule_body is not None:
    #                     # First try to find parts directly
    #                     parts = schedule_body.findall('./ns0:Part', self.NAMESPACES)
                        
    #                     if parts:
    #                         # Process Schedule with Parts structure
    #                         for part in parts:
    #                             part_number = self._get_text(part, './/ns0:Number')
    #                             part_title = self._get_text(part, './/ns0:Title')
                                
    #                             if part_number and part_title:
    #                                 current_part = PartInfo(number=part_number, title=part_title)
                                    
    #                                 # Process each P1group within this Part
    #                                 for p1group in part.findall('.//ns0:P1group', self.NAMESPACES):
    #                                     section_title = self._get_text(p1group, './/ns0:Title')
    #                                     p_number = self._get_text(p1group, './/ns0:P1/ns0:Pnumber')
                                        
    #                                     if not p_number:
    #                                         p_number = str(len(schedule_data['content']) + 1)
                                            
    #                                     content = {
    #                                         'article_number': p_number,
    #                                         'title': section_title,
    #                                         'text': self.extract_article_text(p1group),
    #                                         'part_number': current_part.number,
    #                                         'part_title': current_part.title
    #                                     }
    #                                     schedule_data['content'].append(content)
    #                     else:
    #                         # Process Schedule without Parts - content directly in ScheduleBody
    #                         direct_p1groups = schedule_body.findall('./ns0:P1group', self.NAMESPACES)
                            
    #                         if direct_p1groups:
    #                             # This is a valid schedule without parts - process it normally
    #                             for p1group in direct_p1groups:
    #                                 section_title = self._get_text(p1group, './/ns0:Title')
    #                                 p_number = self._get_text(p1group, './/ns0:P1/ns0:Pnumber')
                                    
    #                                 if not p_number:
    #                                     p_number = str(len(schedule_data['content']) + 1)
                                        
    #                                 content = {
    #                                     'article_number': p_number,
    #                                     'title': section_title,
    #                                     'text': self.extract_article_text(p1group),
    #                                     'part_number': None,  # No Part for this content
    #                                     'part_title': None
    #                                 }
    #                                 schedule_data['content'].append(content)

    #                     if not parts:  # If no parts found with direct search
    #                         # Check if this is truly a schedule without parts
    #                         # Look for P1group elements directly under ScheduleBody
    #                         direct_p1groups = schedule_body.findall('./ns0:P1group', self.NAMESPACES)
                            
    #                         if direct_p1groups:
    #                             # This is a valid schedule without parts - process it normally
    #                             for p1group in direct_p1groups:
    #                                 section_title = self._get_text(p1group, './/ns0:Title')
    #                                 p_number = self._get_text(p1group, './/ns0:P1/ns0:Pnumber')
                                    
    #                                 if not p_number:
    #                                     p_number = str(len(schedule_data['content']) + 1)
                                        
    #                                 content = {
    #                                     'article_number': p_number,
    #                                     'title': section_title,
    #                                     'text': self.extract_article_text(p1group),
    #                                     'part_number': None,  # No Part for this content
    #                                     'part_title': None
    #                                 }
    #                                 schedule_data['content'].append(content)
    #                         else:
    #                             # As a last resort, try recursive search for parts
    #                             parts = self.find_all_parts(schedule_body)

    #                 # if schedule_body is not None:
    #                 #     parts = schedule_body.findall('./ns0:Part', self.NAMESPACES)
    #                 #     if not parts:  # If no parts found with direct children, try recursive approach
    #                 #         parts = self.find_all_parts(schedule_body)
                    
    #                 # if parts:
    #                 #     # Process Schedule with Parts structure
    #                 #     for part in parts:
    #                 #         part_number = self._get_text(part, './/ns0:Number')
    #                 #         part_title = self._get_text(part, './/ns0:Title')
                            
    #                 #         if part_number and part_title:
    #                 #             current_part = PartInfo(number=part_number, title=part_title)
                                
    #                 #             # Process each P1group within this Part
    #                 #             for p1group in part.findall('.//ns0:P1group', self.NAMESPACES):
    #                 #                 section_title = self._get_text(p1group, './/ns0:Title')
    #                 #                 p_number = self._get_text(p1group, './/ns0:P1/ns0:Pnumber')
                                    
    #                 #                 if not p_number:
    #                 #                     p_number = str(len(schedule_data['content']) + 1)
                                        
    #                 #                 content = {
    #                 #                     'article_number': p_number,
    #                 #                     'title': section_title,
    #                 #                     'text': self.extract_article_text(p1group),
    #                 #                     'part_number': current_part.number,
    #                 #                     'part_title': current_part.title
    #                 #                 }
    #                 #                 schedule_data['content'].append(content)
    #                 # else:
    #                 #     # Process Schedule without Parts - content directly in ScheduleBody
    #                 #     schedule_body = schedule.find('.//ns0:ScheduleBody', self.NAMESPACES)
    #                 #     if schedule_body:
    #                 #         for p1group in schedule_body.findall('.//ns0:P1group', self.NAMESPACES):
    #                 #             section_title = self._get_text(p1group, './/ns0:Title')
    #                 #             p_number = self._get_text(p1group, './/ns0:P1/ns0:Pnumber')
                                
    #                 #             if not p_number:
    #                 #                 p_number = str(len(schedule_data['content']) + 1)
                                    
    #                 #             content = {
    #                 #                 'article_number': p_number,
    #                 #                 'title': section_title,
    #                 #                 'text': self.extract_article_text(p1group),
    #                 #                 'part_number': None,  # No Part for this content
    #                 #                 'part_title': None
    #                 #             }
    #                 #             schedule_data['content'].append(content)

    #                 if schedule_data['content']:
    #                     schedules.append(schedule_data)
    #                     self.logger.info(f"Extracted Schedule {number} ({schedule_title}) with {len(schedule_data['content'])} sections")
                            
    #             except AttributeError as e:
    #                 self.logger.warning(f"Skipping malformed schedule: {str(e)}")
    #                 continue
                        
    #         return schedules
                
    #     except Exception as e:
    #         self.logger.error(f"Error extracting schedules: {str(e)}")
    #         return []

    def _build_schedule_link(self, base_uri: str, schedule_number: str, part_info: Optional[PartInfo] = None) -> str:
        """
        Build the appropriate link for a schedule section, handling both parts and non-part structures.
        
        The method creates URLs in these formats:
        - Schedule with part: /uksi/YEAR/NUMBER/schedule/X/part/Y/made
        - Schedule without part: /uksi/YEAR/NUMBER/schedule/X/made
        
        Args:
            base_uri: The base legislation URI (e.g., https://www.legislation.gov.uk/uksi/2017/766)
            schedule_number: The schedule number
            part_info: Optional PartInfo object containing part number and title
            
        Returns:
            Complete URL string for the schedule section
        """
        if part_info and part_info.number:
            # Remove any "PART " prefix from the part number if it exists
            part_number = part_info.number.replace('PART ', '')
            return f"{base_uri}/schedule/{schedule_number}/part/{part_number}/made"
        else:
            return f"{base_uri}/schedule/{schedule_number}/made"

    def extract_schedules(self, root: ET.Element, config: ScheduleConfig, base_uri: str) -> List[Dict]:
        """Extract schedules based on user selection"""
        schedules = []
        
        try:
            for schedule in root.findall('.//ns0:Schedule', self.NAMESPACES):
                try:
                    schedule_number_elem = schedule.find('.//ns0:Number', self.NAMESPACES)
                    if schedule_number_elem is None:
                        continue
                    
                    number = self.clean_text(schedule_number_elem.text).replace('SCHEDULE ', '')
                    
                    if number not in config.selected_schedules or not config.selected_schedules[number]:
                        continue
                    
                    schedule_title = self._get_text(schedule, './/ns0:Title')
                    
                    schedule_data = {
                        'number': number,
                        'name': schedule_title,
                        'content': []
                    }
                    
                    schedule_body = schedule.find('.//ns0:ScheduleBody', self.NAMESPACES)
                    if schedule_body is None:
                        continue
                    
                    parts = schedule_body.findall('./ns0:Part', self.NAMESPACES)
                    
                    if parts:
                        # Pass base_uri to _process_schedule_with_parts
                        self._process_schedule_with_parts(parts, schedule_data, base_uri)
                    else:
                        # Pass base_uri to _process_schedule_without_parts
                        self._process_schedule_without_parts(schedule_body, schedule_data, base_uri)
                    
                    if schedule_data['content']:
                        schedules.append(schedule_data)
                        self.logger.info(f"Extracted Schedule {number} ({schedule_title}) with {len(schedule_data['content'])} sections")
                        
                except AttributeError as e:
                    self.logger.warning(f"Skipping malformed schedule: {str(e)}")
                    continue
                        
            return schedules
                
        except Exception as e:
            self.logger.error(f"Error extracting schedules: {str(e)}")
            return []

    # def extract_schedules(self, root: ET.Element, config: ScheduleConfig, base_uri: str) -> List[Dict]:
    #     """
    #     Extract schedules from legislation XML, handling both schedules with and without parts.
        
    #     This method processes each schedule in the XML document according to its structure:
    #     - For schedules with parts: extracts content preserving the part hierarchy
    #     - For schedules without parts: extracts content directly from the schedule body
        
    #     Args:
    #         root: The root XML element containing schedule data
    #         config: Configuration object containing user selections for schedule processing
            
    #     Returns:
    #         List of dictionaries containing processed schedule data
    #     """
    #     schedules = []
        
    #     try:
    #         # Find all schedule elements
    #         for schedule in root.findall('.//ns0:Schedule', self.NAMESPACES):
    #             try:
    #                 # Extract schedule number and validate it exists
    #                 schedule_number_elem = schedule.find('.//ns0:Number', self.NAMESPACES)
    #                 if schedule_number_elem is None:
    #                     self.logger.warning("Schedule found without number element - skipping")
    #                     continue
                    
    #                 number = self.clean_text(schedule_number_elem.text).replace('SCHEDULE ', '')
                    
    #                 # Check if this schedule was selected for processing
    #                 if number not in config.selected_schedules or not config.selected_schedules[number]:
    #                     continue
                    
    #                 # Extract schedule title
    #                 schedule_title = self._get_text(schedule, './/ns0:Title')
                    
    #                 schedule_data = {
    #                     'number': number,
    #                     'name': schedule_title,
    #                     'content': []
    #                 }
                    
    #                 # Find the schedule body - this is where all content lives
    #                 schedule_body = schedule.find('.//ns0:ScheduleBody', self.NAMESPACES)
    #                 if schedule_body is None:
    #                     self.logger.warning(f"Schedule {number} has no ScheduleBody - skipping")
    #                     continue
                    
    #                 # First check for parts directly under ScheduleBody
    #                 parts = schedule_body.findall('./ns0:Part', self.NAMESPACES)
                    
    #                 if parts:
    #                     # Process schedule with parts structure
    #                     self._process_schedule_with_parts(parts, schedule_data)
    #                 else:
    #                     # Process schedule without parts
    #                     self._process_schedule_without_parts(schedule_body, schedule_data)
                    
    #                 # Only add schedule if we found content
    #                 if schedule_data['content']:
    #                     schedules.append(schedule_data)
    #                     self.logger.info(
    #                         f"Extracted Schedule {number} ({schedule_title}) "
    #                         f"with {len(schedule_data['content'])} sections"
    #                     )
                    
    #             except AttributeError as e:
    #                 self.logger.warning(f"Error processing schedule: {str(e)}")
    #                 continue
                
    #     except Exception as e:
    #         self.logger.error(f"Error extracting schedules: {str(e)}")
            
    #     return schedules

    def _process_schedule_with_parts(self, parts: List[ET.Element], schedule_data: Dict, base_uri: str) -> None:
        """
        Process a schedule that contains parts, handling both P1group and direct P1 elements within each part.
        
        Args:
            parts: List of Part XML elements
            schedule_data: Dictionary to store the extracted content
        """
        for part in parts:
            part_number = self._get_text(part, './/ns0:Number')
            part_title = self._get_text(part, './/ns0:Title')
            
            if not (part_number and part_title):
                self.logger.warning(f"Part found without number or title - skipping")
                continue
            
            current_part = PartInfo(number=part_number, title=part_title)
            
            # Find both P1group elements and direct P1 elements
            all_elements = []
            for element in part:
                if element.tag.endswith('P1group') or element.tag.endswith('P1'):
                    all_elements.append(element)
            
            for element in all_elements:
                section_content = self._extract_p1group_content(element, len(schedule_data['content']))

                # Create the appropriate link for this section
                link = self._build_schedule_link(
                    base_uri=base_uri,
                    schedule_number=schedule_data['number'],
                    part_info=current_part
                )

                section_content.update({
                    'part_number': current_part.number,
                    'part_title': current_part.title,
                    'Link': link
                })
                schedule_data['content'].append(section_content)


    # def _process_schedule_without_parts(self, schedule_body: ET.Element, schedule_data: Dict, base_uri: str) -> None:
    #     """Process a schedule that doesn't contain parts"""
    #     all_elements = []
    #     for element in schedule_body:
    #         if element.tag.endswith('P1group') or element.tag.endswith('P1'):
    #             all_elements.append(element)
        
    #     for element in all_elements:
    #         section_content = self._extract_p1group_content(element, len(schedule_data['content']))
            
    #         # Create link for schedule without parts
    #         link = self._build_schedule_link(
    #             base_uri=base_uri,
    #             schedule_number=schedule_data['number'],
    #             part_info=None
    #         )
            
    #         section_content.update({
    #             'part_number': None,
    #             'part_title': None,
    #             'Link': link
    #         })
    #         schedule_data['content'].append(section_content)

    def _process_schedule_without_parts(self, schedule_body: ET.Element, schedule_data: Dict, base_uri: str) -> None:
        """
        Process a schedule that doesn't contain parts, handling both P1group and direct P1 elements.
        
        Args:
            schedule_body: ScheduleBody XML element
            schedule_data: Dictionary to store the extracted content
        """
        # Find both P1group elements and direct P1 elements
        p1groups = schedule_body.findall('./ns0:P1group', self.NAMESPACES)
        direct_p1s = schedule_body.findall('./ns0:P1', self.NAMESPACES)
        
        # Process all elements in order they appear in the document
        all_elements = []
        for element in schedule_body:
            if element.tag.endswith('P1group') or element.tag.endswith('P1'):
                all_elements.append(element)
        
        for index, element in enumerate(all_elements):
            # Create link for schedule without parts
            link = self._build_schedule_link(
                base_uri=base_uri,
                schedule_number=schedule_data['number'],
                part_info=None
            )

            section_content = self._extract_p1group_content(element, len(schedule_data['content']))
            section_content.update({
                'part_number': None,
                'part_title': None,
                'Link': link
            })
            schedule_data['content'].append(section_content)

    def _extract_p1group_content(self, element: ET.Element, content_count: int) -> Dict:
        """
        Extract content from either a P1group or direct P1 element.
        
        Args:
            element: XML element (either P1group or P1)
            content_count: Current count of content items
            
        Returns:
            Dictionary containing the extracted content
        """
        # Handle P1group structure
        if element.tag.endswith('P1group'):
            section_title = self._get_text(element, './/ns0:Title')
            p_number = self._get_text(element, './/ns0:P1/ns0:Pnumber')
        # Handle direct P1 structure
        else:
            section_title = ""  # Direct P1 elements may not have titles
            p_number = self._get_text(element, './/ns0:Pnumber')
        
        if not p_number:
            p_number = str(content_count + 1)
        
        return {
            'article_number': p_number,
            'title': section_title,
            'text': self.extract_article_text(element)
        }

    def extract_section_content(self, section: ET.Element) -> Dict:
        """Extract content from a section in a schedule"""
        try:
            return {
                'title': self._get_text(section, 'Title'),
                'text': [self.clean_text(text) 
                        for text in self.extract_article_text(section)]
            }
        except Exception as e:
            self.logger.warning(f"Error extracting section content: {str(e)}")
            return {'title': '', 'text': []}

# test_parser.py

def main():
    """Interactive testing script for the LegislationXMLParser"""
    parser = LegislationXMLParser()
    
    print("\nLegislation XML Parser Testing Script")
    print("=====================================")
    
    # Get input file
    xml_file = input("\nEnter the path to the XML file: ")
    
    try:
        print("\nStep 1: Parsing XML file...")
        # input("Press Enter to continue...")
        
        df = parser.parse_xml(xml_file)
        
        print("\nStep 2: Basic Information")
        # ordername = df.iloc[0]
        # print(f"Number of provisions found: {len(df)}")
        # print(f"Columns available: {', '.join(df.columns)}")
        # input("\nPress Enter to see the first article...")
        
        print("\nStep 3: First Article Details")
        first_article = df.iloc[0]
        print(f"\nTitle: {first_article['Title']}")
        print(f"Article Number: {first_article['Art']}")
        
        # Safely display link if available
        if 'Link' in df.columns:
            print(f"Link: {first_article['Link']}")
            
        print("\nFirst paragraph of text:")
        if isinstance(first_article['Text'], list) and len(first_article['Text']) > 0:
            print(first_article['Text'][0])
        elif isinstance(first_article['Text'], str):
            print(first_article['Text'])
            
        # input("\nPress Enter to see version information...")
        
        # print("\nStep 4: Version Information")
        # print(f"Is current version: {first_article.get('is_current', 'Not available')}")
        # print(f"Version date: {first_article.get('version_date', 'Not available')}")
        # if first_article.get('previous_version'):
        #     print(f"Previous version: {first_article['previous_version']}")
        # if first_article.get('next_version'):
        #     print(f"Next version: {first_article['next_version']}")
        
        input("\nPress Enter to save the data...")
        
        # Save to CSV
        output_file = f"parsed_legislation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")
        
    except LegislationParsingError as e:
        print(f"\nError parsing legislation: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
    
    print("\nTesting complete!")

if __name__ == "__main__":
    main()

import os
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

class ScholarshipScraper:
    def __init__(self):
        
        self.url = "https://www.scholars4dev.com/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_page_html(self, url):
        """Fetches raw HTML content from the specified URL safely."""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                return response.text
            else:
                print(f"[!] Failed to fetch page. Status Code: {response.status_code}")
                return None
        except Exception as e:
            print(f"[!] Connection Error: {e}")
            return None

    def clean_text(self, text):
        """Removes messy white spaces, newlines, and trailing characters."""
        if not text:
            return ""
        
        return re.sub(r'\s+', ' ', text).strip()

    def parse_deadline(self, deadline_text):
        """
        Attempts to parse messy string deadlines into standard YYYY-MM-DD format.
        Falls back to raw text if structure varies.
        """
        cleaned_date = self.clean_text(deadline_text.replace("Deadline:", ""))
        
        try:
            # Simple regex search to extract standard day Month year formats if present
            match = re.search(r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})', cleaned_date)
            if match:
                date_str = match.group(1)
                # Parse "27 May 2026" into a true datetime object
                dt = datetime.strptime(date_str, "%d %B %Y")
                return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
        
     
        return cleaned_date if cleaned_date else "Unknown/Variable"

    def scrape_scholarships(self):
        """Main pipeline execution method to scrape, clean, and structure data."""
        print(f"[*] Commencing Ingestion: Querying {self.url}...")
        html_content = self.fetch_page_html(self.url)
        
        if not html_content:
            return pd.DataFrame() # Return empty DataFrame on failure

        soup = BeautifulSoup(html_content, 'html.parser')
        scholarship_list = []

        listings = soup.find_all('div', class_='post')
        
        if not listings:
           
            listings = soup.find_all('div', class_='entry')

        for item in listings:
            
            title_tag = item.find('h2') or item.find('h1')
            if not title_tag or not title_tag.find('a'):
                continue
            
            title = self.clean_text(title_tag.find('a').text)
            link = title_tag.find('a')['href']

            post_content = item.find('div', class_='entry') or item
            paragraphs = post_content.find_all('p')
            
            description = ""
            raw_deadline = ""
            
            for p in paragraphs:
                p_text = p.text
                if "Deadline:" in p_text:
                    raw_deadline = p_text
                elif not p.find('a', class_='more-link'): # Ignore 'read more' boilerplate text anchors
                    description += p_text + " "

            
            final_description = self.clean_text(description)
            parsed_deadline = self.parse_deadline(raw_deadline)

            
            scholarship_data = {
                "Title": title,
                "URL": link,
                "Description": final_description,
                "Raw_Deadline": self.clean_text(raw_deadline.replace("Deadline:", "")),
                "Parsed_Deadline": parsed_deadline,
                "Ingestion_Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            scholarship_list.append(scholarship_data)

       
        df = pd.DataFrame(scholarship_list)
        print(f"[+] Successfully extracted and processed {len(df)} matching entities.")
        return df

if __name__ == "__main__":
    
    os.makedirs("data/raw", exist_ok=True)
    
    # Initialize and execute pipeline
    scraper = ScholarshipScraper()
    structured_df = scraper.scrape_scholarships()
    
    if not structured_df.empty:
        # Save output to local storage
        output_path = "data/raw/scraped_opportunities.csv"
        structured_df.to_csv(output_path, index=False)
        print(f"[✓] Pipeline complete. Clean dataset saved locally to: {output_path}")
        print("\nFirst few records preview:")
        print(structured_df[["Title", "Parsed_Deadline"]].head())
    else:
        print("[!] Execution halted: No records were processed.")
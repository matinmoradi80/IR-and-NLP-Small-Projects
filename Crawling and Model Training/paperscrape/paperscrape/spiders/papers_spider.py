import scrapy
from bs4 import BeautifulSoup
import re

class PaperParser:
    def __init__(self, soup):
        self.soup = soup

    def get_title(self):
        return self.soup.find('head').find('meta', {'name': 'citation_title'}).get('content')

    def get_id(self):
        match = re.match('Corpus ID: (\d+)', self.soup.find('li', {'data-test-id': 'corpus-id'}).string)
        return match.groups()[0] if match else None

    def get_abstract(self):
        return self.soup.find('meta', {'name': 'description'}).get('content')

    def get_publication_year(self):
        return int(self.soup.find('meta', {'name': 'citation_publication_date'}).get('content'))

    def get_authors(self):
        return ', '.join([tag.get('content') for tag in self.soup.find('head').findAll('meta', {'name': 'citation_author'})])

    def get_related_topics(self):
        return ', '.join([re.match('(.*) \(opens in a new tab\)', link.text.strip()).groups()[0]
                          for link in self.soup.find('div', {'id': 'paper-topics'}).find_all('a', {'class': 'paper-topics__topic-link'})])

    def get_citation_count(self):
        return int(self.soup.find('div', {'class': 'scorecard'}).find('span', {'class': 'scorecard-stat__headline__dark'}).text.strip().split()[0])

    def get_reference_count(self):
        return int(self.soup.find('div', {'id': 'cited-papers'}).find('h2', {'class': 'dropdown-filters__result-count__header dropdown-filters__result-count__citations'}).text.strip().split()[0])

    def get_references(self):
        return ', '.join([item.get('data-paper-id') for item in (self.soup.find('div', {'class': 'paper-detail-content-card result-page', 'data-test-id': 'reference'})
                                                                 .find_all('div', {'class': 'cl-paper-row citation-list__paper-row'})[:10])])
                                                                 
class PapersSpider(scrapy.Spider):
    name = 'papers'
    prof_names = ['Kasaei', 'Rabiee', 'Rohban', 'Sharifi','Soleymani']
    start_urls = []
    for pname in prof_names:
        with open(pname + '.txt', 'r') as file:
            for line in file:
                start_urls.append(line.replace("\n", ""))

    custom_settings = {
        'ITEM_COUNT_LIMIT': 40,
        'CONCURRENT_REQUESTS' : 1,
        'DOWNLOAD_DELAY': 15,
        'ّFEED_FORMAT': 'json',
        'FEED_URI': 'papers.json',
    }
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
  
    
    def parse(self, response):
        print(f"\033[91m **Response Title:** \033[0m")
        header = response.css('title')
        print(header)

        try:
          soup = BeautifulSoup(response.text, 'html.parser')
          paper_parser = PaperParser(soup)
          paper = {
              'Title': paper_parser.get_title(),
              'ID': paper_parser.get_id(),
              'Abstract': paper_parser.get_abstract(),
              'Publication Year': paper_parser.get_publication_year(),
              'Authors': paper_parser.get_authors(),
              'Related Topics': paper_parser.get_related_topics(),
              'Citation Count': paper_parser.get_citation_count(),
              'Reference Count': paper_parser.get_reference_count(),
              'References': paper_parser.get_references()
          }
          yield paper

          next_page_links = [
          'https://www.semanticscholar.org' + item.find('a', {'class': 'link-button--show-visited'}).get('href')
          for item in (soup.find(
            'div', {'class': 'paper-detail-content-card result-page', 'data-test-id': 'reference'})
            .find_all('div', {'class': 'cl-paper-row citation-list__paper-row'}) if soup else [])][:10]

          for next_page_link in next_page_links:
            yield scrapy.Request(url=next_page_link, callback=self.parse)

        except Exception as e:
          self.logger.error(f"An error occurred for this url {response.url} : {str(e)}")
          return
import codecs
import os
import urllib.parse
import urllib.request
import re
from argparse import ArgumentParser
from collections import defaultdict

from bs4 import BeautifulSoup

COMPANY_TYPES = [
    'Developer',
    'Developer and Publisher',
    'Mobile',
    'Online',
    'Organization',
    'Publisher',
    'Serious Games',
    'Virtual Reality'
]
MAX_COUNT = 100000
TIMEOUT = 1


def parse_number(s):
    matches = re.search('([0-9,\\.]+)', s)
    if matches is None:
        return None
    match = matches.group(1)
    return int(match.replace(',', '').replace('.', ''))


class CityInfoWebScraper:
    __slots__ = ['_info', '_timeout']

    def __init__(self, name, *, timeout=TIMEOUT):
        assert name
        assert timeout
        self._info = dict(city_name=name,
                          city_population=None)
        self._timeout = timeout
        self._scrape_info_from_web()

    def _scrape_info_from_web(self):
        print('trying to scrape city ({}) info from the web'.format(self._info['city_name']))
        url = 'https://en.wikipedia.org/wiki/{}'.format(urllib.parse.quote(self._info['city_name']))
        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as response:
                html = response.read()
        except:
            print('error accessing \'{}\''.format(url))
            return
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find(class_='infobox geography vcard')
        if table is None:
            return
        pop_str = None
        deep_search = False
        for tr_tag in table.find_all('tr'):
            tr_text = tr_tag.get_text()
            if 'Population' in tr_text:
                td_tag = tr_tag.find(name='td')
                if td_tag is None:
                    deep_search = True
                else:
                    pop_str = td_tag.get_text()
                    break
            elif deep_search and ('Urban' in tr_text or 'Metro' in tr_text or 'City'in tr_text or 'Total' in tr_text):
                td_tag = tr_tag.find(name='td')
                pop_str = td_tag.get_text()
                break
        if pop_str:
            self._info['city_population'] = parse_number(pop_str)

    def __getitem__(self, item):
        return self._info[item]

    def csv_fields(self):
        return ','.join([str(data) for data in self._info.keys()])

    def to_csv_str(self):
        return ','.join([str(data) for data in self._info.values()])


class CompanyInfoWebScraper:
    __slots__ = ['_info', '_city', '_timeout']

    def __init__(self, name, website, type_, city, *, timeout=TIMEOUT):
        assert name
        assert website
        assert type_
        assert city
        assert timeout
        self._city = city
        self._info = dict(company_name=name,
                          company_type=type_,
                          company_website=website,
                          could_access_company_website=None,
                          could_find_job_application=None)
        self._timeout = timeout
        self._scrape_info_from_web()

    def _scrape_info_from_web(self):
        print('trying to scrape company ({}) info from the web'.format(self._info['company_name']))
        try:
            with urllib.request.urlopen(self._info['website'], timeout=self._timeout) as response:
                html = response.read()
            self._info['could_access_company_website'] = True
        except:
            print('error accessing \'{}\''.format(self._info['company_website']))
            self._info['could_access_company_website'] = False
            return
        soup = BeautifulSoup(html, 'html.parser')
        if soup.find(text='Opening') or soup.find(text='Career') or soup.find(text='Job') or \
                soup.find(text='Apply'):
            self._info['could_find_job_application'] = True
        else:
            self._info['could_find_job_application'] = False

    def __getitem__(self, item):
        return self._info[item]

    def csv_fields(self):
        return '{},{}'.format(','.join([str(data) for data in self._info.keys()]), self._city.csv_fields())

    def to_csv_str(self):
        return '{},{}'.format(','.join([str(data) for data in self._info.values()]), self._city.to_csv_str())


def main():
    parser = ArgumentParser()
    parser.add_argument('--out', type=str, required=True)
    parser.add_argument('--country', type=str, required=True)
    parser.add_argument('--city', type=str, required=False, default='')
    parser.add_argument('--company_type', type=str, choices=COMPANY_TYPES, required=False, default='')
    parser.add_argument('--start', type=int, required=False, default=-1)
    parser.add_argument('--max_count', type=int, required=False, default=-1)
    parser.add_argument('--web_scrape_timeout', type=int, required=False, default=TIMEOUT)
    args = parser.parse_args()

    url = 'https://gamedevmap.com/index.php?' \
          'country={country}&' \
          'city={city}&' \
          'type={company_type}&' \
          'start={start}&' \
          'count={max_count}'.format(country=args.country,
                                     city=args.city,
                                     company_type=args.company_type,
                                     start=args.start if args.start >= 0 else 0,
                                     max_count=args.max_count if args.max_count > 0 else MAX_COUNT)
    print('accessing {}'.format(url))
    with urllib.request.urlopen(url) as response:
        html = response.read()
    city_infos = dict()
    company_infos = []
    soup = BeautifulSoup(html, 'html.parser')
    tr_tags = soup.find_all('tr', class_='row1') + soup.find_all('tr', class_='row2')
    print('found {} companies'.format(len(tr_tags)))
    company_type_count = dict()
    for i, tr_tag in enumerate(tr_tags):
        children = list(tr_tag.children)
        assert len(children) == 5
        name = children[0].get_text().strip()
        print('[{}/{}] processing company \'{}\''.format(i + 1, len(tr_tags), name))
        website = children[0].find('a').get('href').strip()
        type_ = children[1].get_text().strip()
        city_name = children[2].get_text().strip()
        if city_name not in city_infos:
            city_infos[city_name] = CityInfoWebScraper(city_name, timeout=args.web_scrape_timeout)
        # state = children[3].get_text().strip()
        # country = children[4].get_text().strip()
        company_infos.append(CompanyInfoWebScraper(name, website, type_, city_infos[city_name],
                                                   timeout=args.web_scrape_timeout))
        company_type_count[type_] = company_type_count.get(type_, 0) + 1

    stats = defaultdict(lambda: 0)
    if company_infos:
        out = args.out
        base, _ = os.path.splitext(out)
        with codecs.open('{}.csv'.format(base), 'w', 'utf-8') as csv_file:
            csv_file.write(company_infos[0].csv_fields() + '\n')
            for company_info in company_infos:
                csv_file.write(company_info.to_csv_str() + '\n')
                if company_info['could_access_company_website']:
                    stats['could_access_company_website'] += 1
                if company_info['could_find_job_application']:
                    stats['could_access_company_website'] += 1

    print('Summary:')
    print('- companies per type:')
    for company_type, count in company_type_count.items():
        print('{} {}(s) ({}%)'.format(
            count, 
            company_type, 
            count / len(tr_tags) * 100.0
        ))
    print('- accessible company websites: {}/{} ({}%)'.format(
        stats['could_access_company_website'],
        len(company_infos),
        stats['could_access_company_website'] / len(company_infos) * 100.0
    ))
    print('- job applications found: {}/{} ({}%)'.format(
        stats['could_access_company_website'],
        len(company_infos),
        stats['could_access_company_website'] / len(company_infos) * 100.0
    ))


if __name__ == '__main__':
    main()

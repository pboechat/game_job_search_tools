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
        self._info = dict(name=name,
                          population=None)
        self._timeout = timeout
        self._scrape_info_from_web()

    def _scrape_info_from_web(self):
        print(f'trying to scrape city ({self._info["name"]}) info from the web')
        url = f'https://en.wikipedia.org/wiki/{urllib.parse.quote(self._info["name"])}'
        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as response:
                html = response.read()
        except:
            print(f'error accessing \'{url}\'')
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
            elif deep_search and ('Urban' in tr_text or 'Total' in tr_text):
                td_tag = tr_tag.find(name='td')
                pop_str = td_tag.get_text()
                break
        if pop_str:
            self._info['population'] = parse_number(pop_str)

    def __getitem__(self, item):
        return self._info[item]

    def csv_fields(self):
        return ','.join([str(data) for data in self._info.keys()])

    def to_csv_str(self):
        return ','.join([str(data) for data in self._info.values()])


class CompanyInfoWebScraper:
    __slots__ = ['_info', '_city', '_timeout']

    def __init__(self, name, link, type_, city, *, timeout=TIMEOUT):
        assert name
        assert link
        assert type_
        assert city
        assert timeout
        self._city = city
        self._info = dict(name=name,
                          link=link,
                          type=type_,
                          accessible_website=None,
                          job_application_found=None)
        self._timeout = timeout
        self._scrape_info_from_web()

    def _scrape_info_from_web(self):
        print(f'trying to scrape company ({self._info["name"]}) info from the web')
        try:
            with urllib.request.urlopen(self._info['link'], timeout=self._timeout) as response:
                html = response.read()
            self._info['accessible_website'] = True
        except:
            print(f'error accessing \'{self._info["link"]}\'')
            self._info['accessible_website'] = False
            return
        soup = BeautifulSoup(html, 'html.parser')
        if soup.find(text='Opening') or soup.find(text='Career') or soup.find(text='Job') or \
                soup.find(text='Apply'):
            self._info['job_application_found'] = True
        else:
            self._info['job_application_found'] = False

    def __getitem__(self, item):
        return self._info[item]

    def csv_fields(self):
        return f'{",".join([str(data) for data in self._info.keys()])},{self._city.csv_fields()}'

    def to_csv_str(self):
        return f'{",".join([str(data) for data in self._info.values()])},{self._city.to_csv_str()}'


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
    print(f'accessing {url}')
    with urllib.request.urlopen(url) as response:
        html = response.read()
    city_infos = dict()
    company_infos = []
    soup = BeautifulSoup(html, 'html.parser')
    tr_tags = soup.find_all('tr', class_='row1') + soup.find_all('tr', class_='row2')
    print(f'found {len(tr_tags)} companies')
    company_type_count = dict()
    for i, tr_tag in enumerate(tr_tags):
        children = list(tr_tag.children)
        assert len(children) == 5
        name = children[0].get_text().strip()
        print(f'[{i + 1}/{len(tr_tags)}] processing company "{name}"')
        link = children[0].find('a').get('href').strip()
        type_ = children[1].get_text().strip()
        city_name = children[2].get_text().strip()
        if city_name not in city_infos:
            city_infos[city_name] = CityInfoWebScraper(city_name, timeout=args.web_scrape_timeout)
        # state = children[3].get_text().strip()
        # country = children[4].get_text().strip()
        company_infos.append(CompanyInfoWebScraper(name, link, type_, city_infos[city_name],
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
                if company_info['accessible_website']:
                    stats['accessible_websites'] += 1
                if company_info['job_application_found']:
                    stats['job_applications_found'] += 1

    print('Summary:')
    print('- companies per type:')
    for company_type, count in company_type_count.items():
        print(f'{count} {company_type}(s) ({count / len(tr_tags) * 100.0}%)')
    print(f'- accessible websites: '
          f'{stats["accessible_websites"]}/'
          f'{len(company_infos)} '
          f'({stats["accessible_websites"] / len(company_infos) * 100.0}%)')
    print(f'- job applications found: '
          f'{stats["job_applications_found"]}/'
          f'{len(company_infos)} '
          f'({stats["job_applications_found"] / len(company_infos) * 100.0}%)')


if __name__ == '__main__':
    main()

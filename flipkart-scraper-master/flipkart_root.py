from bs4 import BeautifulSoup as Bs
from pandas import DataFrame as df
import requests
import logging

logging.basicConfig(filename='logs', level=logging.DEBUG)


class Scrapper:
    URL = 'https://www.flipkart.com/search?q='
    PRODUCT_CLASS_DICT = {'name': '_3wU53n',
                          'rating': 'hGSR34',
                          'rating2': 'hGSR34 _1x2VEC',
                          'rating3': 'hGSR34 _1nLEql',
                          'specs': 'vFw0gD',
                          'price': '_1vC4OE _2rQ-NK',
                          'mrp': '_3auQ3N _2GcJzG', }
    BOX_PRODUCT_CLASS_DICT = {'name': '_2cLu-l',  # <a> class
                              'rating': 'hGSR34',
                              'rating2': 'hGSR34 _1x2VEC',
                              'rating3': 'hGSR34 _1nLEql',
                              'specs': '_1rcHFq',   # <div> class
                              'price': '_1vC4OE', }

    def __init__(self, searchterm):
        self.searchterm = searchterm
        self.url = self.URL + self.create_url(self.searchterm)

    def create_url(self, searchterm):
        string_list = searchterm.split(' ')
        new_string = ''
        for i in string_list:
            new_string = new_string + i + '+'
        return new_string[:-1]

    def initialize(self):  # main Url validation
        logging.info('Checking Url: ' + self.url)
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                logging.info('Url is Valid, initiating scraping')
                print('Scraping initiated for search: ', self.searchterm)
                return self.get_number_of_results(response)
            else:
                logging.error(response.status_code)
                print('Request timed out, Poor connection.Try again.')
        except ConnectionError:
            logging.error('Invalid Url or no connection')
            print('Request timed out, Poor connection.Try again.')
            exit()

    def get_number_of_results(self, response):
        raw_html = response.content
        soup = Bs(raw_html, 'html.parser')
        klass = '_2yAnYN'
        try:
            raw_results = soup.find('span', {'class': klass}).get_text()
            if raw_results is None:
                logging.error("No Results found for <h1> class: " + klass)
                exit()
            else:
                start = raw_results.index('of')
                end = raw_results.index('results')
                no_of_results = int(raw_results[start + 3:end - 1].replace(',', ''))
                logging.info('Number of results for ' + self.searchterm + ':' + str(no_of_results))
                if no_of_results > 10000:
                    print('Too many' + '(' + str(no_of_results) + ')results for ' + self.searchterm + '.\
 Please extend your search term.')
                    print('Do you still want to continue, it will take a lot of time.(Y/N)')
                    choice = input()
                    if choice == 'Y' or choice == 'y':
                        return self.get_max_page(response)
                    elif choice == 'N' or choice == 'n':
                        exit()
                    else:
                        print('invalid choice, exiting')
                        exit()
                else:
                    print('No of results: ', no_of_results)
                    return self.get_max_page(response)
        except AttributeError:
            logging.error("screen format different for this search result, cant continue" + self.searchterm)
            return self.handle_different_screen_format()

    def get_max_page(self, response):
        raw_html = response.content
        soup = Bs(raw_html, 'html.parser')
        klass = '_2zg3yZ'
        try:
            raw_results = soup.find('div', {'class': klass}).select_one('span').get_text()
            start = raw_results.index('of')
            no_of_pages = int(raw_results[start + 3:].replace(' ', ''))
        except AttributeError:
            no_of_pages = 1
            logging.info('Only first page found')
        return self.create_page_urls(no_of_pages)

    def create_page_urls(self, no_of_pages):
        pages_url_list = list()
        for i in range(1, no_of_pages + 1):
            url = self.url + '&page=' + str(i)
            pages_url_list.append(url)
        return self.validate_page_urls(pages_url_list)

    def validate_page_urls(self, pages_url_list):
        valid_page_url_list = list()
        for url in pages_url_list:
            logging.info('Checking page url: ' + url)
            for i in range(1, 4):
                try:
                    for j in range(1, 4):
                        response = requests.get(url)
                        if response.status_code == 200:
                            valid_page_url_list.append(url)
                            logging.info(url + ' is valid')
                            print(url + ' is valid')
                            break
                        else:
                            logging.error('Response: ' + str(response.status_code))
                            print('Retrying...' + str(j))
                            continue
                except:
                    logging.error('No connection')
                    print('Request not completed for ' + url + ', Retrying..' + str(i))
                    continue
                break
        if len(valid_page_url_list) is not None:
            return self.check_diplay_type(valid_page_url_list)
        else:
            print('No valid url found, exiting...')
            exit()

    def check_diplay_type(self, valid_page_url_list):
        # class = '_1HmYoV _35HD7C col-10-12' --> box format
        # _1HmYoV hCUpcT

        item = valid_page_url_list[0]
        response = requests.get(item)
        raw_html = response.content
        soup = Bs(raw_html, 'html.parser')
        try:
            for var in soup.find_all("div", class_='bhgxx2 col-12-12'):
                if var.find('a', {'class': '_2cLu-l'}) is not None:
                    logging.info('Box type screen structure found')
                    return self.get_product_info_box(valid_page_url_list)
                elif var.find('div', {'class': self.PRODUCT_CLASS_DICT['name']}) is not None:
                    return self.get_product_info(valid_page_url_list)
                else:
                    logging.error('screen type cannot be recognized')
        except AttributeError:
            logging.error('Wrong class name in check_display_type()')

    def get_product_info_box(self, valid_page_url_list):
        raw_name_list = list()
        raw_rating_list = list()
        raw_specs_list = list()
        raw_price_list = list()
        for item in valid_page_url_list:
            response = requests.get(item)
            raw_html = response.content
            soup = Bs(raw_html, 'html.parser')
            try:
                for var in soup.find_all("div", class_='bhgxx2 col-12-12'):
                    if var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating']}) is not None:
                        rating = var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating']}).get_text()
                        raw_rating_list.append(rating)
                    elif var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating2']}) is not None:
                        rating = var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating2']}).get_text()[:-2]
                        raw_rating_list.append(float(rating))
                    elif var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating3']}) is not None:
                        rating = var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['rating3']}).get_text()[:-2]
                        raw_rating_list.append(float(rating))
                    else:
                        rating = 0
                        raw_rating_list.append(rating)
                    if var.find('a', {'class': self.BOX_PRODUCT_CLASS_DICT['name']}) is None:
                        raw_name_list.append(None)
                    else:
                        name = var.find('a', {'class': self.BOX_PRODUCT_CLASS_DICT['name']}).get_text()
                        raw_name_list.append(name)
                    if var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['specs']}) is None:
                        raw_specs_list.append(None)
                    else:
                        specs = var.find('div', {'class': self.BOX_PRODUCT_CLASS_DICT['specs']}).get_text()
                        raw_specs_list.append(specs)
                    if var.find("div", class_=self.BOX_PRODUCT_CLASS_DICT['price']) is None:
                        raw_price_list.append(None)
                    else:
                        price = var.find("div", class_=self.BOX_PRODUCT_CLASS_DICT['price']).get_text()[1:].replace(',', '')
                        raw_price_list.append(int(price))
                print('Scraping...please wait...')
            except AttributeError:
                print('Class name is different')
        df1 = df({'NAME': raw_name_list, 'RATING': raw_rating_list, 'SPECS': raw_specs_list, 'PRICE': raw_price_list})
        df1 = df1.dropna()
        print('No of valid products fetched: ' + str(df1.shape[0]))
        print('Thank-you from danish jain.')
        return df1

    def get_product_info(self, valid_page_url_list):
        raw_name_list = list()
        raw_rating_list = list()
        raw_specs_list = list()
        raw_price_list = list()
        for item in valid_page_url_list:
            response = requests.get(item)
            raw_html = response.content
            soup = Bs(raw_html, 'html.parser')
            try:
                for var in soup.find_all("div", class_='bhgxx2 col-12-12'):
                    if var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating']}) is not None:
                        rating = var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating']}).get_text()
                        raw_rating_list.append(rating)
                    elif var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating2']}) is not None:
                        rating = var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating2']}).get_text()[:-2]
                        raw_rating_list.append(float(rating))
                    elif var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating3']}) is not None:
                        rating = var.find('div', {'class': self.PRODUCT_CLASS_DICT['rating3']}).get_text()[:-2]
                        raw_rating_list.append(float(rating))
                    else:
                        rating = 0
                        raw_rating_list.append(rating)
                    if var.find('div', {'class': self.PRODUCT_CLASS_DICT['name']}) is None:
                        raw_name_list.append(None)
                    else:
                        name = var.find('div', {'class': self.PRODUCT_CLASS_DICT['name']}).get_text()
                        raw_name_list.append(name)
                    if var.find('ul', {'class': self.PRODUCT_CLASS_DICT['specs']}) is None:
                        raw_specs_list.append(None)
                    else:
                        specs = var.find('ul', {'class': self.PRODUCT_CLASS_DICT['specs']}).get_text()
                        raw_specs_list.append(specs)
                    if var.find("div", class_=self.PRODUCT_CLASS_DICT['price']) is None:
                        raw_price_list.append(None)
                    else:
                        price = var.find("div", class_=self.PRODUCT_CLASS_DICT['price']).get_text()[1:].replace(',', '')
                        raw_price_list.append(int(price))
                print('Scraping...please wait...')
            except AttributeError:
                print('Class name is different')
        df1 = df({'NAME': raw_name_list, 'RATING': raw_rating_list, 'SPECS': raw_specs_list, 'PRICE': raw_price_list})
        df1 = df1.dropna()
        print('No of valid products fetched: ' + str(df1.shape[0]))
        print('Thank-you from project owner of ONEFORALL.')
        
        return df1

    def handle_different_screen_format(self):
        print('Screen format is different, this functionality will soon be incorporated')

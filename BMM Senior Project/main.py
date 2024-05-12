from selenium import webdriver
from time import sleep
import yaml as y
import os
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
import json
import tld

class EcommerceScraper:
    def __init__(self, url, reviews=True):
        self.scrollScript = "window.scrollTo({top:document.documentElement.scrollHeight, behavior: 'smooth'});"
        self.is_scroll = True
        self.reviews = reviews
        options = webdriver.ChromeOptions()
        # Uncomment the line below if you want to run Chrome in headless mode
        # options.add_argument('--headless')
        options.add_argument('--disable-logging')
        self.driver = webdriver.Chrome(chrome_options=options)
        name = tld.get_tld(url, as_object=True).domain
        self.conf = self.get_config(name)
        self.cconf = self.get_config('common')
        self.scroll = True
        self.driver.get(url)
        self.driver.set_window_size(1024, 768)

    def get_config(self, site):
        dir = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir, "config.yaml")) as yaml_file:
            try:
                conf = y.load(yaml_file, Loader=y.FullLoader)
            except y.YAMLError as exc:
                print(exc, 'inside loading yaml')
        return conf.get(site)

    def search_product(self, product):
        url_page_lst = []
        driver = self.driver
        num_pages_id = '//*[@class="a-pagination"]/li[6]'
        # Handling close button if present
        close_btn = driver.find_elements_by_xpath("//button[contains(@class, 'close')]")
        for el in close_btn[::-1]:
            try:
                el.click()
                driver.implicitly_wait(5)
            except Exception as e:
                pass

        if 'search' in self.conf.keys():
            search_id = self.conf.get('search')['xpath']
        else:
            search_id = self.cconf.get('search')['xpath']

        search_bar = driver.find_element_by_xpath(search_id)
        search_bar.click()
        search_bar.send_keys(product)
        search_bar.send_keys(Keys.RETURN)
        driver.implicitly_wait(5)

        page_no = 1
        next_btn_xpath = self.conf.get('next')['xpath']

        # Loop through the pages to extract URLs
        for page in range(int(page_no)):
            try:
                url_page_lst.append(driver.current_url)
                try:
                    driver.find_element_by_xpath(next_btn_xpath).click()
                except Exception as e:
                    driver.implicitly_wait(10)
            except Exception as e:
                url_page_lst = url_page_lst[:len(url_page_lst) - 1]
        self.url_page_lst = url_page_lst

    def extract_product_url_lst(self):
        url_product_lst = []
        driver = self.driver
        outer_envelope_xpath = self.conf.get('outer_envelope')['xpath']
        inner_envelope_xpath = self.conf.get('inner_envelope')['xpath']

        # Loop through the pages to extract product URLs
        for url in self.url_page_lst:
            driver.get(url)
            driver.implicitly_wait(5)
            if self.is_scroll:
                driver.execute_script(self.scrollScript)
                sleep(2)
                driver.implicitly_wait(5)
            outer_envelope_el = driver.find_elements_by_xpath(outer_envelope_xpath)
            inner_envelope_el = driver.find_elements_by_xpath(inner_envelope_xpath)

            for idx, el in enumerate(inner_envelope_el):
                url_product_lst.append(el.find_element_by_tag_name('a').get_attribute("href"))
        self.url_product_lst = url_product_lst

    def extract_product_details(self):
        url_product_lst = self.url_product_lst
        driver = self.driver
        conf = self.conf['product']
        products = []

        # Loop through each product URL to extract details
        for url in self.url_product_lst:
            driver.get(url)
            driver.implicitly_wait(5)

            if self.is_scroll:
                driver.execute_script(self.scrollScript)
                sleep(1)
                driver.implicitly_wait(5)

            for key in conf.keys():
                # Extract text type data
                if conf[key]['type'] == 'text':
                    if 'special' in conf[key].keys():
                        xpath = conf[key]['special']['xpath']
                    else:
                        xpath = conf[key]['xpath']
                    try:
                        product[key] = driver.find_element_by_xpath(xpath).text
                    except Exception as e:
                        product[key] = ''
                # Extract list type data
                elif 'list' in conf[key]['type']:
                    if 'special' in conf[key].keys():
                        lst = conf[key]['special']
                    else:
                        lst = conf[key]['xpath']
                    for itm in lst:
                        xpath = itm['xpath']
                        try:
                            if key not in product.keys():
                                product[key] = []
                            product[key].append(driver.find_element_by_xpath(xpath).text)
                        except Exception as e:
                            pass
                # Extract review data
                elif conf[key]['type'] == 'reviews':
                    product[key] = []
                    if self.reviews:
                        try:
                            clicks = conf[key]['click']['xpath']
                            if 'list-and' in conf[key]['click']['type']:
                                for click in clicks:
                                    driver.find_element_by_xpath(click).click()
                                    driver.implicitly_wait(5)
                            else:
                                driver.find_element_by_xpath(clicks).click()
                                driver.implicitly_wait(5)
                            driver.implicitly_wait(5)
                            els = conf[key]['review']
                            while 1:
                                try:
                                    elements = driver.find_elements_by_xpath(
                                        conf[key]['inner_envelope']['xpath'])
                                    for idx, element in enumerate(elements):
                                        temp = {}
                                        for el in els:
                                            xpath = conf[key]['review'][el]['xpath']
                                            temp[el] = BeautifulSoup(
                                                driver.find_elements_by_xpath(xpath)[idx].get_attribute(
                                                    'outerHTML')).text.strip()
                                        product[key].append(temp)
                                    nxt = driver.find_element_by_xpath(conf[key]['next']['xpath']).click()
                                    driver.implicitly_wait(5)
                                except Exception as e:
                                    break

                        except Exception as e:
                            print(f'Error capturing all reviews: {e}')
                            product[key] = {}

            products.append(product)

        self.products = products

    def get_product(self):
        with open("products.json", "w") as f:
            json.dump(self.products, f)

    def get_url_product_lst(self):
        return self.url_product_lst

    def get_url_page_lst(self):
        return self.url_page_lst

# Instantiate the class with the URL
url = 'https://kaystore.com'
amazon = EcommerceScraper(url)

# Search for a product
product = 'laptop'
amazon.search_product(product)

# Extract product URLs
amazon.extract_product_url_lst()

# Extract product details
amazon.extract_product_details()

# Write product details to JSON file
amazon.get_product()

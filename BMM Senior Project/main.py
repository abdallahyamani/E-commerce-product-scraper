from selenium import webdriver
from time import sleep
import yaml as y
import os 
from bs4 import BeautifulSoup
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from selenium.webdriver.common.keys import Keys
import json
import tld

class EcommerceScraper():
    def __init__(self, url, reviews= True):
        self.scrollScript="window.scrollTo({top:document.documentElement.scrollHeight, behavior: 'smooth'});"
        self.is_scroll= True
        self.reviews= reviews
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless') 
        options.add_argument('--disable-logging') 
        driver= webdriver.Chrome(chrome_options=options)
        name= tld.get_tld(url, as_object=True).domain
        self.conf= self.get_config(name)
        self.cconf= self.get_config('common')
        self.scroll= True
        driver.get(url)        
        driver.set_window_size(1024, 768)
        self.driver= driver        

    def get(self, url):
        self.driver.get(url)
        return driver

    def search_product(self, product):
        url_page_lst= []
        driver= self.driver
        num_pages_id= '//*[@class="a-pagination"]/li[6]'
        if 'search' in self.conf.keys():
            kwargs= {
                'search_id': self.conf.get('search')['xpath'],
            }  
        else:
            kwargs= {
                'search_id': self.cconf.get('search')['xpath'],
            }              
        search_id= kwargs['search_id']      
        close_btn= driver.find_elements_by_xpath("//button[contains(@class, 'close')]")
        for el in close_btn[::-1]:
            try:
                print(el.get_attribute("outerHTML"), el.is_displayed())
                el.click()
                driver.implicitly_wait(5)
            except Exception as e:
                pass
        
        search_bars= driver.find_elements_by_xpath(search_id)
        for search_bar in search_bars:
            print(search_bar)
            if search_bar.is_displayed():
                break
            
        print('*'*200, search_bar.get_attribute("outerHTML"), search_bar.is_displayed(),'*'*200)
        search_bar.click()
        search_bar.send_keys(product)
        search_bar.send_keys(Keys.RETURN)
        driver.implicitly_wait(5)

        page_no= 1
        next= self.conf.get('next')['xpath']
        if self.is_scroll:
            driver.execute_script(self.scrollScript) 
            driver.implicitly_wait(20)
            sleep(2)

        for page in range(int(page_no)):
            try:
                url_page_lst.append(driver.current_url)
                try:
                    driver.find_element_by_xpath(next).click()
                except Exception as e:
                    driver.implicitly_wait(10)
            except Exception as e:
                url_page_lst= url_page_lst[:len(url_page_lst)-1] 
        self.url_page_lst=  url_page_lst

    def extract_product_url_lst(self):
        url_product_lst= []
        driver= self.driver
        
        kwargs= {
            'outer_envelope': self.conf.get('outer_envelope')['xpath'],
            'inner_envelope': self.conf.get('inner_envelope')['xpath']
        }

        outer_envelope= kwargs['outer_envelope']
        inner_envelope= kwargs['inner_envelope']
        for url in self.url_page_lst:
            driver.get(url)
            driver.implicitly_wait(5)
            if self.is_scroll:
                driver.execute_script(self.scrollScript) 
                sleep(2)
                driver.implicitly_wait(5)
            outer_envelope_el= driver.find_elements_by_xpath(outer_envelope)
            inner_envelope_el= driver.find_elements_by_xpath(inner_envelope)
            print(len(inner_envelope_el))
            
            for idx, el in enumerate(inner_envelope_el):

                print( el.find_element_by_tag_name('a').get_attribute("href"))
                url_product_lst.append(el.find_element_by_tag_name('a').get_attribute("href"))
        self.url_product_lst=  url_product_lst       

    def extract_product_details(self):
        url_product_lst= self.url_product_lst
        driver= self.driver
        conf= self.conf['product']
        product={}
        products= []
        for url in self.url_product_lst:
            driver.get(url)
            driver.implicitly_wait(5)

            if self.is_scroll: 
                driver.execute_script(self.scrollScript) 
                sleep(1)
                driver.implicitly_wait(5)
            func= driver.find_element_by_xpath

            for key in conf.keys():
                if conf[key]['type']=='text':
                    if 'special' in conf[key].keys():
                        xpath= conf[key]['special']['xpath']
                        click= conf[key]['special'].get('click', '')
                    else:
                        xpath= conf[key]['xpath']
                        click= ''
                    try:
                        if click!='':
                            element= driver.find_element_by_xpath(xpath).click()
                            driver.implicitly_wait(5)
                            sleep(1)
                        product[key]= func(xpath).text
                    except Exception as e:
                        product[key]= ''
                                
                elif 'list' in conf[key]['type']: 
                    print('list')
                    if 'special' in conf[key].keys():
                        lst= conf[key]['special']
                    else:
                        lst= conf[key]['xpath']
                    for idx, itm in enumerate(lst):
                        # try: 
                            if 'special' in conf[key].keys():
                                xpath= itm['xpath']
                                click= itm.get('click', '')
                            else:
                                xpath= itm
                                click= ''

                            if click!='':
                                element= driver.find_element_by_xpath(click).click()
                                driver.implicitly_wait(5)
                                sleep(1)
                            if 'or' in conf[key]['type']:
                                try:
                                    product[key]= func(xpath).text
                                    break
                                except Exception as e:
                                    product[key]= ''
                            elif 'and' in conf[key]['type']:
                                if key not in product.keys():
                                    product[key]= []
                                product[key].append(func(xpath).text)
                elif conf[key]['type']=='reviews':
                    product[key]= []
                    if self.reviews:
                        try:
                            clicks= conf[key]['click']['xpath']
                            if 'list-and' in conf[key]['click']['type']:
                                for click in clicks:
                                    element= driver.find_element_by_xpath(click).click()
                                    driver.implicitly_wait(5)
                            else:
                                element= driver.find_element_by_xpath(clicks).click()
                                driver.implicitly_wait(5)                          
                            driver.implicitly_wait(5)
                            els= conf[key]['review']
                            while 1:
                                try:
                                    elements= driver.find_elements_by_xpath(conf[key]['inner_envelope']['xpath'])
                                    print([e for e in elements])
                                    for idx, element in enumerate(elements):
                                        temp= {}
                                        for el in els:
                                            xpath= conf[key]['review'][el]['xpath']
                                            
                                            temp[el]= BeautifulSoup(driver.find_elements_by_xpath(xpath)[idx].get_attribute('outerHTML')).text.strip()   
                                        product[key].append(temp)
                                    
                                    nxt= func(conf[key]['next']['xpath']).click()
                                    driver.implicitly_wait(5)
                                except Exception as e:
                                    break
                        
                        except Exception as e:
                            print(f'Error capturing all reviews: {e}')
                            product[key]= {}
                    
                    
            print(product)
            products.append(product)
            
        self.products=  products   
    @staticmethod
    def get_config(site):
        dir= os.path.dirname(os.path.realpath(__file__))
        # confdir= 'config' 
        with open(os.path.join(dir,"config.yaml")) as yaml_file:
            try:
                conf= y.load(yaml_file, Loader=y.FullLoader)
            except y.YAMLError as exc:
                print(exc, 'inside loading yaml')    
        return conf.get(site)

    def get_product(self):
        with open(r'C:\Users\Abed\BMM Senior Project\json.txt', "w") as f:
            json.dump(self.products, f)
    
    
    def get_url_product_lst(self):
        return self.url_product_lst

    def get_url_page_lst(self):
        return self.url_page_lst
    def get_driver(self):
        return self.driver
    def set_driver(self, driver):
        self.driver= driver
    def set_url_product_lst(self, url_product_lst):
        self.url_product_lst= url_product_lst
    def set_url_page_lst(self, url_page_lst):
        self.url_page_lst= url_page_lst
    




# %%
# url= 'https://www.bestbuy.com/?intl=nosplash'
url= 'https://kaystore.com'
#url= r'http://www.amazon.com'
# amazon= BestBuyScraper(url)
amazon= EcommerceScraper(url)


product= 'laptop'
amazon.search_product(product)
amazon.extract_product_url_lst()
amazon.extract_product_details()
amazon.url_product_lst
amazon.url_page_lst

print(amazon.get_product())


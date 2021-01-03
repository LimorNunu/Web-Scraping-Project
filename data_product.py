from html_soup import Html_soup
from bs4 import BeautifulSoup as bs
import configuration as cfg
import requests
from tqdm import tqdm
import logging
from exchange_api import exchange_rate, date_exchange_rate


class Data_product:
    @staticmethod
    def soup_find(soup, s_type, class_name):
        """
        :param soup: soup of the page
        :param s_type: string of div or span
        :param class_name: string of the class name
        :return: text of the wanted class in the soup
        """
        return soup.find(s_type, {cfg.CLASS: class_name}).text

    @staticmethod
    def find_all(soup, class_name):
        """
        :param soup: soup of the page
        :param class_name: string of the class name
        :return: text of the wanted elements of the class in the soup
        """
        return soup.find_all(cfg.DIV, {cfg.CLASS: class_name})

    @staticmethod
    def get_data(url, section):
        """
        :param url: url address of the product
        :return: dict of all the info of the product,
                 using the get_html function to get the soup of the url
        """

        soup = Html_soup.get_soup(url)
        prod_dict = {}

        # adding ID for the product:
        prod_dict[ID] = Data_product.soup_find(soup, cfg.DIV, cfg.CLASS_ID).strip().split()[cfg.ID_SPLIT_NUM]

        # adding price for the product:
        prod_price = float(Data_product.soup_find(soup, cfg.DIV, cfg.CLASS_PRICE).split(cfg.PRICE_SPLIT_SIGN)[cfg.PRICE_SPLIT_NUM].strip())
        prod_dict[cfg.PRICE] = prod_price

        # adding average rate for the product:
        prod_dict[cfg.RATE] = float(Data_product.soup_find(soup, cfg.DIV, cfg.CLASS_RATE).strip())

        # adding reviews amount for the product:
        prod_dict[cfg.RVW_AMOUNT] = Data_product.soup_find(soup, cfg.SPAN, cfg.CLASS_RVW_AMOUNT).strip().split()[cfg.RVW_AMNT_SPLIT_NUM]

        # adding the percentage of product fit to size:
        for sz in Data_product.find_all(soup, cfg.CLASS_FIT):
            prod_dict[sz.text.split(cfg.FIT_SPLIT_TYPE)[cfg.FIT_FIRST_SPLIT_NUM]] = \
                sz.text.split(cfg.FIT_SPLIT_TYPE)[cfg.FIT_SEC_SPLIT_NUM]

        # adding the description of the product:
        for item in Data_product.find_all(soup, cfg.CLASS_DESCRIPTION):
            prod_dict[item.text.split(cfg.DESC_SPLIT_TYPE)[cfg.DESC_FIRST_SPLIT_NUM].strip()] = \
                item.text.split(cfg.DESC_SPLIT_TYPE)[cfg.DESC_SEC_SPLIT_NUM].strip()

        # adding the price and date from the exchange_api file
        prod_dict[cfg.PRICE_EXCHANGE] = round(exchange_rate * prod_price, cfg.ROUND_PRICE_EX)
        prod_dict[cfg.DATE_EXCHANGE] = date_exchange_rate

        # adding product_type by the section:
        prod_dict[cfg.PRODUCT_TYPE] = section
        return prod_dict

    @staticmethod
    def product_info(url_choice, num_of_products, section):
        """
        :param url_choice: url of the chosen product (the page of the products)
        :param num_of_products: number of products to scrap
        :param section: chosen section of product (dresses/tops/swimwear)
        :return: products list (of dictionaries), and the chosen section
        """

        products_list = []      # get dict for each product
        total_url_list = []     # get all products url

        for page in tqdm(range(1, cfg.NUMBER_OF_PAGES)):
            # changing the pages
            url_page = url_choice + cfg.PAGE.format(page)

            # create url addresses for all the dresses products in the page
            soup = bs(requests.get(url_page).content, cfg.HTML_PRS)
            prod = soup.findAll(cfg.URL_FIND_TYPE, href=True)

            products_url_list = []
            for address in prod:
                temp = (str(address).split(cfg.URL_SPLIT_SIGN))[cfg.TEMP_SPLIT_NUM]
                url_prod = temp.split(cfg.URL_PROD_SPLIT_SIGN)[cfg.URL_PROD_SPLIT_NUM].strip()
                if url_prod.endswith(cfg.HTML_END):
                    products_url_list.append(cfg.URL + url_prod)

            # list of url for each product
            for url1 in products_url_list[cfg.FROM: cfg.TO]:
                total_url_list.append(url1)

        total_url_list = list(set(total_url_list))
        # the first url is the main page of all dresses, so the list start from the 1st item

        logging.basicConfig(format=cfg.LOGGING_FORMAT,
                            filename=cfg.LOGGING_FILE_NAME, filemode=cfg.LOGGING_FILE_MODE)
        logger = logging.getLogger()
        logger.setLevel(logging.NOTSET)

        # get html and then the info of each product
        for product in tqdm(total_url_list[:num_of_products]):
            try:
                products_list.append(Data_product.get_data(product, section))
            except AttributeError:
                logger.warning(cfg.LOGGING_ATT_ERROR.format(product))
                pass
            except ValueError:
                logger.warning(cfg.LOGGING_VAL_ERROR.format(product))
                pass

        return products_list, section


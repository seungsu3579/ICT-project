import os
import time
import re
import random
from PIL import Image
import requests
import urllib.request
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from argparse import ArgumentParser


# option
parser = ArgumentParser()
parser.add_argument("-p", "--num_page", type=int, help="number of page to crawl")
parser.add_argument(
    "-c",
    "--all_category",
    type=str,
    nargs="+",
    help="category which you want to crawl  >  상의  아우터  원피스  바지  스커트  가방  \n스니커즈  신발  시계  모자  스포츠용품  \n레그웨어속옷  안경  액세서리  디지털테크  \n생활취미예술  뷰티  반려동물  책음악티켓",
)
parser.add_argument(
    "-f", "--folder_path", type=str, help="where to store crawled image"
)
parser.add_argument(
    "-d", "--driver_path", type=str, required=True, help="your chrome driver path"
)


class musinsa_crawler:
    def __init__(self, driver_path=None, folder_path="."):
        self.driver_start(driver_path)
        self.category = self.get_category_data()
        self.folder_path = folder_path

    def driver_start(self, driver_path=None):
        if driver_path == None:
            driver_path = "/Users/seungsu/Desktop/YBIGTA/chromedriver.exe"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("window-size=1920x1080")
        chrome_options.add_argument("headless")
        try:
            self.driver = webdriver.Chrome(driver_path, options=chrome_options)
        except:
            print("\x1b[1;31mError : You should give driver_path option\x1b[1;m")
        self.driver.implicitly_wait(3)

    def get_category_data(self):
        """
        <Get Musinsa Category Data>
        """
        self.driver.get("https://store.musinsa.com/app/")
        all_nav = self.driver.find_element_by_css_selector("nav.nav_menu")
        navs = all_nav.find_elements_by_css_selector("div.nav_category")
        category = {}
        for nav in navs[1:]:
            cat = {}
            big = nav.find_element_by_css_selector(
                "div.nav_menu_title"
            ).find_element_by_css_selector("a")
            big.click()
            big_cat_name = big.find_element_by_css_selector(
                "strong.title"
            ).text.replace("/", "")
            ll = nav.find_element_by_css_selector("div.item_sub_menu")
            uls = ll.find_elements_by_css_selector("ul")
            for ul in uls:
                al = ul.find_elements_by_css_selector("li")
                for a in al:
                    m = a.find_element_by_css_selector("a")
                    h = m.get_attribute("href")
                    exp = re.compile("[가-힣\s/]*")
                    title = exp.findall(m.text)[0].strip(" ").replace("/", " ")
                    cat[title] = h
            category[big_cat_name] = cat
        return category

    def check_directory(self, category_name):
        """
        category_name (str): Category name
        """
        try:
            os.mkdir(f"{self.folder_path}/{category_name}/")
            print(f"\x1b[1;32m  {category_name} Directory is created!\x1b[1;m")
        except:
            print(f"\x1b[1;35m  {category_name} Directory exist!\x1b[1;m")

    def getBSobj(self, category_id, page=1):
        """
        <Get BS object with fake header>
        page        (int): how many page crawling   | Default : 1
        category_id (str): Sub Category ID
        """
        url = f"https://store.musinsa.com/app/items/lists/{category_id}/?category=&d_cat_cd={category_id}&u_cat_cd=&brand=&sort=pop&sub_sort=&display_cnt=90&page={str(page)}&page_kind=category&list_kind=small&free_dlv=&ex_soldout=&sale_goods=&exclusive_yn=&price=&color=&a_cat_cd=&sex=&size=&tag=&popup=&brand_favorite_yn=&goods_favorite_yn=&blf_yn=&campaign_yn=&price1=&price2=&brand_favorite=&goods_favorite=&chk_exclusive=&chk_sale=&chk_soldout="
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        html = session.get(url, headers=headers).content
        bsObj = bs(html, "html.parser")
        return bsObj

    # 한 페이지 크롤러
    def crawl_page(self, bsObj, category_name, sub_name):
        """
        <Page Crawler>
        bsObj       (bs4Obj): BS object that contains page where you want to crawl
        category_name  (str): Category name
        sub_name       (int): Sub Category name
        """
        body = bsObj.find("ul", {"class": "snap-article-list"})
        all_items = body.find_all("li", {"class": "li_box"})
        for li in all_items:
            a = li.find("a", {"class": "img-block"})
            id = a["href"].lstrip("/app/product/detail/").rstrip("/0")
            img = "http:" + a.find("img")["data-original"]
            image = urllib.request.urlretrieve(
                img,
                f"{self.folder_path}/{category_name}/{category_name}_{sub_name}_{id}.png",
            )
            # image resize
            image = Image.open(
                f"{self.folder_path}/{category_name}/{category_name}_{sub_name}_{id}.png"
            )
            resize_img = image.resize((125, 125))
            resize_img.save(
                f"{self.folder_path}/{category_name}/{category_name}_{sub_name}_{id}.png"
            )

    # sub category 별 크롤러
    def crawl_SubCategory(self, main, sub, page=1):
        """
        <Sub Category Crawler>
        main (str): main category
        sub  (str): sub category
        page (int): how many page crawling   | Default : 1
        """
        category_id = self.category[main][sub].lstrip(
            "https://store.musinsa.com/app/items/lists/"
        )

        bsObj = self.getBSobj(page=1, category_id=category_id)
        total_page = bsObj.find("span", {"class": "totalPagingNum"}).text.strip(" ")
        if page > int(total_page):
            page = int(total_page)

        for p in range(1, int(page + 1)):
            print(f"CRAWLING\t{main}\t>\t{sub} \t\t page = {p}")
            bsObj = self.getBSobj(page=p, category_id=category_id)
            self.crawl_page(bsObj, category_name=main, sub_name=sub)
            rand_time = random.random() * 2
            time.sleep(rand_time)

    def crawl_AllCategory(self, categories=None, page=1):
        """
        <All Category Crawler>
        categories (list): main category            | Default : None (crawl all categories)
        page        (int): how many page crawling   | Default : 1
        """
        if categories == None:
            for category_name, contents in self.category.items():
                self.check_directory(category_name=category_name)
                for sub_category_name in contents.keys():
                    self.crawl_SubCategory(
                        main=category_name, sub=sub_category_name, page=page
                    )
                    print(
                        f"\x1b[1;32mCOMPLETE\x1b[1;m\t{category_name} > {sub_category_name}"
                    )
        else:
            for category_name in categories:
                self.check_directory(category_name=category_name)
                for sub_category_name in self.category[category_name].keys():
                    self.crawl_SubCategory(
                        main=category_name, sub=sub_category_name, page=page
                    )
                    print(
                        f"\x1b[1;32mCOMPLETE\x1b[1;m\t{category_name} > {sub_category_name}"
                    )


if __name__ == "__main__":
    args = parser.parse_args()

    crawler = musinsa_crawler(args.driver_path, args.folder_path)

    crawler.crawl_AllCategory(
        categories=args.all_category, page=args.num_page,
    )

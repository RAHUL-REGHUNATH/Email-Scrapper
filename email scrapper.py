# Import modules
import requests
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import re
import requests.exceptions
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
import urllib.request
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import sys

# Initialising list and variables
count = 1
search_results = []
lists = []
words = ['contact', 'contact-us']


def htmlPageRead(url):
    try:
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)
        driver.get(url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var "
                              "lenOfPage=document.body.scrollHeight;return lenOfPage;")
        time.sleep(3)
        content = driver.page_source
        driver.quit()
        return content
    except:
        pass


# EmailsLeechFunction
def emailsLeechFunc(url):
    try:
        return htmlPageRead(url)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            try:
                url = 'http://webcache.googleusercontent.com/search?q=cache:' + url
                return htmlPageRead(url)
            except:
                pass
        else:
            pass


def email_extract(lp):
    emails = []
    for url in lp:
        email_l = len(emails)
        if email_l < 6:
            try:
                response = emailsLeechFunc(url)
                print("Crawling URL %s" % url)
                reg_email = re.findall(r"([a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)", response, re.I)
                for e in reg_email:
                    if e[-3:] == 'png' or e[-3:] == 'jpg':
                        pass
                    else:
                        emails.append(e)
            except:
                print("inside email_extract  - ", sys.exc_info()[0])
                continue
        else:
            break
    return set(emails)


def email(url):
    lp = []
    try:
        lp.append(url)
        response = emailsLeechFunc(url)
        parts = urlsplit(url)
        site = "{0.netloc}".format(parts)
        base_url = "{0.scheme}://{0.netloc}".format(parts)
        base_url1 = base_url.replace('www.', '')
        path = url[:url.rfind('/') + 1] if '/' in parts.path else url
        soup = BeautifulSoup(response, 'lxml')
        for anchor in soup.find_all("a"):
            link = anchor.attrs["href"] if "href" in anchor.attrs else ''
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith('http'):
                link = path + link
            if base_url in link or base_url1 in link:
                if any(word in link for word in words):
                    split_link = link.split("/")
                    len_split = split_link.count(site)
                    if len_split < 2:
                        lp.append(link)
        lp1 = set(lp)
        print(lp1)
        result = email_extract(lp1)
        if len(result) == 0:
            return ['No email', 'No email', 'No email', 'No email', 'No email']
        else:
            #list_of_strings = [str(s) for s in result]
            #res = " , ".join(list_of_strings)
            val = list(result)
            ln = len(val)
            if ln < 5:
                for i in range(5-ln):
                    val.append('No email')
            return val
    except:
        print("inside email  - ", sys.exc_info()[0])
        pass


# Scraping function
def Scrap(words, counts, sheet):
    query_no = 1
    try:
        for word in words:
            print("QUERY NUMBER {}".format(query_no))
            print("***Authenticating api****")
            paid_list = []
            localPack_url = []
            localPack_title = []
            headers = {
                "apikey": 'api key'}

            params = (
                ("q", word),
                ("gl", "US"),
                # ('search_engine', 'google.com')
            )

            response = requests.get("https://app.zenserp.com/api/v2/search", headers=headers, params=params)
            time.sleep(2)
            result = response.json()

            # field 1
            Query = result["query"]["q"]

            # field 2
            try:
                for organic in result["organic"][0]['localPack']:
                    localPack_url.append(organic["url"])
                    localPack_title.append(organic["title"])
            except:
                localPack_url = ['None', 'None', 'None']
                localPack_title = ['None', 'None', 'None']

            # field 3
            try:
                for paid_item in result["paid"]:
                    paid_list.append(paid_item["visurl"])

                print("number of paid site to be scraped in query- {0} is {1}".format(Query, len(paid_list)))

                # Combining
                for item in paid_list:
                    email_list = email(item)
                    record = {
                        'Query': Query,
                        'paid': item,
                        'title1': localPack_title[0],
                        'comp1': localPack_url[0],
                        'title2': localPack_title[1],
                        'comp2': localPack_url[1],
                        'title3': localPack_title[2],
                        'comp3': localPack_url[2],
                        'email1': email_list[0],
                        'email2': email_list[1],
                        'email3': email_list[2],
                        'email4': email_list[3],
                        'email5': email_list[4]
                    }
                    search_results.append(record)
                    print("record updated {}".format(counts))
                    counts += 1
            except:
                print("number of paid site to be scraped in query- {0} is {1}".format(Query, len(paid_list)))
                # Combining
                record = {
                    'Query': Query,
                    'paid': 'None',
                    'title1': localPack_title[0],
                    'comp1': localPack_url[0],
                    'title2': localPack_title[1],
                    'comp2': localPack_url[1],
                    'title3': localPack_title[2],
                    'comp3': localPack_url[2],
                    'email1': 'No email',
                    'email2': 'No email',
                    'email3': 'No email',
                    'email4': 'No email',
                    'email5': 'No email'
                }
                search_results.append(record)
                print("record updated {}".format(counts))
                counts += 1
            sheet_runs = sheet.get_worksheet(1)
            df = pd.DataFrame(search_results)
            search_results.clear()
            for value in df.values.tolist():
                sheet_runs.append_row(value)
            query_no += 1
    except:
        print("inside scrap  - ", sys.exc_info()[0])
        pass


if __name__ == "__main__":
    start_time = time.time()
    print("start time {}".format(start_time))
    try:
        # ------------- Authentication--------------------------
        print("***********************Authenticating google spread sheet **********************")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        cred = ServiceAccountCredentials.from_json_keyfile_name('google spread sheet api key', scope)
        client = gspread.authorize(cred)
        sheet = client.open('google spreadsheet')
        print("***********************Authentication success **********************")

        try:
            # --------------READ-------------------------------------
            # get the first sheet of the Spreadsheet
            sheet_instance = sheet.get_worksheet(0)
            records_data = sheet_instance.get_all_records()
            for name in records_data:
                lists.append(name["Query"].strip())
            print("*********************** Input from google spread sheet **********************")
            print(lists)
        except:
            print("read  - ", sys.exc_info()[0])
            pass
        try:
            #  ---------------Scraping-------------------------------
            print("*********************** Scraping started **********************")
            Scrap(lists, count, sheet)
            print(search_results)
        except:
            print("scrap  - ", sys.exc_info()[0])
            pass
    except:
        print("main exit gspread  - ", sys.exc_info()[0])
        pass
    end_time = time.time()
    total_time = end_time - start_time
    print("Total Time elapsed : {}".format(total_time))

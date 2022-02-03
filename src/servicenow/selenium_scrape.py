from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import json
from bs4 import BeautifulSoup
import requests
import uuid


class SessionMgmt:
    _output_dir = "output"

    def __init__(self):
        self.filename = "driver_session.json"

    def start_session(self):
        driver = webdriver.Chrome()
        executor_url = driver.command_executor._url
        session_id = driver.session_id
        session_info = {'url': executor_url, 'sid': session_id}
        with open(self.filename, 'w') as f:
            json.dump(session_info, f)
        return driver

    def get_remote_session(self):
        if not os.path.isfile(self.filename):
            raise Exception("No session file:{}".format(self.filename))

        with open(self.filename, 'r') as f:
            session_dict = json.load(f)
        executor_url = session_dict['url']
        session_id = session_dict['sid']
        driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
        driver.session_id = session_id
        return driver

    @classmethod
    def set_output_dir(cls, output_dir):
        cls._output_dir = output_dir

    @classmethod
    def get_output_dir(cls):
        if not os.path.isdir(cls._output_dir):
            os.makedirs(cls._output_dir)

        return cls._output_dir


def next_uuid():
    return str(uuid.uuid4())


def get_output_dir():
    base_dir = SessionMgmt.get_output_dir()
    directory_path = os.path.join(base_dir, 'kb.html')
    if not os.path.isdir(directory_path):
        os.makedirs(directory_path)
    return directory_path


def get_media_dir():
    basedir = get_output_dir()
    media_dir = os.path.join(basedir, 'media')
    if not os.path.isdir(media_dir):
        os.makedirs(media_dir)
    return media_dir, "media"


def get_media_file_path(filename):
    media_dir, dirname = get_media_dir()
    unique_name = "{}-{}".format(next_uuid(), filename)
    filepath = os.path.join(media_dir, unique_name)
    return filepath, dirname + "/" + unique_name


def get_file_path(filename):
    dir_path = get_output_dir()
    return os.path.join(dir_path, "{}.html".format(filename))


def parse_html(html_string, append_html=True):
    html_doc = html_string
    if append_html:
        html_doc = "<html><body>{}</body></html>".format(html_string)
    soup = BeautifulSoup(html_doc, 'html.parser')
    return soup


def save_kb_article(kb, driver, save_pdf=False):
    link = kb.link
    driver.get(link)
    wait_time_sec = 5
    print("waiting for {} seconds for {} to load".format(wait_time_sec, link))
    time.sleep(wait_time_sec)
    kb.find_article_element(driver)
    kb.fix_links()
    kb.save_article()
    if save_pdf:
        driver.execute_script('window.print();')


def make_link(kb):
    return "<li><a href='{}.html'>{}</li>".format(kb.index, kb.text)


def make_db(kb_articles, driver, save_pdf=False):
    links = []
    for kb in kb_articles:
        save_kb_article(kb, driver, save_pdf)
        link_text = make_link(kb)
        links.append(link_text)
    index_file = get_file_path('index')
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("<html><body><ol>")
        for link in links:
            f.write(link)
        f.write("</ol></body></html>")


def remove_amp_and_view(rel_url: str):
    remove_list = ['&amp;view=true', '&view=true']
    for t in remove_list:
        if rel_url.endswith(t):
            return rel_url[:-len(t)]
    return rel_url


def make_attachment_request(relative_link, base_url, driver_cookies):
    cookies = {}
    rel_link_clean = remove_amp_and_view(relative_link)
    for cookie in driver_cookies:
        cookies[cookie['name']] = cookie['value']
    url = base_url[:-1] + rel_link_clean

    # url = base_url[:-1] + relative_link[:-10]
    r = requests.get(url, cookies=cookies)
    if r.status_code == 200:
        return r
    else:
        print("Failed to get url:{}".format(url))
        return None


def get_filename_from_response_header(response):
    key = 'Content-Disposition'
    if not (key in response.headers):
        return None
    content_disposition_header = response.headers[key]
    parts = content_disposition_header.split(';')
    filename_key = 'filename='
    for part in parts:
        part = part.strip()
        if part.startswith(filename_key):
            filename = part[len(filename_key):].strip()
            if filename.startswith("\""):
                filename = filename[1:]
            if filename.endswith("\""):
                filename = filename[:-1]
            if filename.startswith("'"):
                filename = filename[1:]
            if filename.endswith("'"):
                filename = filename[:-1]

            return filename
    return None


class KBArticleLine:
    def __init__(self, element, base_url, idx=-1):
        self.index = idx
        self.base_url = base_url
        self.outer = element.get_attribute('outerHTML')
        self.soup = parse_html(self.outer)
        self.href = self.soup.a.get('href')
        self.text = self.soup.text
        self.inner = element.get_attribute('innerHTML')
        self.link = self.base_url + self.href
        self.elements, self.content_soup, self.cookies = None, None, None

    def set_cookies(self, cookies):
        self.cookies = cookies

    def find_article_element(self, driver):
        self.elements = driver.find_element(By.CSS_SELECTOR, '.panel-body')
        self.content_soup = BeautifulSoup(driver.page_source, 'html.parser')

    def _process_attachments(self):
        attachments = self.content_soup.find_all("li", {"class": "attached-file"})
        if not attachments:
            return None
        for attachment in attachments:
            a = attachment.find("a")
            if not a:
                continue
            rel_link = a['href']
            resp = make_attachment_request(rel_link, self.base_url, self.cookies)
            if not resp:
                continue
            filename = get_filename_from_response_header(resp)
            if not filename:
                print("No filename found in url:{}".format(rel_link))
                print("Headers:{}".format(resp.headers))
                continue
            filepath, rel_path = get_media_file_path(filename)
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            a['href'] = rel_path

    def _make_request(self, url):
        cookies = {}
        for cookie in self.cookies:
            cookies[cookie['name']] = cookie['value']
        response = requests.get(url, cookies=cookies)
        if response.status_code != 200:
            return None
        return response

    def _download_and_save_image(self, image_src):
        response = self._make_request(image_src)
        if not response:
            print("Image get request failed:{}".format(image_src))
            return None
        filename = get_filename_from_response_header(response)
        if not filename:
            print("No filename in response header:{}".format(image_src))
            print("Response headers:{}".format(response.headers))
            return None
        filepath, rel_path = get_media_file_path(filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return rel_path

    def _process_images(self):
        if not self.cookies:
            raise Exception("Cookies not set")

        for img in self.content_soup.find_all('img'):
            src = img['src']
            if src.startswith('/') or src.startswith("sys_attachment"):
                full_src = self.base_url + src
                rel_path = self._download_and_save_image(full_src)
                if rel_path:
                    img['src'] = rel_path
            else:
                continue

    def fix_links(self):
        self._process_images()
        self._process_attachments()
        """
        for img in self.content_soup.find_all('img'):
            src = img['src']
            if src.startswith('/') or src.startswith("sys_attachment"):
                img['src'] = self.base_url + src
        """

        title_headers = self.content_soup.find_all("h2", {"class": "kb-title-header"})
        header = title_headers[0]
        new_tag = self.content_soup.new_tag("a")
        new_tag.attrs['href'] = self.link
        new_tag.string = 'Read in ServiceNow'
        br = self.content_soup.new_tag("br")
        p = self.content_soup.new_tag("p")
        p.string = "[ You must be logged on to ServiceNow for images to work ]"
        header.insert_after(br)
        br.insert_after(new_tag)
        new_tag.insert_after(p)
        new_tag.insert_after(self.content_soup.new_tag("br"))
        self._remove_extra_content()
        # header.append(br)

    def _remove_extra_content(self):
        fz_headers = self.content_soup.find_all("div", {"sn-atf-area": "Fujitsu Header"})
        if fz_headers:
            for header in fz_headers:
                header.decompose()

        header = self.content_soup.find('header')
        if header:
            header.decompose()
        kb_number_info = self.content_soup.find_all("div", {"class": "kb-number-info"})
        if kb_number_info:
            for row in kb_number_info:
                row.decompose()

    def save_article(self):
        if self.index < 0:
            raise Exception("Index not set ")
        file_path = get_file_path("{}".format(self.index))
        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(str(self.content_soup))

    def set_index(self, idx):
        self.index = idx
        return self

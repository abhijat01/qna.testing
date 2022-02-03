import servicenow.selenium_scrape as sel

from selenium.webdriver.common.by import By
import time
from utils import info


def download():
    svc_now_url = 'https://tizona.service-now.com/fna/'
    sess = sel.SessionMgmt()
    driver = sess.get_remote_session()
    driver.get(svc_now_url)
    url = "https://tizona.service-now.com/fna/?id=kb_category&kb_category=25e9fde64febde405165fc828110c7db"
    driver.get(url)
    time.sleep(10)
    click_ = True
    element = None
    counter = 0
    break_after = 100
    while click_:
        if not (element is None):
            element.click()
        info("Waiting for 5 seconds for page to fully load")
        time.sleep(5)
        elements = driver.find_elements(By.CSS_SELECTOR, '.btn-loadmore')
        click_ = (len(elements) > 0)
        if click_:
            element = elements[0]
            counter += 1
        if counter > break_after:
            break
    info("Listed all knowledge base articles")

    x_path = "//*[contains(@ng-href,'id=kb_article')]"
    elements = driver.find_elements(By.XPATH, x_path)
    kb = [sel.KBArticleLine(element, svc_now_url, i) for i, element in enumerate(elements)]
    for k in kb:
        k.set_cookies(driver.get_cookies())
    len(kb)
    sel.make_db(kb, driver)
    pass


if __name__ == '__main__':
    download()

import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

import logging
logger = logging.getLogger(__name__)


def parse_by_dates(start_date, end_date):
    starting_time = datetime.now()
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    dates = [(start + timedelta(days=i)).strftime("%Y%m%d") for i in range((end - start).days + 1)]
    results = []
    with ThreadPoolExecutor(max_workers=os.cpu_count() // 2) as executor:
        futures = {executor.submit(get_articles, date): date for date in dates}
        for future in as_completed(futures):
            results.extend(future.result())
    logger.info(f"{len(results)} articles found in {datetime.now() - starting_time}")
    return results


def get_articles(date):
    starting_time = datetime.now()
    logger.info(f"STARTED parsing of {date}")
    driver = webdriver.Chrome()
    driver.set_window_position(20 * int(threading.current_thread().name[-1]), 0)
    driver.get(f"https://ria.ru/{date}")
    wait = WebDriverWait(driver, 10)

    button = driver.find_element(By.CSS_SELECTOR, "div.list-more")
    driver.execute_script("arguments[0].scrollIntoView();", button)
    button.click()
    time.sleep(2)

    elem = driver.find_element(By.TAG_NAME, "body")

    while True:
        try:
            elem.send_keys(Keys.PAGE_DOWN)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.list-more")))

        except TimeoutException:
            urls = []
            for article in driver.find_elements(By.CSS_SELECTOR, "div.list-item[data-type='article']"):
                urls.append(article.find_element(By.CSS_SELECTOR, "a.list-item__title").get_attribute("href"))
            logger.info(f"COMPLETED parsing of {date} {len(urls)} found in {datetime.now() - starting_time}")
            driver.close()
            return urls
        except Exception as e:
            driver.close()
            raise e


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parse_by_dates('20250201', '20250214')

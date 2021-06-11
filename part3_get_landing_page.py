from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from time import sleep
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import sys
import tqdm

CHROME_BINARY_LOCATION = '/usr/bin/google-chrome-stable'
CHROME_DRIVER_PATH = '/deeperpool/zhangjunqi/chromedriver/chromedriver'


def road_situation():

    # 初始化一个谷歌浏览器实例
    options = webdriver.ChromeOptions()
    options.binary_location = CHROME_BINARY_LOCATION
    options.add_argument('user-agent="Chrome(Android 6.1.1; Nexus 6 Build/LYZ28E)"')
    options.add_argument('headless')
    options.add_argument('hide-scrollbars')
    options.add_argument('window-size=360x4800')
    driver = webdriver.Chrome(CHROME_DRIVER_PATH, chrome_options=options)

    with open('mobile_data/info/position_all_ready.txt') as f:
        position_all_ready = f.read()
        query_info_list = position_all_ready.strip().split('\n\n')
        for i, item in tqdm.tqdm(enumerate(query_info_list)):
            item_list = item.split('\n')
            print("No.",i," query: ",item_list[0].split('\t')[0])
            for url_i, url in enumerate(item_list[1:]):
                url_url = url.strip().split('\t')[1]
                try:
                    driver.get(url_url)
                    try:
                        if EC.alert_is_present():
                            WebDriverWait(driver,5).until(EC.element_to_be_clickable((By.ID, "CloseLink"))).click()
                        edit_name = driver.find_element_by_id("nickname")
                        edit_name.clear()
                        edit_name.send_keys(u"marinio")

                        tarea_content = driver.find_element_by_id("commentContent")
                        tarea_content.clear()
                        tarea_content.send_keys(u"Ale tu fajna pogoda :-) a jak u was?")

                        button_send = driver.find_element_by_id("submit")
                        # only after alert-adverb is closed:
                        button_send.click()

                        # or with JSexecutor:
                        driver.execute_script("document.getElementById('submit').click()")
                        WebDriverWait(driver, 2).until(EC.text_to_be_present_in_element((By.XPATH, "//body"), u'Komentarz zostanie dodany'))
                    except:
                        a=1
                        # print("Unexpected error:", sys.exc_info()[0])
                    driver.get_screenshot_as_file("mobile_data/landing_page/"+str(i)+'_'+str(url_i)+".png")
                except:
                    print('error loading')
    driver.quit()

if __name__ == "__main__":
    road_situation()

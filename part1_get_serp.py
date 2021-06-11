#coding:utf-8
from selenium import webdriver
import time
import urllib
from PIL import Image
import numpy as np
import requests
import re
import json

def cropImage(query_id, page, id_, img, box):
    region=img.crop(box)
    region.save('mobile_data/crop/'+query_id+'_'+str(id_)+'.png', "PNG") #保存图片

def screenshot(query, query_id, page, driver):
    url = "https://wap.sogou.com/web/searchList.jsp?keyword="+urllib.parse.quote(query)
    try:
        driver.get(url)
        driver.find_element_by_id("ajax_next_page").click()
        time.sleep(5)
    except Exception as e:
        print(e)
        return False

    try:
        # pageSource = driver.page_source
        pageSource = driver.execute_script('return document.documentElement.outerHTML')
        # pageSource = driver.find_element_by_xpath("//*").get_attribute("outerHTML")
        file = open('mobile_data/html/' + query_id + '.html', 'w', encoding='utf-8')
        file.write(pageSource)
        file.close()
    except Exception as e:
        print(e)
        print('error write html file!')
        return False

    driver.get_screenshot_as_file('mobile_data/screenshot/'+query_id+'.png')

    try:
        main = driver.find_element_by_class_name("mainbody")  #结果
    except Exception as e:
        print('error find element! query: ' + query)
        print(e)
        return False

    def get_rect(element):
        rect = element.rect
        return [rect['x'], rect['y'], rect['width'], rect['height']]

    results_X_pages = main.find_elements_by_class_name("results")
    results_info = []
    for results in results_X_pages:
        results = results.find_elements_by_tag_name("div")
        #print('**********results**********')
        for result in results:
            class_ = result.get_attribute("class")
            #if class_.find('result')!=-1 or class_.find('vrResult')!=-1 and class_.find('JS')==-1:
            if class_=='result' or class_=='vrResult' or class_.find('vrResult newvr')!=-1:
                html_str = result.get_attribute('outerHTML')
                obj = {'html': html_str}
                html = json.dumps(obj)
                try:
                    url = result.find_element_by_class_name("resultLink").get_attribute("href")
                    if not url:
                        url = ''
                except:
                    print('url error!')
                    url = ''

                size_temp = result.size
                location_temp = result.location
                info = {'rect': get_rect(result), 'info': [url, html]}
                results_info.append(info)
    return results_info

def per_thread(queries, page_num):
    options = webdriver.ChromeOptions()
    options.binary_location = CHROME_BINARY_LOCATION
    options.add_argument('user-agent="Chrome(Android 6.1.1; Nexus 6 Build/LYZ28E)"')
    options.add_argument('headless')
    options.add_argument('hide-scrollbars')
    options.add_argument('window-size=360x6000')
    driver = webdriver.Chrome(CHROME_DRIVER_PATH, chrome_options=options)

    position_file = open('mobile_data/info/position_'+'0'+'.txt', 'a', encoding='utf-8')
    error_file = open('mobile_data/info/error_'+'0'+'.txt', 'a', encoding='utf-8')
    for id, query in enumerate(queries):
        query_id = str(id)
        print('query_id: {}, query: {}'.format(query_id, query))
        flag = True
        for page in range(page_num):
            try:
                results = screenshot(query, query_id, str(page+1), driver)
                if results is False:
                    flag = False
                    break
            except Exception as e:
                print(e)
                flag = False
                break

            img = Image.open('mobile_data/screenshot/'+query_id+'.png')
            position_file.write(query+'\t'+str(page+1)+'\t'+str(len(results))+'\n')
            for i, item in enumerate(results):
                x, y, w, h = item['rect']
                if w != 0 and h != 0:
                    cropImage(query_id, str(page+1), i, img, [x,y,x+w,y+h])
                rect = ' '.join([str(t) for t in item['rect']])
                info = '\t'.join(item['info'])
                position_file.write(rect+'\t'+info+'\n')
        if flag:
            position_file.write('\n')
    position_file.close()
    error_file.close()
    driver.quit()

def combine_file(num_thread):
    position_file = open('mobile_data/info/position.txt', 'w', encoding='utf-8')
    for i in range(num_thread):
        position_file_thread = open('mobile_data/info/position_'+str(i)+'.txt', 'r', encoding='utf-8')
        data = position_file_thread.read().strip()
        if data == '':
            continue
        position_file.write(data+'\n\n')
        position_file_thread.close()
    position_file.close()

    error_file = open('mobile_data/info/error.txt', 'w', encoding='utf-8')
    for i in range(num_thread):
        error_file_thread = open('mobile_data/info/error_'+str(i)+'.txt', 'r', encoding='utf-8')
        data = error_file_thread.read().strip()
        error_file.write(data+'\n')
        error_file_thread.close()
    error_file.close()

def main():
    queries = []
    with open(QUERY_DATA_PATH, "r", encoding="utf8") as query_file:
        for line in query_file.readlines():
            queries.append(line.strip())
    
    per_thread(queries,page_num=1)
    combine_file(1)


if __name__ == '__main__':
    # chrome driver path
    CHROME_BINARY_LOCATION = '/usr/bin/google-chrome-stable'
    CHROME_DRIVER_PATH = '/deeperpool/zhangjunqi/chromedriver/chromedriver'
    # your query file path
    QUERY_DATA_PATH = 'query.txt'
    main()


#coding:utf-8
import numpy as np
import urllib.parse as parse
import re
import sys

from local_utils import decode_query, read_lines

page_num = 1



######################  helper functions #########################
def get_query2id():
    query2id = {}
    with open(query_list_path, 'r', encoding='utf8') as fin:
        for i, line in enumerate(fin):
            query = line.strip().split('\t')[0]
            query2id[query] = str(i)
    return query2id

def get_id2query():
    id2query = []
    with open(query_list_path, 'r', encoding='utf8') as fin:
        for line in fin:
            id2query.append(line.strip().split('\t')[0])
    return id2query

def get_url2id():
    url2id = {}
    with open('mobile_data/analysis/web_url_all.txt', 'r', encoding='utf8') as fin:
        for i, line in enumerate(fin):
            url = line. strip()
            url2id[url] = str(i)
    return url2id

def get_id2url():
    id2url = []
    with open('mobile_data/analysis/web_url_all.txt', 'r', encoding='utf8') as fin:
        for line in fin:
            url = line.strip()
            id2url.append(url)
    return id2url

vrid_patt = re.compile(r'sogou_vr_(\d+)')
vrid_patt1 = re.compile(r'vrid=(\d+)')
url_patt = re.compile(r'[&|;]url=(.*?)&')

# 在html中解析出真实的url
def get_real_url(url, html):
    # 若爬取的url合法，则直接可以unquote返回
    if url.startswith('http'):
        return parse.unquote(url)

    url_res = url_patt.search(html)
    if url_res != None:
        url = url_res.group(1)
        url = parse.unquote(url)
    return url

# 在html中解析出vrid
def get_real_vrid(html):
    vrid_res = vrid_patt.search(html)
    if vrid_res != None:
        return vrid_res.group(1)

    vrid_res = vrid_patt1.search(html)
    if vrid_res != None:
        return vrid_res.group(1)

    return '-1'

# 在url中解析真实的url和对应的vrid
def get_url_vrid(url):
    # 只有以此开头的url能解析，否则需要去html中解析
    if not url.startswith('https://wap.sogou.com/web'):
        return (url, None)
    vrid = vrid_patt1.search(url)
    if vrid != None: vrid = vrid.group(1)
    else:
        # 有时候vrid的出现形式是'vr=xxxxxxxx'，和标准的不一样
        vrid = re.search(r'vr=(\d+)', url)
        # 目前vrid不存在的情况只遇到了一种：搜索一个不存在的网址，返回的第一个结果是没有vrid的
        if vrid == None: vrid = '-1'
        else: vrid = vrid.group(1)
    url_res = url_patt.search(url)
    if url_res != None: url = url_res.group(1)
    # 有时候url在unquote之后结尾会出现'\n'，需要strip掉
    url = parse.unquote(url).strip()
    return (url, vrid)

######################### major tasks ###############################
def web_data():
    with open('mobile_data/info/position.txt', 'r', encoding='utf8') as file, \
        open('mobile_data/info/position_all_ready.txt', 'w', encoding='utf8') as out_file, \
        open('mobile_data/analysis/web_url_all.txt', 'w', encoding='utf8') as url_file, \
        open('mobile_data/analysis/web_vrid_all.txt', 'w', encoding='utf8') as vrid_file, \
        open('mobile_data/analysis/novel_list.txt', 'w', encoding='utf8')as novel_out, \
        open('mobile_data/analysis/web_url_html.txt', 'w', encoding='utf8') as url_html_file:

        queries, urls, vrids = set(), set(), {}
        num = 1
        line_no = 0
        bad_vrid_cnt = 0
        novel_cnt = 0

        while True:
            lines = read_lines(file)
            if lines == []: break

            if num % 1000 == 0: print(num)
            num += 1
            page_anchor = 0
            page_indexs = []
            flag = True
            for i in range(page_num):
                page_indexs.append(page_anchor)
                if page_anchor >= len(lines):
                    print('{}: page not exist error!'.format(num))
                    flag = False
                    break
                line = lines[page_anchor].strip().split('\t')
                query, result_num = line[0], int(line[2])
                line_no += result_num + 2
                if page_anchor+result_num+1 > len(lines):
                    print('{}: result not exist error!'.format(num))
                    flag = False
                    break

                url_list, url_html = [], []
                for ind in range(page_anchor+1, page_anchor+result_num+1):
                    line = lines[ind].strip('\n').split('\t')
                    crop_ind = ind-1
                    try:
                        position = line[0]
                        x,y,w,h = position.split(' ')
                        if w == '0' or h == '0': continue

                        if len(line)==3:
                            url, html = line[1:]
                            if url == None: print(url)
                            url, vrid = get_url_vrid(url)
                            if vrid == None:
                                # 对于小说类query的特判。小说类query返回的第一个结果是一个聚合框，对于这个框，
                                # 爬虫会爬出4个result，其中第一个是有效的，可以match上log中的url，后两个长宽为0，在前面过滤掉了
                                # 第二个的html以此开头，对应了一个推荐框"同作者小说/同类型小说"
                                # 在此特判，将其html与前一个result合并，并追加上截图的ind
                                if re.match(r'{"html": "<div class=\\"vrResult\\">\\n\s+<div class=\\"vr-novel171019\\">\\n', html):
                                    novel_cnt += 1
                                    # print(query, ind)
                                    novel_out.write(query+'\t'+str(crop_ind)+'\n')
                                    url_html[-1] += (html, )
                                    url_list[-1] += (str(crop_ind), )
                                    continue
                                url = get_real_url(url, html)
                                vrid = get_real_vrid(html)
                                # print出的结果只有一种：query为一个不存在的网址
                                if vrid == '-1':
                                    # print('query='+query+', ind: '+str(ind)+', url='+url)
                                    # print(html[10:100])
                                    bad_vrid_cnt += 1
                        else:
                            print('{}-{}: less than three!'.format(num, ind))
                            url, html, vrid = 'null', 'null', '-1'

                        if url == '': url = 'null'
                        urls.add(url)

                        url_list.append((position, url, vrid, str(crop_ind)))
                        url_html.append((url, html))
                        if vrid in vrids: vrids[vrid] += 1
                        else: vrids[vrid] = 1
                    except Exception as e:
                        print(url)
                        print(num)
                        print(e)
                        url_list.append(('null', 'null', '-1'))
                        urls.add('null')
                out_file.write(query+'\t'+str(i+1)+'\t'+str(len(url_list))+'\n')
                for item in url_list:
                    out_file.write('\t'.join(item)+'\n')
                for item in url_html:
                    url_html_file.write('\t'.join(item)+'\n')
                page_anchor = result_num+1
            if flag:
                out_file.writelines('\n')
            if query not in queries and flag and query != '':
                queries.add(query)
        print(len(queries))
        print(len(urls))
        print(bad_vrid_cnt)
        print(novel_cnt)
        print(line_no)

        for url in urls:
            url_file.write(url+'\n')
        vrids = sorted(vrids.items(), key=lambda d:d[1], reverse=True)
        for vrid, cnt in vrids:
            vrid_file.write(vrid+'\t'+str(cnt)+'\n')

def web_raw2id(query_id, url_id):
    with open('mobile_data/info/position_all_ready.txt', 'r', encoding='utf8') as file, \
        open('mobile_data/analysis/position_id_all.txt', 'w', encoding='utf8') as out_file:

        num = 1
        while True:
            lines = read_lines(file)
            if lines == []: break
            if num % 1000 == 0: print(num)
            num += 1
            page_anchor = 0
            flag = True
            url_pages = []
            for i in range(page_num):
                if page_anchor >= len(lines):
                    print('page not exist error!')  #如果确实页面，舍弃该query
                    flag = False
                    break
                line = lines[page_anchor].strip().split('\t')
                query = line[0]
                result_num = int(line[2])
                if page_anchor+result_num+1 > len(lines):
                    print('result not exist error!')  #如果页面中缺失结果，舍弃该query
                    flag = False
                    break
                url_per_page = []
                for ind in range(page_anchor+1, page_anchor+result_num+1):   #页面都在，结果都全
                    line = lines[ind].strip().split('\t')
                    url = line[1]
                    url_per_page.append(url_id[url]+'#'+'#'.join(line[2:]))
                url_pages.append(url_per_page)
                page_anchor = result_num+1
            if flag:
                out_file.write(query_id[query]+'\t'+' '.join(url_pages[0])+'\n')

def match_one(log, crawl, K, fout = None, LIMIT = 10):
    cnt = 0
    log = [t.split('#')[:2] for t in log]
    crawl = [t.split('#')[:2] for t in crawl]
    urls = set([url for (url, vrid) in crawl])
    v2u = {}
    for u, v in crawl:
        if v in v2u: v2u[v].append(u)
        else: v2u[v] = [u]
    for u, v in log:
        if u in urls: cnt += 1
        elif v not in v2u: continue
        elif len(v2u[v]) == 1:
            cnt += 1
            # fout.write('{}\n{}\n{}\n\n'.format(v, u, id2url[int(v2u[v][0])]))
    return cnt >= LIMIT

def match_top_K(K = 10):   #K=10
    query_id = get_query2id()
    id_query = get_id2query()

    with open('mobile_data/analysis/position_id_all.txt', 'r', encoding='utf8') as web_file, \
        open('mobile_data/analysis/part-r_id.txt', 'r', encoding='utf8') as click_file:
        # open('mobile_data/analysis/special_vrid_url.txt', 'w', encoding='utf8') as vrid_file:
        web, match = {}, {}
        for i, line in enumerate(web_file):
            if i % 1000 == 0: print(i)
            line = line.strip().split('\t')
            if len(line)>2:
                urls_vrids = (line[1]+' '+line[2]).strip().split(' ')
            elif len(line) == 2:
                urls_vrids = line[1].split(' ')
            else:
                continue
            if len(urls_vrids) < K: continue

            web[line[0]] = urls_vrids
            match[line[0]] = [0, 0]

        for i, line in enumerate(click_file):
            if i % 100000 == 0: print(i)
            line = line.strip().split('\t')
            if len(line) < 2: continue
            query = line[0]
            cnt = match.get(query)
            if cnt == None: continue

            cnt[0] += 1
            urls_vrids = line[1].split(' ')
            if len(urls_vrids) < K: continue

            if match_one(urls_vrids[:K], web[query], K, LIMIT = 9):
                cnt[1] += 1

        # file_temp = open('data/analysis/match_top_{}.txt'.format(K), 'w', encoding='utf8')
        cnt = 0
        total_cnt = 0
        match_cnt = 0
        for key, item in match.items():
            all_num, match_num = item
            total_cnt += all_num
            match_cnt += match_num
            if match_num > 0:
                cnt += 1
        #         file_temp.write(id_query[int(key)]+'\t'+str(all_num)+'\t'+str(match_num)+'\n')
        # file_temp.close()
        print('total: {}, match_cnt: {}, total_log: {}, match_log_cnt: {}'.format(len(web), cnt, total_cnt, match_cnt))


if __name__ == '__main__':
    query_list_path = 'query.txt'
    web_data()  #获取web所有query和url
    web_raw2id(get_query2id(), get_url2id())

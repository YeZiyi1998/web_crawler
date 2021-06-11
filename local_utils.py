import urllib.parse as parse
import chardet
import re
import requests

url_pattern = re.compile(r'(%[A-F0-9]{2})+')
def decode_query(query):  #解码query
    query_bytes = parse.unquote_to_bytes(query)
    try:
        result = query_bytes.decode('utf8')
        if url_pattern.match(result) != None: # 有时会出现转义多次的情况，递归调用
            result = decode_query(result)
    except:
        try:
            result = query_bytes.decode('gbk')
        except: # 如果gbk和utf8均解码出错，使用chardet包检测编码方式
            char_detect = chardet.detect(query_bytes)
            if char_detect['confidence'] > 0.9:
                char_set = char_detect['encoding']
                try: # 有时会检测出系统没有的字符集，例如EUC-TW
                    result = query_bytes.decode(char_set, 'ignore')
                    return result
                except:
                    pass
            # chardet也检测失败/系统没有检测出的字符集：直接返回未解码的url串
            # print('strange query: ' + query)
            return query

    return result

def read_lines(file):
    lines = []
    line = file.readline()
    lines.append(line)
    while line != '\n':
        if not line:
            break
        line = file.readline()
        lines.append(line)
    return lines[:-1]

def realURL(url):
    if not url.startswith('https://www.sogou.com/link?') and not url.startswith('http://www.sogou.com/link?'):
        return url
    try:
        realurl = requests.get(url = url, timeout=1)
        match = re.compile("URL=.*></noscript>",re.DOTALL)
        newurl = match.findall(realurl.text,re.M)[0].replace('URL=\'','').replace('></noscript>','').replace('"','').replace('\'','')
    except Exception as e:
        return url
    return newurl

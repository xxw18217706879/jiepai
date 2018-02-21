import requests
from urllib.parse import  urlencode
from requests.exceptions import  RequestException
import json
import re
import os
from config import *
import pymongo


client=pymongo.MongoClient(MONGO_URL)
db=client[MONGO_DB]
table=db[MONGO_TABLE]



k=0
headers={
    'user-agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'referer':'https://www.toutiao.com/search/?keyword=%E8%A1%97%E6%8B%8D',
    'x-requested-with':'XMLHttpRequest'

}
def get_page_index(offset):
    base_url="https://www.toutiao.com/search_content/?"
    data={
        'offset':offset,
        'format':'json',
        'keyword':KEYWORD,
        'autoload':'true',
        'count':20,
        'cur_tab':3,
        'from':'gallery'
    }
    url=base_url+urlencode(data)
    #print(url)
    try:
        response=requests.get(url,headers=headers)
        if response.status_code ==200:
            return response.text
        return None
    except RequestException:
        print('请求索引页失败')
        return None


def parse_page_index(text):
    data=json.loads(text)
    if data and "data" in data.keys():
        for item in data.get('data'):
            yield item.get('article_url')


def get_page_detail(url):
    try:
        response=requests.get(url,headers=headers)
        if response.status_code ==200:
            return response.text
        return None
    except RequestException:
        print('请求详情页失败',url)
        return None

def save_to_mongo(content):
    try:
        if table.insert(content):
            print('save to mongo successfully',content)
    except Exception as e:
        print(e)
        print('fail')





def parse_page_detail(text):
    try:
        results=re.search('gallery: JSON.parse\("({.*?})"\),',text,re.S)
        results=(results.group(1)).replace('\\','')
        results=json.loads(results)
        images=(results['sub_images'])
        #print(len(images))
        return images
    except Exception as e:
        print(e)
        return None

def get_image_content(url):
    try:
        response=requests.get(url)
        if response.status_code==200:
            return response.content
        return None
    except Exception as e:
        print(e)
        print('图片请求失败!')

def download_image(content,k,i):
    file_path=("{}\{}({}).{}".format(os.getcwd(),str(k),str(i),'jpg'))
    print('正在下载:',file_path)
    if not os.path.exists(file_path):
        with open(file_path,'wb')as f:
            f.write(content)
            f.close()

def main ():
    if table:
        table.drop()
    global k
    offsets=[20*t for t in range(100)]
    for offset in offsets:
        text=get_page_index(offset)
        print(text)
        for item in parse_page_index(text):
            k=k+1
            print('正在下载第{}组'.format(str(k)),item)
            dic={}
            dic['url']=item
            save_to_mongo(dic)
            text=get_page_detail(item)
            images=parse_page_detail(text)
            if images:
                i=0
                for image in images:
                    i=i+1
                    image_url=image['url']
                    content=get_image_content(image_url)
                    download_image(content,k,i)

if __name__=='__main__':
    main()


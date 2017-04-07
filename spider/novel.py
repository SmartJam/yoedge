# -*- coding: utf-8 -*-
'''
Created on Mar 17, 2017

@author: Jam
'''
import requests
import re

from bs4 import BeautifulSoup
from util.common import Logger

ConstUserAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

toFile = open("t.txt", 'w')


def crawl(url):
    '''
        return nextUrl | None
    '''
    session = requests.Session()
    resp = session.get(novelUrl, headers = {'User-Agent':ConstUserAgent})
    if resp.status_code != 200:
        Logger.log("crawl failed, url:{}, resp:{}".format(novelUrl, resp))
        return None
        
    soup = BeautifulSoup(resp.text, "lxml")
    posts = soup.find_all('td', id=re.compile("postmessage_*"))
    
    for post in posts:
        if not post.find('strong'):
            continue
        
        print post.strong.text
        if post.i:
            post.i.extract()
        toFile.write(post.text)
        
    nextNode = soup.find('a', class_='nxt')
    if nextNode:
        return nextNode.get("href")
    
    return None


if __name__ == '__main__':
    novelUrl = "https://ck101.com/thread-2763314-1-1.html"
    
    while True:
        nextUrl = crawl(novelUrl)
        if not nextUrl:
            break
        novelUrl = nextUrl
    
    
        
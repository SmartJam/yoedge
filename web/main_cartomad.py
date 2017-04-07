# -*- coding: utf-8 -*-
'''
Created on Jan 17, 2017

@author: Jam
'''

from flask import Flask
from flask.templating import render_template
from util.common import Logger
import requests
import re

from bs4 import BeautifulSoup

ConstUserAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

toFile = open("t.txt", 'w')


def crawl(url):
    '''
        return None | {chapterName, imgUrls:[], nextChapterId}
    '''
    session = requests.Session()
    resp = session.get(url, headers = {'User-Agent':ConstUserAgent})
    if resp.status_code != 200:
        Logger.log("crawl failed, url:{}, resp:{}".format(url, resp))
        return None
        
    resp.encoding = "big5"
    soup = BeautifulSoup(resp.text, "lxml")
    
    title = soup.title.text
    
    img = soup.find('img', src=re.compile("http://web\d*.cartoonmad.com/*"))    
    imgUrl = img.get('src')
    imgUrlPrefix = imgUrl[:imgUrl.rfind('/')] + "/"
    
    urls = soup.find_all('a', class_='pages')
    imgsNum = int(urls[-2].text)
    
    imgUrls = []
    for imgNo in range(1, imgsNum + 1):
        imgUrls.append(imgUrlPrefix + ('/%03d' % imgNo) + ".jpg")
    
    chapter = {}
    chapter['name'] = title
    chapter['imgUrls'] = imgUrls
    return chapter


app = Flask(__name__)

@app.route('/<int:chapterId>')
def show_chapter(chapterId):
    chapterUrl = "http://www.cartoonmad.com/comic/" + str(chapterId) + ".html"
    chapter = crawl(chapterUrl)
    if chapter == None:
        return render_template('404.html'), 404
    
    return render_template('chapter_cartomad.html', chapter = chapter)

@app.route("/")
def show_index():
    return show_chapter(109000011095001);

if __name__ == '__main__':
    # test only!!
    print "running test.112111"
    
    #crawl("http://www.cartoonmad.com/comic/109000011095001.html")
    app.run("0.0.0.0", 8187, True)
    
    # spider.change2Stop()
    
    
        
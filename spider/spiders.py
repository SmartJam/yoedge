# -*- coding: utf-8 -*-
'''
Created on Apr 18, 2016

@author: Jam
'''
import ConfigParser
import Queue
import json
import threading
import time
import requests
import re
import os.path

from bs4 import BeautifulSoup
from db.datasource import DataSource
from util.common import Logger

conf = ConfigParser.ConfigParser()
conf.read("../spider.ini")        
ImgRepoDir = conf.get("baseconf", "imgRepoDir")
ShouldDownloadCover = bool(conf.get("baseconf", "downloadCover")) # 是否下载封面
IntervalSecondPerCrawl = max(int(conf.get("baseconf", "intervalSecondPerCrawl")), 1)

ConstUserAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

def downloadImage(connSession, refererUrl, imgUrl, toFilepath):
    '''
            下载图片并保存到指定路径。根据需要创建目标路径的父目录
    '''
    if os.path.exists(toFilepath):
        Logger.log("目标路径已使用， toFilepath:{}, imgUrl:{}".format(toFilepath, imgUrl))
        return
    
    fileDir = os.path.dirname(toFilepath)
    if not os.path.exists(fileDir):
        os.makedirs(fileDir)
                
    reqHeaders = {'Referer':refererUrl, 'User-Agent':ConstUserAgent}
    respImg = connSession.get(imgUrl, headers = reqHeaders)
        
    targetFile = open(toFilepath,'wb')
    targetFile.write(respImg.content)
    targetFile.close

class ChapterDownloader(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
        self.taskChapterAppIds = Queue.Queue(0)
        self.continuousFailedTimes = 0
        self.connSession = None
        self.datasource = DataSource()
        return
    
    def addTasksByComicId(self, comicId):
        queryChaptersSql = '''
            select chapterId from chapters where comicId = %s and status != 'downloaded'
        '''
        _rowCount, rows = self.datasource.execute(queryChaptersSql, [comicId])
        
        chapterAppIds = []
        for row in rows:
            chapterAppIds.append(str(row[0]))
             
        self.addTasks(chapterAppIds)
    
    def addTasks(self, chapterAppIds):
        '''
        chapterAppIds - array of chapterAppId
        '''
        
        updateSql = '''
            update chapters set status = 'downloading' where chapterId = %s
        '''
        for chapterAppId in chapterAppIds:
            self.datasource.execute(updateSql, [chapterAppId])
            self.taskChapterAppIds.put_nowait(chapterAppId)
    
    def run(self):
        while (True) :
            try:
                chapterAppId = self.taskChapterAppIds.get(True, 1)
            except Exception as _e:
                Logger.log("[ChapterDownloader] no task got, ready to exist")
                break
            
            try:
                self.tryCrawlChapter(chapterAppId)
            except Exception as e:
                Logger.log("[ChapterDownloader] crawl chapter failed, chapterAppId:{}, err:{}".format(chapterAppId, e))
                self.continuousFailedTimes += 1
                if self.continuousFailedTimes > 10:
                    Logger.log("[ChapterDownloader] too many errors, ready to exist.")
                    break
                time.sleep(3)
      
    def ensureSession(self):
        if self.connSession == None:
            self.connSession = requests.Session()
        
        return self.connSession
    
    def tryCrawlChapter(self, chapterAppId):
        chapterIndexUrl = "http://smp.yoedge.com/smp-app/{}/shinmangaplayer/index.html".format(chapterAppId)
        chapterConfUrl = "http://smp.yoedge.com/smp-app/{}/shinmangaplayer/smp_cfg.json".format(chapterAppId)
        
        
        Logger.log('[ChapterDownloader] try crawl chapter:{}, confUrl:{}'.format(chapterAppId, chapterConfUrl))
        
        session = self.ensureSession()
        respChapterConf = session.get(chapterConfUrl, headers = {'Referer':chapterIndexUrl, 'User-Agent':ConstUserAgent})
        if respChapterConf.status_code != 200:
            Logger.log("[ChapterDownloader] get chapter conf failed, url:{}, resp:{}".format(chapterConfUrl, respChapterConf))
            raise Exception('get chapter conf failed.')
            return
        
        chapterConfData = json.loads(respChapterConf.text)
        pagesData = chapterConfData['pages']
        if 'order' not in pagesData:
            #Logger.log("[ChapterDownloader] no 'order' field in resp, chapter:{}, confUrl:{}".format(chapterAppId, chapterConfUrl))
            downloadFailedUpdateSql = '''
                update chapters set status = 'download_failed' where chapterId = %s
            '''
            self.datasource.execute(downloadFailedUpdateSql, [chapterAppId])
            raise Exception("no 'order' field in conf")
         
        imgUrls = pagesData['page']
        imgOrders = pagesData['order']
        
        imgCount = 0
        for imgOrder in imgOrders:
            imgCount += 1
            
            # http://smp.yoedge.com/smp-app/{chapterAppId}/shinmangaplayer/{imgUrl}
            imgUrl = "http://smp.yoedge.com/smp-app/{}/shinmangaplayer/{}".format(chapterAppId, imgUrls[imgOrder])
            toFilepath = ImgRepoDir + '/chapters/' + str(chapterAppId) + ('/%03d' % imgCount) + ".jpg" 
            downloadImage(session, chapterIndexUrl, imgUrl, toFilepath)
            
            time.sleep(1)
        
        updateChapterSql = '''
            update chapters set status = 'downloaded', pageCount = %s 
            where chapterId = %s
        '''
        self.datasource.execute(updateChapterSql, [imgCount, chapterAppId])
        
        return

class ComicInfoSpider(threading.Thread):
    '''
            漫画信息收集器，包括漫画名、简介、封面
    '''
    def __init__(self, isDebug=False):
        threading.Thread.__init__(self)
        
        self.taskComicIds = Queue.Queue(0) # 需要爬取的任务漫画id队列
        self.connSession = None
        self.continuousFailedTimes = 0
        self.datasource = DataSource()
    
        
    def run(self):
        noTaskCount = 0
        while (True) :
            try:
                comicId = self.taskComicIds.get(True, 1)
                noTaskCount = 0
            except Exception as _e:
                # no task return
                noTaskCount += 1
                if noTaskCount > 10:
                    Logger.log("[ComicInfoSpider] no task got, thread ready to stop.")
                    break
                
                time.sleep(3)
                continue
            
            try:
                if self.tryCrawlComicInfo(comicId) == False:
                    self.continuousFailedTimes += 1
                    if self.continuousFailedTimes >= 100:
                        Logger.log("[ComicInfoSpider] stop crawling cause too much fail.")
                        break
                else:
                    self.continuousFailedTimes = 0
            except Exception as e:
                Logger.log("[ComicInfoSpider] failed, comicId:{}, error:{}".format(comicId, e))
            
            time.sleep(IntervalSecondPerCrawl)
            
    def ensureSession(self):
        # how to test the session is available or not??
        if self.connSession == None:
            self.connSession = requests.Session()
        
        return self.connSession
    
    def addTasks(self, comicIds):
        '''
        comicIds - array of comicId
        '''
        for comicId in comicIds:
            self.taskComicIds.put_nowait(comicId)
    
    def addTasksByRange(self, comicFromId, comicToId):
        '''
        comicFromId - from id
        comicToId - to id, included
        comicFromId must be larger than comicToId
        '''
        if comicFromId > comicToId:
            return
        
        for comicId in range(comicFromId, comicToId + 1):
            self.taskComicIds.put_nowait(comicId)
        
    # http://smp.yoedge.com/view/omnibus/${comicId}    
    def tryCrawlComicInfo(self, comicId):
        '''
        return true:success, false:failed
        '''
        Logger.log("[ComicInfoSpider] try handle comic:{}".format(comicId))
        
        comicIndexUrl = "http://smp.yoedge.com/view/omnibus/" + str(comicId)
        
        session = self.ensureSession()
        resp = session.get(comicIndexUrl, headers = {'User-Agent':ConstUserAgent})
        if resp.status_code != 200:
            Logger.log("[ComicInfoSpider] get comic info failed, url:{}, resp:{}".format(comicIndexUrl, resp))
            return False
        
        comicData = self.parsePage(resp.text)
        comicData['comicId'] = comicId
        
        self.sync2DB(comicData)
        
        if ShouldDownloadCover == True and bool(comicData['coverUrl']):
            coverUrl = comicData['coverUrl']
            coverImgPath = ImgRepoDir + '/covers/' + str(comicId) + '.jpg'
            downloadImage(self.ensureSession(), comicIndexUrl, coverUrl, coverImgPath)
            
        return True
    
    def parsePage(self, pageContent):
        '''
        return {
                'coverUrl':"",
                'name':"",
                'author':"", 
                'description':"", 
                'chapters':[{chapterAppId, chapterName, chapterOrder}]
                }
        '''
        soup = BeautifulSoup(pageContent, "lxml")
        
        coverUrl = soup.find("img").get("src")
        
        infoView = soup.find("div", class_="am-u-sm-8")
        
        abbrViews = infoView.find_all("abbr")
        name = abbrViews[0].string.encode('utf-8')
        author = abbrViews[1].string.encode('utf-8').replace("作者：", "")
        
        description = infoView.find("div").string.encode('utf-8').strip()
        
        chapterOrder = 0
        chapters = []
        chapteLinks = soup.find_all("a", class_="am-btn am-btn-secondary am-radius am-btn-sm")
        for link in chapteLinks:
            aHref = link.get("href")
            if bool(aHref) == False:
                continue
            
            chapterOrder += 1
            newChapter = {}
            newChapter['chapterAppId'] = re.findall('smp-app/(.*)/shinmangaplayer', aHref)
            newChapter['chapterName'] = link.string.encode('utf-8')
            newChapter['chapterOrder'] = chapterOrder            
            chapters.append(newChapter)
        
        ret = {}
        ret['coverUrl'] = coverUrl
        ret['name'] = name
        ret['author'] = author
        ret['description'] = description
        ret['chapters'] = chapters
        
        #self.sync2DB(ret)
        return ret
    
    def sync2DB(self, comicData):        
        comicId = comicData['comicId']
        name = comicData['name']
        author = comicData['author']
        description = comicData['description']
        coverUrl = comicData['coverUrl']
        
        chapterRows = []
        for chapter in comicData['chapters']:
            newRow = []
            newRow.append(comicId)
            newRow.append(chapter['chapterAppId'])
            newRow.append(chapter['chapterOrder'])
            newRow.append(chapter['chapterName'])
            chapterRows.append(newRow)
            
        insertComicSql = """
                insert into comics(
                        id, name, author, description, coverUrl,
                        status, updatedAt)
                values(%s,%s,%s,%s,%s, 'new',now())  
                on duplicate key update updatedAt = now()
        """
              
        insertChapterSql = """
                insert into chapters(
                    comicId, chapterId, chapterOrder, chapterName, addedAt,
                    status,pageCount)
                values(%s,%s,%s,%s,now(), 'new',0)
                on duplicate key update chapterOrder = values(chapterOrder), addedAt = now() 
        """      
        try:
            self.datasource.execute(insertComicSql, [comicId, name, author, description, coverUrl])
            self.datasource.inert_or_update_batch(insertChapterSql, chapterRows)
        except Exception as e:
            Logger.log("[sync2DB] fail, comicId:{}, error:{}".format(comicId, e))
        
if __name__ == '__main__':
    # test only!!
    print "running test."
        
#     spider = ComicInfoSpider(True)
#     spider.start()
#     spider.addTasksByRange(1003001, 1003100)  # end:1003016
    #spider.addTasks([1001925])
    
    downloader = ChapterDownloader()
    downloader.addTasks([1066714])
    #downloader.addTasksByComicId(1000931)
    downloader.start()
    
    time.sleep(1)
    # spider.change2Stop()
    
    
        
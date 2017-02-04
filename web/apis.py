# -*- coding: utf-8 -*-
'''
Created on Jan 22, 2017

@author: Jam
'''

import time
from db.datasource import DataSource
from util.common import Logger
from spider.spiders import ComicInfoSpider, ChapterDownloader

def _buildSuccessResp():
    return {'success':True}

def _buildFailResp(failMsg = "unknown"):
    return {'success':False, 'message':failMsg}

def _changeComicStatus(comicId, toStatus):
    sql = "update comics set status = %s, updatedAt = now() where id = %s"
    updatedCount, _ = DataSource().execute(sql, [toStatus, comicId])
    if updatedCount != 1:
        Logger.log("mark comic failed, comicId:" + str(comicId))
        return _buildFailResp('record not found')
        
    return _buildSuccessResp()

def _toCoverUrl(comicId):
    return "http://oji3qlphh.bkt.clouddn.com/covers/" + str(comicId) + ".jpg"

_comicInfoSpider = None
def _getComicSpider():
    if _comicInfoSpider == None:
        _comicInfoSpider = ComicInfoSpider()
        
    if _comicInfoSpider.isActive() == False:
        _comicInfoSpider.start()    
        
    return _comicInfoSpider
    
    
    
_chapterDownloader = None
    

def get_comics_info(pageNo = 1, pageSize = 10, onlyMarked = False):
    '''
    return: {totalCount, pageNo, pageSize, comics:[{id,name,author,description,coverUrl,status,updatedAt}]}
    '''
    offset = (pageNo - 1) * pageSize
    
    db = DataSource()
    countSql =  "select count(1) from comics"
    if onlyMarked:
        countSql += " where status = 'makred'"
    _, [[totalCount]] = db.execute(countSql)
    
    querySql = "select id,name,author,description,status, updatedAt from comics"
    if onlyMarked:
        querySql += " where status = 'marked'"
    querySql += " limit %s,%s"
    _rowCount, rows = db.execute(querySql, [offset, pageSize])
    
    comics = []
    for row in rows:
        comic = {}
        comic['id'] = row[0]
        comic['name'] = row[1]
        comic['author'] = row[2]
        comic['description'] = row[3]
        comic['coverUrl'] = _toCoverUrl(row[0])
        comic['status'] = row[4]
        comic['updatedAt'] = time.mktime(row[5].timetuple())
        
        comics.append(comic)
    
    result = _buildSuccessResp()
    result['totalCount'] = totalCount
    result['pageNo'] = pageNo
    result['pageSize'] = pageSize
    result['comics'] = comics
    
    return result
    
def mark_comic(comicId):
    return _changeComicStatus(comicId, 'marked')

def unmark_comic(comicId):
    return _changeComicStatus(comicId, 'new')

def block_comic(comicId):
    return _changeComicStatus(comicId, 'blocked')

def crawl_comic_info(comicId):
    spider = _getComicSpider()
    spider.addTasks([comicId])
    return
    

if __name__ == '__main__':
    # test only!!
    print "running test."
    
    print crawl_comic_info(1000214)
    
    # spider.change2Stop()
    
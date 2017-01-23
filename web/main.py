# -*- coding: utf-8 -*-
'''
Created on Jan 17, 2017

@author: Jam
'''

import flask
from flask import Flask, send_from_directory, request
from flask.templating import render_template
from fileinput import filename
from db.datasource import DataSource
import time
from web import apis
from util.common import Logger

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chapter/<int:chapterId>')
def show_chapter(chapterId):
    return render_template('chapter.html')

# @app.route('/static/<path:path>')
# def send_static(path):
#     Logger.log("path:" + path)
#     return send_from_directory("static", path)

@app.route('/favicon.ico')
def send_favicon():
    return send_from_directory("static", "favicon.ico")

@app.route('/api/comics', methods = ['GET'])
def get_comics_info():
    '''
    url params: page, size, mark=true|false
    return: {totalCount, pageNo, pageSize, comics:[{id,name,author,description,status,updatedAt}]}
    '''
    onlyMarked = request.args.get('marked') == "true"
    pageNo = int(request.args.get('page'))
    pageSize = int(request.args.get('size'))

    result = apis.get_comics_info(pageNo, pageSize, onlyMarked)
    return flask.jsonify(**result)

@app.route('/api/comic/<int:comicId>', methods = ['POST'] )
def mark_comic(comicId):
    result =  apis.mark_comic(comicId)
    print result
    return flask.jsonify(**result)

if __name__ == '__main__':
    # test only!!
    print "running test.112111"
    
    app.run("0.0.0.0", 8187, True)
    
    # spider.change2Stop()
    
    
        
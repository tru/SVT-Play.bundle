# -*- coding: utf-8 -*

import re
import string
from common import *

def ReindexShows(maxPaginatePages = 100):
    Log("Reindex shows")
    ReindexPaginate(URL_INDEX_THUMB % 1, URL_INDEX_THUMB, "am", Dummy, maxPaginatePages)

def Dummy():
    Log("Dummy")

def ReindexPaginate(startUrl, requestUrl, divId, callFunc, maxPages):
    Log("Reindex Pagination in progress...")
    pageElement = HTML.ElementFromURL(startUrl)
    xpathBase = "//div[@id='%s']" % (divId)
    paginationLinks = pageElement.xpath(xpathBase + "//div[@class='pagination']//li[@class='']/a")
    Log("Pagination links len: %d" % len(paginationLinks))

    start = 1
    linkPages = len(paginationLinks)
    if(linkPages > 0): 
        stop = int(paginationLinks[linkPages-1].text)
        stop = min(stop, maxPages)
    else:
        stop = 1

    Log("Start: %s, Stop: %s" % (start, stop))

    for i in range(start, stop + 1):
        nextUrl = requestUrl % i
        Log(nextUrl)
        pageElement = HTML.ElementFromURL(nextUrl)
        FindAllShows(pageElement)

def FindAllShows(pageElement):
   xpathBase = "//div[@id='%s']" % "am"
   showLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href,'/t/')]")
   for show in showLinks:
        Log("info: %s " % show.get("href"))
        GetShowInfo(URL_SITE + show.get("href"))


def GetShowInfo(showUrl):
    Log("Getting info from: %s " % showUrl)
    pageElement = HTML.ElementFromURL(showUrl)
    showImageUrl = pageElement.xpath("//meta[@property='og:image']/@content")[0]
    showInfo = (pageElement.xpath("//meta[@property='og:description']/@content")[0]
    title = pageElement.xpath("//meta[@property='og:title']/@content")[0]
    showName = string.strip(string.split(title, '|')[0])
    Log("showName: %s" % showName)
    Log(showInfo)
    Log(showUrl)
    Log(showImageUrl)
    HTTP.Request(showImageUrl, cacheTime=60)
    si = ShowInfo()
    si.name = showName
    si.info = showInfo
    si.thumbnailUrl = showImageUrl
    si.showUrl = showUrl
    if(len(showName) > 0):
        Log("Saving data for: %s " % showName)
        Data.SaveObject(showName, si) 


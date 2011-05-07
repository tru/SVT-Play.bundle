# -*- coding: utf-8 -*

import re
import string
from common import *

class ShowInfo:
    def __init__(self):
        self.thumbNailUrl = None
        self.name = None
        self.info = None
        self.url = None
        self.episodes = []


def ReindexShows(maxPaginatePages = 100):
    Log("Reindex shows")
    ReindexPaginate(URL_INDEX_THUMB % 1, URL_INDEX_THUMB, "am", Dummy, maxPaginatePages)

def GetIndexShows(sender):
    Log("GetIndexShows")
    showsList = MediaContainer(title1=TEXT_INDEX_SHOWS)
    xpathBase = "//div[@class='tab active']"
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href,'/t/')]")
    for programLink in programLinks:
        showUrl = URL_SITE + programLink.get("href")
        showName = programLink.xpath("text()")[0]
        Log("Program Link: %s" % showName)
        if(Data.Exists(showName)):
            si = Data.LoadObject(showName)
            Log("SHOW: %s " % si.name)
            Log("subtitle: %s" % si.info)
            Log("thumbnail: %s " % si.thumbNailUrl)
            showsList.Append(Function(DirectoryItem(key=GetShowEpisodes,title=showName, summary=si.info,
                thumb=si.thumbnailUrl), showInfo = si))
        else:
            showsList.Append(Function(DirectoryItem(key=GetShowEpisodes,title=showName), showInfo = None, showUrl =
                showUrl))
            
    return showsList
 
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
    showImageUrl = str(pageElement.xpath("//meta[@property='og:image']/@content")[0])
    showInfo = str(pageElement.xpath("//meta[@property='og:description']/@content")[0])
    title = str(pageElement.xpath("//meta[@property='og:title']/@content")[0])
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
    si.url = showUrl
    if(len(showName) > 0):
        Log("Saving data for: %s " % showName)
        Data.SaveObject(showName, si) 


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
        #self.episodes = []


def ReindexShows():
    Log("Reindex shows")
    pages = GetPaginatePages(URL_INDEX, "am", URL_INDEX_THUMB_PAGINATE)
    Dict["TEST2"] = ShowInfo()
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        FindAllShows(pageElement)
    
    Log("Reindex complete")


def GetIndexShows(sender):
    Log("GetIndexShows")
    showsList = MediaContainer(title1=TEXT_INDEX_SHOWS)
    xpathBase = "//div[@class='tab active']"
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href,'/t/')]")
    for programLink in programLinks:
        showUrl = URL_SITE + programLink.get("href")
        showName = string.strip(programLink.xpath("text()")[0])
        Log("Program Link: %s" % showName)
        if(Data.Exists(showName)):
            si = Data.LoadObject(showName)
            #Log("SHOW: %s " % si.name)
            #Log("subtitle: %s" % si.info)
            #Log("thumbnail: %s " % si.thumbNailUrl)
            showsList.Append(Function(DirectoryItem(key=GetShowEpisodes,title=showName, summary=si.info,
                thumb=si.thumbNailUrl), showInfo = si))
            #Log("DONE")
        else:
            showsList.Append(Function(DirectoryItem(key=GetShowEpisodes,title=showName), showInfo = None, showUrl =
                showUrl, showName = showName))
            
    return showsList

def FindAllShows(pageElement):
   xpathBase = TAG_DIV_ID  % "am"
   showLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href, '/t/')]/@href") 
   Log("FindAllShows showLinkslen: %d" % len(showLinks))
   for show in showLinks:
        Log("info: %s " % show)
        GetShowInfo(URL_SITE + show)


def GetShowInfo(showUrl):
    Log("Getting showinfo from: %s " % showUrl)
    pageElement = HTML.ElementFromURL(showUrl)
    showImageUrl = str(pageElement.xpath("//meta[@property='og:image']/@content")[0])
    showInfo = str(pageElement.xpath("//meta[@property='og:description']/@content")[0])
    title = str(pageElement.xpath("//meta[@property='og:title']/@content")[0])
    showName = string.strip(string.split(title, '|')[0])
    #Log(showInfo)
    #Log(showUrl)
    #Log(showImageUrl)
    HTTP.Request(showImageUrl, cacheTime=60)
    si = ShowInfo()
    si.name = str(showName)
    si.info = showInfo
    si.thumbNailUrl = showImageUrl
    si.url = showUrl

    if(len(showName) > 0):
        Data.SaveObject(showName, si) 

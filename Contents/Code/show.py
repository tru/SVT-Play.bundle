# -*- coding: utf-8 -*

import re
import string
from common import *

class ShowInfo:
    def __init__(self):
        self.thumbNailUrl = None
        self.thumbFileName = None
        self.name = None
        self.info = None
        self.url = None
        #self.episodes = []


def ReindexShows():
    Log("Reindex shows")
    pages = GetPaginatePages(URL_INDEX, "am", URL_INDEX_THUMB_PAGINATE)
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
                thumb=Function(GetShowThumb, showInfo=si)), showInfo = si))
            #Log("DONE")
        else:
            showsList.Append(Function(DirectoryItem(key=GetShowEpisodes,title=showName, thumb=Function(GetShowThumb,
                showInfo=None)), showInfo = None, showUrl = showUrl, showName = showName))
            
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
    pageElement = HTML.ElementFromURL(showUrl, cacheTime = CACHE_TIME_1DAY)
    showImageUrl = str(pageElement.xpath("//meta[@property='og:image']/@content")[0])
    showInfo = str(pageElement.xpath("//meta[@property='og:description']/@content")[0])
    title = str(pageElement.xpath("//meta[@property='og:title']/@content")[0])
    showName = string.strip(string.split(title, '|')[0])
    
    moreInfoUrl = pageElement.xpath("//div[@class='info']//li[@class='title']/a/@href")
    if(len(moreInfoUrl)):
        extShowInfo = MoreInfoPopup(HTML.ElementFromURL(URL_SITE + moreInfoUrl[0], cacheTime = CACHE_TIME_1DAY)).ShowInfo()
        if(extShowInfo != None):
            showInfo = str(extShowInfo)
    Log(showInfo)


    si = ShowInfo()
    try:
        image = HTTP.Request(showImageUrl, cacheTime=CACHE_TIME_1DAY).content
        imageName = showName + ".image"
        Log("imageName: %s" % imageName)
        Log("image: %s" % image)
        Data.SaveObject(imageName, image)
        si.thumbFileName = imageName
    except:
        si.thumbFileName = ""
       

    si.name = str(showName)
    si.info = showInfo
    si.thumbNailUrl = showImageUrl
    si.url = showUrl

    if(len(showName) > 0):
        Data.SaveObject(showName, si) 

def GetShowThumb(showInfo = None):
    if(showInfo == None):
        return Redirect(R(THUMB))

    try:
        if(Data.Exists(showInfo.thumbFileName)):
            Log("Found image: %s" % showInfo.thumbFileName)
            image = Data.LoadObject(showInfo.thumbFileName)
            return DataObject(image, "image/jpeg")
    except:
        Log("Could not get image for %s (imageName:%s)" % (showInfo.name, showInfo.thumbFileName))
        pass

    try:
        image = HTTP.Request(showInfo.thumbNailUrl, cacheTime=CACHE_TIME_SHORT).content
        return DataObject(image, "image/jpeg")
    except: 
        pass

    return Redirect(R(THUMB))


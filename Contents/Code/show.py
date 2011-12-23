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
    pages = GetPaginatePages(url=URL_INDEX, divId="am", paginateUrl=URL_INDEX_THUMB_PAGINATE, maxPaginateDepth=500)
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        FindAllShows(pageElement)

    Log("Reindex complete")

def FindAllShows(pageElement):
    xpathBase = TAG_DIV_ID  % "am"
    showLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href, '/t/')]/@href") 
    Log("FindAllShows showLinkslen: %d" % len(showLinks))
    for show in showLinks:
        Log("info: %s " % show)
        GetShowInfo(URL_SITE + show)

def GetIndexShows():
    Log("GetIndexShows")
    showsList = ObjectContainer(title2=TEXT_INDEX_SHOWS)
    xpathBase = "//div[@class='tab active']"
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href,'/t/')]")
    
    CreateShowList(showsList, programLinks)

    return showsList

def GetRecommendedShows():
    Log("GetRecommendedShows")
    showsList = ObjectContainer(title2=TEXT_RECOMMENDED_SHOWS)
    pages = GetPaginatePages(URL_RECOMMENDED_SHOWS, "pb")
    programLinks = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        pLinks = pageElement.xpath("//div[@id='pb']//div[@class='content']//li/a[starts-with(@href, '/t/')]")
        programLinks = programLinks + pLinks

    CreateShowList(showsList, programLinks, True)
    return showsList

def GetCategoryShows(catUrl, catName):
    Log("GetCategoryShows %s" % catUrl)
    catShows = ObjectContainer(title2=catName)
    pages = GetPaginatePages(catUrl, 'pb')
    programLinks = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        pLinks = pageElement.xpath("//div[@id='pb']//div[@class='content']//li/a[starts-with(@href, '/t/')]")
        programLinks = programLinks + pLinks

    CreateShowList(catShows, programLinks, True)
    return catShows 

def GetCategoryNewsShows(catUrl, catName):
    Log("GetCategoryNewsShows")
    catShows = ObjectContainer(title2 = catName)
    pageElement = HTML.ElementFromURL(catUrl)
    links = pageElement.xpath("//div[@id='sb' or @id='se']//div[@class='content']//a")
    CreateShowList(catShows, links, True)
    return catShows

#This function wants a <a>..</a> tag
def CreateShowList(container, programLinks, isRecommendedShows = False):
    for programLink in programLinks:
        showUrl = URL_SITE + programLink.get("href")
        showName = string.strip(programLink.xpath("text()")[0])
        secondaryThumbUrl = None
        if(isRecommendedShows):
            showName = string.strip(programLink.xpath(".//span/text()")[0])
            secondaryThumbUrl = programLink.xpath(".//img/@src")[0]
            Log("Secondary thumb url: %s" % secondaryThumbUrl)
        
        Log("Program name: %s" % showName)
        if(Data.Exists(showName)):
            si = Data.LoadObject(showName)
            Log("Using stored data for: %s " % si.name)
            #Log("subtitle: %s" % si.info)
            #Log("thumbnail: %s " % si.thumbNailUrl)
            thumbF = Callback(GetShowThumb, showInfo=si, secondaryThumb=secondaryThumbUrl)
            container.add(DirectoryObject(key=Callback(GetShowContents, showInfo=si),
                                             title=showName, summary=si.info, thumb=thumbF))
            #Log("DONE")
        else:
            thumbF = Callback(GetShowThumb, showInfo=None, secondaryThumb=secondaryThumbUrl)
            container.add(DirectoryObject(key=Callback(GetShowContents, showInfo=None, showUrl=showUrl, showName=showName),
                                             title=showName, thumb=thumbF))

    return container


def GetShowContents(showInfo, showUrl = None, showName = None):
    if(showUrl == None):
        Log("GetShowContents: %s, %s" %  (showInfo.name, showInfo.url))
        showUrl = showInfo.url
        showName = showInfo.name
    else:
        Log("GetShowContents(no showInfo):")

    list = ObjectContainer(title2=showName)
    GetShowCategories(list, showUrl)
    GetShowEpisodes(list, showUrl)

    return list

def GetShowCategories(container, showUrl=None):
    pages = GetPaginatePages(showUrl, "sb")
    catInfos = []
    for page in pages:
        catInfos = catInfos + GetCategoryInfosFromPage(page)

    for catInfo in catInfos:
        f = DirectoryObject(key=Callback(GetCategoryContents, ci=catInfo), title=catInfo.name, thumb=catInfo.thumbUrl)
        container.add(f)
        
    return container

def GetShowEpisodes(container, showUrl = None):
    pages = GetPaginatePages(showUrl, "sb")
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    for epUrl in epUrls:
        #Log("EPURL: %s" % epUrl)
        epInfo = GetEpisodeInfo(epUrl)
        container.add(epInfo.GetMediaItem())
    return container


def GetShowInfo(showUrl):
    Log("Getting showinfo from: %s " % showUrl)
    pageElement = HTML.ElementFromURL(showUrl, cacheTime = CACHE_TIME_1DAY)
    showImageUrl = pageElement.xpath("//meta[@property='og:image']/@content")[0].text
    showInfo = pageElement.xpath("//meta[@property='og:description']/@content")[0].text
    title = pageElement.xpath("//meta[@property='og:title']/@content")[0].text
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

def GetShowThumb(showInfo = None, secondaryThumb = None):
    Log("GetShowThumb")
    if(showInfo != None):
        Log("GetShowThumb: %s" % showInfo.name)
        try:
            if(Data.Exists(showInfo.thumbFileName)):
                Log("Found image: %s" % showInfo.thumbFileName)
                image = Data.LoadObject(showInfo.thumbFileName)
                imageObj = DataObject(image, "image/jpeg")
                return imageObj
        except:
            Log("Could not get image for %s (imageName:%s)" % (showInfo.name, showInfo.thumbFileName))
            pass

        try:
            Log("Trying to get standard thumb from website")
            image = HTTP.Request(showInfo.thumbNailUrl, cacheTime=CACHE_TIME_SHORT).content
            imageObj = DataObject(image, "image/jpeg")
            return imageObj
        except: 
            pass

    if(secondaryThumb != None):
        Log("Got a secondary thumb")
        try:
            image = HTTP.Request(secondaryThumb, cacheTime=CACHE_TIME_SHORT).content
            imageObj = DataObject(image, "image/jpeg")
            return imageObj
        except:
            Log("Failed to retreive secondary thumb")
            pass

    Log("No thumb could be loaded, using default")
    return Redirect(R(THUMB))


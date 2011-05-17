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

def GetIndexShows(sender):
    Log("GetIndexShows")
    showsList = MediaContainer(title1 = sender.title1, title2=TEXT_INDEX_SHOWS)
    xpathBase = "//div[@class='tab active']"
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href,'/t/')]")
    
    showsList.Extend(CreateShowList(programLinks))

    return showsList

def GetRecommendedShows(sender):
    Log("GetRecommendedShows")
    showsList = MediaContainer(title1 = sender.title1, title2=TEXT_RECOMMENDED_SHOWS)
    pages = GetPaginatePages(URL_RECOMMENDED_SHOWS, "pb")
    programLinks = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        pLinks = pageElement.xpath("//div[@id='pb']//div[@class='content']//li/a[starts-with(@href, '/t/')]")
        programLinks = programLinks + pLinks

    showsList.Extend(CreateShowList(programLinks, True))
    return showsList

def GetCategoryShows(sender, catUrl, catName):
    Log("GetCategoryShows %s" % catUrl)
    catShows = MediaContainer(title1 = sender.title2, title2=catName)
    pages = GetPaginatePages(catUrl, 'pb')
    programLinks = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        pLinks = pageElement.xpath("//div[@id='pb']//div[@class='content']//li/a[starts-with(@href, '/t/')]")
        programLinks = programLinks + pLinks

    catShows.Extend(CreateShowList(programLinks, True))
    return catShows 

def GetCategoryNewsShows(sender, catUrl, catName):
    Log("GetCategoryNewsShows")
    catShows = MediaContainer(title1=sender.title2, title2 = catName)
    pageElement = HTML.ElementFromURL(catUrl)
    links = pageElement.xpath("//div[@id='sb' or @id='se']//div[@class='content']//a")
    catShows.Extend(CreateShowList(links, True))
    return catShows

#This function wants a <a>..</a> tag
def CreateShowList(programLinks, isRecommendedShows = False):
    showsList = []
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
            thumbF = Function(GetShowThumb, showInfo=si, secondaryThumb=secondaryThumbUrl)
            showsList.append(Function(DirectoryItem(key=GetShowContents,title=showName, summary=si.info,
                thumb=thumbF), showInfo = si))
            #Log("DONE")
        else:
            thumbF = Function(GetShowThumb, showInfo=None, secondaryThumb=secondaryThumbUrl)
            showsList.append(Function(DirectoryItem(key=GetShowContents,title=showName, thumb=thumbF),
                showInfo = None, showUrl = showUrl, showName = showName))

    return showsList     


def GetShowContents(sender, showInfo, showUrl = None, showName = None):
    if(showUrl == None):
        Log("GetShowContents: %s, %s" %  (showInfo.name, showInfo.url))
        showUrl = showInfo.url
        showName = showInfo.name
    else:
        Log("GetShowContents(no showInfo):")

    list = MediaContainer(title1=sender.title2, title2=showName)
    list.Extend(GetShowCategories(showUrl))
    list.Extend(GetShowEpisodes(showUrl))

    return list

def GetShowCategories(showUrl=None):
    pages = GetPaginatePages(showUrl, "sb")
    catInfos = []
    for page in pages:
        catInfos = catInfos + GetCategoryInfosFromPage(page)

    catItems = []

    for catInfo in catInfos:
        f = Function(DirectoryItem(key=GetCategoryContents, title=catInfo.name, thumb=catInfo.thumbUrl), ci=catInfo)
        catItems.append(f)

    return catItems

def GetShowEpisodes(showUrl = None):
    pages = GetPaginatePages(showUrl, "sb")
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    epList = []
    for epUrl in epUrls:
        #Log("EPURL: %s" % epUrl)
        epInfo = GetEpisodeInfo(epUrl)
        epList.append(epInfo.GetMediaItem())
    return epList


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


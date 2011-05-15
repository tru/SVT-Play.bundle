# -*- coding: utf-8 -*

from common import *

class CategoryInfo:
    def __init__(self):
        self.url = None
        self.thumbUrl = None
        self.name = None
    def GetMediaItems(self):
        pages = GetPaginatePages(self.url, "sb")
        epUrls = []
        for page in pages:
            epUrls = epUrls + GetEpisodeUrlsFromPage(page)

        epList = []
        for epUrl in epUrls:
            #Log("EPURL: %s" % epUrl)
            epInfo = GetEpisodeInfo(epUrl)
            epList.append(epInfo.GetMediaItem())
        return epList

       
def GetCategoryContents(sender, ci):
    list = MediaContainer(title1=sender.title2, title2=ci.name)
    list.Extend(ci.GetMediaItems())
    return list

def GetCategoryInfosFromPage(url):
    Log("GetCategoryUrlsFromPage: %s" % url)
    catUrls = []
    pageElement = None
    try: 
        pageElement = HTML.ElementFromURL(url, cacheTime = CACHE_TIME_1DAY) 
    except:
        Log("page fetch fail")
        return None 

    catInfoList = []
    catElems = pageElement.xpath("//div[@id='sb']//div[@class='content']//li/a[@class='folder overlay tooltip']/..")
    for catElem in catElems:
        catName = catElem.xpath(".//span/text()")[0]
        catUrl = url + catElem.xpath(".//a/@href")[0]
        catThumbUrl = catElem.xpath(".//a//img[@class='folder-thumb']/@src")[0]
        Log("CatName:  %s" % catName)
        Log("CatUrl: %s" % catUrl)
        Log("CatThumbUrl: %s" % catThumbUrl)
        ci = CategoryInfo()
        ci.name = catName
        ci.url = catUrl
        ci.thumbUrl = catThumbUrl
        catInfoList.append(ci)

    return catInfoList

    

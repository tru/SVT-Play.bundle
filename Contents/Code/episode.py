# -*- coding: utf-8 -*

from common import *

class EpisodeInfo:
    def __init__(self):
        self.episodeUrl = None
        self.thumbNailUrl = None
        self.info = None
        self.length = 0
        self.qualities = dict()

def GetShowEpisodes(sender, showInfo, showUrl = None): 
    epList = []
    if(showUrl == None):
        Log("GetShowEpisodes: %s, %s" %  (showInfo.name, showInfo.url))
        showUrl = showInfo.url
    else:
        Log("GetShowEpisodes (no showInfo):")

    pages = GetPaginatePages(showUrl)
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    for epUrl in epUrls:
        Log("EPURL: %s" % epUrl)
        GetEpisodeInfo(epUrl)

    return epList

def GetEpisodeUrlsFromPage(url):
    epUrls = []
    pageElement = HTML.ElementFromURL(url)
    xpathbase = TAG_DIV_ID % "sb"
    episodeElements = pageElement.xpath(xpathbase + "//a[starts-with(@href,'/v/')]")
    for epElem in episodeElements:
        epUrl = URL_SITE + epElem.get("href")
        epUrls.append(epUrl)

    return epUrls

def GetEpisodeInfo(episodeUrl):
    Log(episodeUrl)
    
    pageElement = HTML.ElementFromURL(episodeUrl) 

    episodeImageUrl = str(pageElement.xpath("//meta[@property='og:image']/@content")[0])
    Log("Episode thumbnail: %s " % episodeImageUrl)
    
    infoElements = pageElement.xpath("//div[@id='description-episode']")
    episodeInfo = TEXT_NO_INFO
    if (len(infoElements) > 0):
        episodeInfo = infoElements[0].text.strip()
    
    moreInfoUrl = pageElement.xpath("//div[@class='info']//li[@class='episode']//a[starts-with(@href, '/popup')]") 
    if(len(moreInfoUrl) > 0):
        infoUrl = URL_SITE + moreInfoUrl[0].get("href")
        Log("MerInfoURL: %s " % infoUrl)
        infoElement = HTML.ElementFromURL(infoUrl)
        infoTexts = infoElement.xpath("//div[@id='wrapper']//p//text()")
        if(len(infoTexts) > 0):
            episodeInfo = infoTexts[0]
            Log(episodeInfo)
        
    episodeLengthMillis=""    
    lengthElements = pageElement.xpath(u"//div[@class='info']//span[contains(text(), 'Längd:')]")
    if (len(lengthElements) > 0):
        lengthText = lengthElements[0].tail.strip()
        (hours, minutes, seconds) = [0,0,0]
        hoursMatch = re.search(r'(\d+) tim',lengthText)
        minutesMatch = re.search(r'(\d+) min',lengthText)
        secondsMatch = re.search(r'(\d+) sek',lengthText)
        
        if (hoursMatch):
            hours = int(hoursMatch.group(1))
        if (minutesMatch):
            minutes = int(minutesMatch.group(1))
        if (secondsMatch):
            seconds = int(secondsMatch.group(1))
        
        Log("Episode length: %s %s %s" % (hours, minutes, seconds))
        episodeLengthMillis = "%d" % (1000 * (hours*60*60 + minutes*60 + seconds))
    
    # Get the url for the stream
    #contentUrl = GetContentUrl(episodeElements)
    #Log("Content url:" + contentUrl)
    #return (episodeInfo, episodeLengthMillis, contentUrl)
 
def BuildShowEpisodesMenu(url, divId):
    Log("BuildShowEpisodesMenu")
    menuItems = []
    pageElement = HTML.ElementFromURL(url)
    xpathBase = TAG_DIV_ID  % (divId)
    playerTest = pageElement.xpath("//div[@id='player']")
    Log(playerTest)
    if(len(playerTest)):
        Log("Found show page")
        showUrl = pageElement.xpath("//div[@id='player']//div[@class='layer']//div[@class='info']//a[starts-with(@href,'/t/')]")[0].get("href")
        #Compose the full URL
        paginateUrl = FindPaginateUrl(url)
        completeUrl = SITE_URL + showUrl + paginateUrl
        Log("CompleteURL: %s" % completeUrl)
        menuItems = Paginate(completeUrl % 1, completeUrl, divId, BuildGenericMenu)
        return menuItems



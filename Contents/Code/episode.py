# -*- coding: utf-8 -*

from common import *

class EpisodeInfo:
    def __init__(self):
        self.title = None
        self.episodeUrl = None
        self.thumbNailUrl = None
        self.info = None
        self.length = 0
        self.qualities = dict()

def GetShowEpisodes(sender, showInfo, showUrl = None, showName = None):
    if(showUrl == None):
        Log("GetShowEpisodes: %s, %s" %  (showInfo.name, showInfo.url))
        showUrl = showInfo.url
        showName = showInfo.name
    else:
        Log("GetShowEpisodes (no showInfo):")

    pages = GetPaginatePages(showUrl)
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    epList = MediaContainer(title1=showName)
    for epUrl in epUrls:
        Log("EPURL: %s" % epUrl)
        epInfo = GetEpisodeInfo(epUrl)
        contentUrl = GetContentUrlFromUserQualSettings(epInfo)
        epList.Append(VideoItem(key=contentUrl, title=epInfo.title, summary=epInfo.info, duration=epInfo.length,
            thumb=epInfo.thumbNailUrl, art=epInfo.thumbNailUrl))

    return epList

def GetContentUrlFromUserQualSettings(epInfo):
    #Log("DICTIONARY: %s" % epInfo.qualities)
    url = epInfo.qualities[Prefs['quality']]
    #Log("SELECTED CONTENT URL: %s" % url)
    return url

def GetEpisodeUrlsFromPage(url):
    epUrls = []
    pageElement = HTML.ElementFromURL(url)
    xpathbase = TAG_DIV_ID % "sb"
    episodeElements = pageElement.xpath(xpathbase + "//a[starts-with(@href,'/v/')]/@href")

    for epElem in episodeElements:
        epUrl = URL_SITE + epElem
        epUrls.append(epUrl)

    return epUrls

def GetEpisodeInfo(episodeUrl):
    Log(episodeUrl)

    pageElement = HTML.ElementFromURL(episodeUrl) 

    episodeImageUrl = str(pageElement.xpath("//meta[@property='og:image']/@content")[0])
    Log("Episode thumbnail: %s " % episodeImageUrl)

    episodeTitle = pageElement.xpath("//meta[@property='og:title']/@content")[0]
    episodeTitle = string.split(episodeTitle, "|")[0]

    infoElements = pageElement.xpath("//div[@id='description-episode']")
    episodeInfo = TEXT_NO_INFO
    moreInfoUrl = ""
    if (len(infoElements) > 0):
        episodeInfo = infoElements[0].text.strip()
        moreInfoUrl = infoElements[0].xpath("../a[@class='plus']/@href")

    if(len(moreInfoUrl) > 0):
        infoUrl = URL_SITE + moreInfoUrl[0]
        Log("MerInfoURL: %s " % infoUrl)
        infoElement = HTML.ElementFromURL(infoUrl)
        infoTexts = infoElement.xpath("//div[@id='wrapper']//p//text()")
        if(len(infoTexts) > 0):
            episodeInfo = infoTexts[0]
            Log(episodeInfo)

    episodeLengthMillis = 0    
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
        episodeLengthMillis =  (1000 * (hours*60*60 + minutes*60 + seconds))

    contentUrls = GetContentUrls(pageElement)

    hiresImage = GetHiResThumbNail(pageElement)
    if(hiresImage != None):
        episodeImageUrl = hiresImage

    epInfo = EpisodeInfo()
    epInfo.title = episodeTitle
    epInfo.episodeUrl = episodeUrl
    epInfo.thumbNailUrl = episodeImageUrl 
    epInfo.info = episodeInfo 
    epInfo.length = episodeLengthMillis 
    epInfo.qualities = contentUrls

    return epInfo 

def GetHiResThumbNail(pageElement):
    imageTag = "background="
    flashvars = pageElement.xpath("(//div[@class='video']//param[@name='flashvars'])[1]/@value") 

    if(len(flashvars) > 0):
        flashvars = flashvars[0]
    else:
        return None

    index = string.find(flashvars, imageTag) 
    index = index + len(imageTag)
    indexAnd = string.find(flashvars, "&", index)
    #Log("INDEXES %d, %d" % (index, indexAnd))
    if(index > -1 and indexAnd > index):
        bgimage = flashvars[index:indexAnd]
        #Log("NEW BG IMAGE: %s" % bgimage)
        return bgimage
    return None

def GetContentUrls(pageElement):
    flashvars = pageElement.xpath("(//div[@class='video']//param[@name='flashvars'])[1]/@value") 
    d = dict()

    Log("Flashvars: %s" % flashvars)
    if(len(flashvars) > 0):
        flashvars = flashvars[0]
        urls = string.split(flashvars, "url:")
        for url in urls:
            Log("Content URLS: %s" % url)
            if(string.find(url, "rtmp") > -1):
                SetQuality(url, d)
        Log("QualDict: %s" % d)
    
    SetHighestQuality(d)
    return d

def SetQuality(contentUrl, d):
    s = string.split(contentUrl, ',')
    Log("SetQuality: %s " % s)
    if(string.find(s[1], '2400') > -1):
        d[QUAL_T_HIGHEST] = s[0]
        d[QUAL_T_HD] = s[0]
    elif(string.find(s[1], '1400') > -1):
        d[QUAL_T_HIGH] = s[0]
    elif(string.find(s[1], '850') > -1):
        d[QUAL_T_MED] = s[0]
    else:
        d[QUAL_T_LOW] = s[0]

def SetHighestQuality(d):
    try:
        highest = d[QUAL_T_LOW]
        d[QUAL_T_HIGHEST] = highest
    except KeyError:
        Log("No low quality")
    try:
        highest = d[QUAL_T_MED]
        d[QUAL_T_HIGHEST] = highest
    except KeyError:
        Log("No med quality")
    
    try:
        highest = d[QUAL_T_HIGH]
        d[QUAL_T_HIGHEST] = highest
    except KeyError:
        Log("No high quality")

    try:
        highest = d[QUAL_T_HD]
        d[QUAL_T_HIGHEST] = highest
    except KeyError:
        Log("No hd  quality")


        

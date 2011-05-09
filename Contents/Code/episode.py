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
        self.flashArgs = dict()
        self.isLive = False

def GetShowEpisodes(sender, showInfo, showUrl = None, showName = None):
    if(showUrl == None):
        Log("GetShowEpisodes: %s, %s" %  (showInfo.name, showInfo.url))
        showUrl = showInfo.url
        showName = showInfo.name
    else:
        Log("GetShowEpisodes (no showInfo):")

    pages = GetPaginatePages(showUrl, "sb")
    epUrls = []
    for page in pages:
        epUrls = epUrls + GetEpisodeUrlsFromPage(page)

    epList = MediaContainer(title1=showName)
    for epUrl in epUrls:
        #Log("EPURL: %s" % epUrl)
        epInfo = GetEpisodeInfo(epUrl)
        contentUrl = GetContentUrlFromUserQualSettings(epInfo)
        if(contentUrl.endswith('.flv')):
            epList.Append(VideoItem(key=contentUrl, title=epInfo.title, summary=epInfo.info, duration=epInfo.length,
                thumb=epInfo.thumbNailUrl, art=epInfo.thumbNailUrl))
        else:
            epList.Append(Function(VideoItem(key=PlayVideo, title=epInfo.title, summary=epInfo.info,
                duration=epInfo.length, thumb=epInfo.thumbNailUrl, art=epInfo.thumbNailUrl), url=contentUrl))

    return epList

def PlayVideo(sender, url):
    Log("Request to play video: %s" % url)
    return Redirect(WebVideoItem(url))


def GetContentUrlFromUserQualSettings(epInfo):
    try:
        url = epInfo.qualities[Prefs['quality']]
    except KeyError:
        url = epInfo.qualities[QUAL_T_HIGHEST]

    if(string.find(url, "rtmp") > -1):
        if (url.endswith('.mp4')):
            #special case rmpte stream with mp4 ending.
            url = URL_PLEX_PLAYER + url.replace("_definst_/","_definst_&clip=mp4:")
        else:
            url = URL_PLEX_PLAYER + url.replace("_definst_/","_definst_&clip=")

    if(epInfo.isLive):
        url = re.sub(r'^(.*)/(.*)$','\\1&clip=\\2', url)
        url = url +"&live=true&width=640&height=360"

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
    epInfo = EpisodeInfo()

    pageElement = HTML.ElementFromURL(episodeUrl, cacheTime = CACHE_TIME_EPISODE)
    (contentUrls, flashArgs) = GetContentUrls(pageElement)

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
        #Log("moreInfoUrl: %s " % infoUrl)
        infoElement = HTML.ElementFromURL(infoUrl)
        infoTexts = infoElement.xpath("//div[@id='wrapper']//p//text()")
        if(len(infoTexts) > 0):
            episodeInfo = infoTexts[0]
            Log(episodeInfo)

    try:
        epLength = flashArgs['length']
        if(len(epLength) > 0):
            epLength = int(epLength)
        else:
            epLength = 0
        #Log("New Length millis: %d" % (int(epLength) * 1000))
        epLength = epLength * 1000
    except KeyError:
        Log("No length found :(")

    try:
        if(len(flashArgs['liveStart']) > 0):
            epInfo.isLive = True
            episodeTitle = TEXT_LIVE + episodeTitle
            #Log("IS LIVE")
    except KeyError:
        Log('liveStart not found')

    hiresImage = GetHiResThumbNail(pageElement)
    if(hiresImage != None):
        episodeImageUrl = hiresImage
    else:
        episodeImageUrl = str(pageElement.xpath("//meta[@property='og:image']/@content")[0])
    HTTP.PreCache(episodeImageUrl, cacheTime = CACHE_TIME_EPISODE)

    epInfo.title = episodeTitle
    epInfo.episodeUrl = episodeUrl
    epInfo.thumbNailUrl = episodeImageUrl 
    epInfo.info = episodeInfo 
    epInfo.length = epLength 
    epInfo.qualities = contentUrls
    epInfo.flashArgs = flashArgs

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

    #Log("Flashvars: %s" % flashvars)
    if(len(flashvars) > 0):
        flashvars = flashvars[0]
#We can either get rtmp streams or flv
        if(string.find(flashvars, "dynamicStreams") > -1):
            urls = string.split(flashvars, "url:")
            for url in urls:
                #Log("Content URLS: %s" % url)
                if(string.find(url, "rtmp") > -1):
                    SetQuality(url, d)
            #Log("QualDict: %s" % d)
            SetHighestQuality(d)
        else:
           tag = "pathflv="
           index = string.find(flashvars, tag)
           index = index + len(tag)
           indexAnd = string.find(flashvars, "&", index)
           if(index > -1 and indexAnd > -1):
               url = flashvars[index:indexAnd]
               Log("FLV file: %s" % url)
               d[QUAL_T_HIGHEST] = url 
               d[QUAL_T_HD] = url 
               d[QUAL_T_HIGH] = url 
               d[QUAL_T_MED] = url 
               d[QUAL_T_LOW] = url 

    args = GetUrlArgs(flashvars) 
    return (d, args)

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


        

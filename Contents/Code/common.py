# -*- coding: utf-8 -*

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION="3.1"
PLUGIN_PREFIX	= "/video/svt"

PLEX_CLIP_PLAYER_URL = "http://www.plexapp.com/player/player.php?clip="

#URLs
URL_SITE = "http://svtplay.se"
URL_INDEX = URL_SITE + "/alfabetisk"
URL_INDEX_THUMB_PAGINATE = "?am,,%d,thumbs"
URL_INDEX_THUMB = URL_INDEX + URL_INDEX_THUMB_PAGINATE
URL_PLEX_PLAYER = "http://www.plexapp.com/player/player.php?&url="
URL_LIVE = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1596757,1,f,"

#Texts
TEXT_LIVE_SHOWS = u'Livesändningar'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_TITLE = u'SVT Play'
TEXT_NO_INFO = u'Ingen information hittades'
TEXT_PREFERENCES = u'Inställningar'

TEXT_LIVE = u'LIVE: '

#The page step function will only step this many pages deep. Can be changed / function call.
MAX_PAGINATE_PAGES = 100

ART = "art-default.jpg"
THUMB = 'icon-default.png'

CACHE_TIME_LONG    = 60*60*24*30 # Thirty days
CACHE_TIME_SHORT   = 60*10    # 10  minutes
CACHE_TIME_SHOW = CACHE_TIME_SHORT
CACHE_TIME_EPISODE = CACHE_TIME_LONG

#Quality shorts...
QUAL_HD = 0
QUAL_HIGH = 1
QUAL_MED = 2
QUAL_LOW = 3

#These must match text strings in DefaultPrefs.json
QUAL_T_HIGHEST = u"Högsta"
QUAL_T_HD = u"HD"
QUAL_T_HIGH = u"Hög"
QUAL_T_MED = u"Medel"
QUAL_T_LOW = u"Låg"

#Prefs settings
PREF_QUALITY = 'quality'

#random stuff
TAG_DIV_ID = "//div[@id='%s']" 


def FindPaginateUrl(url, divId):
    pageElement = HTML.ElementFromURL(url)
    #Pick the first a href after the pagination div tag and treat it as the base link
    xbasepath = "(//div[@id='%s']//div[@class='pagination']//a)[1]/@href" % divId
    paginateUrl = pageElement.xpath(xbasepath)[0]
    #Replace the index number in the url to a %d so that we can easily loop over all the pages
    p2 = string.split(paginateUrl, ',')
    p2[len(p2) - 3] = "%d"
    paginateUrl =  string.join(p2, ',')
    return paginateUrl

def GetPaginatePages(url, divId, paginateUrl = None):
    requestUrl = url
    if(paginateUrl == None):
        paginateUrl = FindPaginateUrl(url, divId)
    else: #ugly special case for the alphabetic thumbs thing
        requestUrl = url + (paginateUrl % 1)

    pageElement = HTML.ElementFromURL(requestUrl)
    xpathBase = TAG_DIV_ID  % divId 
    paginationLinks = pageElement.xpath(xpathBase + "//div[@class='pagination']//li[@class='']/a")
    start = 1
    linkPages = len(paginationLinks)
    if(linkPages > 0): 
        stop = int(paginationLinks[linkPages-1].text)
    else:
        stop = 1

    Log("Start: %s, Stop: %s" % (start, stop))

    paginatePages = []
    for i in range(start, stop + 1):
        nextUrl = url + paginateUrl % i
        paginatePages.append(nextUrl)
    
    for newUrl in paginatePages:
        Log(newUrl)
        HTTP.PreCache(newUrl)
    
    return paginatePages


def GetUrlArgs(url):
    args = string.split(url, '&')
    d = dict()
    for arg in args:
        a = string.split(arg, '=')
        if(len(a) > 1):
           d[a[0]] = a[1]
    return d

# Replaces all running whitespace characters with a single space
def strip_all(str):
    return string.join(string.split(str), ' ')
 
class MoreInfoPopup:
    def __init__(self, pageElement):
        self.pageElement = pageElement
        self.xbasepath = "//div[@id='wrapper']//p[%d]/text()"
        self.episodeInfo = pageElement.xpath(self.xbasepath % 1)[0]
        self.showInfo = pageElement.xpath(self.xbasepath % 2)[0]

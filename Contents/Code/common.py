# -*- coding: utf-8 -*

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION="3.1"
PLUGIN_PREFIX	= "/video/svt"

#URLs
URL_SITE = "http://svtplay.se"
URL_INDEX = URL_SITE + "/alfabetisk"
URL_INDEX_THUMB_PAGINATE = "?am,,%d,thumbs"
URL_INDEX_THUMB = URL_INDEX + URL_INDEX_THUMB_PAGINATE
URL_PLEX_PLAYER = "http://www.plexapp.com/player/player.php?&url="
URL_LIVE = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1596757,1,f,"
URL_RECOMMENDED_SHOWS = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1364142,1,f,"
URL_LATEST_CLIPS = "http://svtplay.se/?cb,a1364145,1,f,/pb,a1364142,1,f,-1"
URL_LATEST_SHOWS = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1364143,1,f,"
URL_LATEST_NEWS = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1527537,1,f,"
URL_MOST_VIEWED = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1364144,1,f,"
URL_CATEGORIES = "http://svtplay.se/kategorier"
URL_CAT_CHILD = "http://svtplay.se/c/96251/barn"
URL_CAT_MOVIE_DRAMA = "http://svtplay.se/c/96257/film_och_drama"
URL_CAT_CULTURE = "http://svtplay.se/c/96256/kultur_och_noje"
URL_CAT_FACT = "http://svtplay.se/c/96254/samhalle_och_fakta"
URL_CAT_NEWS = "http://svtplay.se/c/96255/nyheter"
URL_CAT_SPORT = "http://svtplay.se/c/96253/sport"

#Texts
TEXT_LIVE_SHOWS = u'Livesändningar'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_TITLE = u'SVT Play'
TEXT_NO_INFO = u'Ingen information hittades'
TEXT_PREFERENCES = u'Inställningar'
TEXT_RECOMMENDED_SHOWS = u'Rekommenderat'
TEXT_LATEST_CLIPS = u'Senaste klipp'
TEXT_LATEST_SHOWS = u'Senaste program'
TEXT_LATEST_NEWS = u'Senaste nyhetsprogram'
TEXT_MOST_VIEWED = u'Mest sedda'
TEXT_CATEGORIES = u'Kategorier'
TEXT_CAT_CHILD = u'Barn'
TEXT_CAT_MOVIE_DRAMA = u'Film & Drama'
TEXT_CAT_CULTURE = u'Kultur & Nöje'
TEXT_CAT_FACT = u'Samhälle & Fakta'
TEXT_CAT_NEWS = u'Nyheter'
TEXT_CAT_SPORT = u'Sport'

TEXT_LIVE = u'LIVE: '
TEXT_LIVE_CURRENT = u'JUST NU: '

#The page step function will only step this many pages deep. Can be changed / function call.
MAX_PAGINATE_PAGES = 5

ART = "art-default.jpg"
THUMB = 'icon-default.png'

CACHE_TIME_LONG    = 60*60*24*30 # Thirty days
CACHE_TIME_SHORT   = 60*10    # 10  minutes
CACHE_TIME_1DAY    = 60*60*24
CACHE_TIME_SHOW = CACHE_TIME_1DAY
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
PREF_PAGINATE_DEPTH = 'paginate_depth'

#random stuff
TAG_DIV_ID = "//div[@id='%s']" 

def PlayVideo(url):
    Log("Request to play video: %s" % url)
    return Redirect(WebVideoItem(url))
    
def GetThumb(url):
    try:
        data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
        return DataObject(data, 'image/jpeg')
    except:
        return Redirect(R(THUMB))

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

def GetPaginatePages(url, divId, paginateUrl = None, maxPaginateDepth = MAX_PAGINATE_PAGES):
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
        stop = min(stop, maxPaginateDepth)
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
    def EpisodeInfo(self):
        episodeInfo = self.pageElement.xpath(self.xbasepath % 1)
        if(len(episodeInfo) > 0):
            return episodeInfo[0]
        return None

    def ShowInfo(self):
        showInfo = self.pageElement.xpath(self.xbasepath % 2)
        if(len(showInfo) > 0):
            return showInfo[0]
        return None

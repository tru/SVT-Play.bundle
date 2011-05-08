# -*- coding: utf-8 -*

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION="3.1"
PLUGIN_PREFIX	= "/video/svt"

PLEX_CLIP_PLAYER_URL = "http://www.plexapp.com/player/player.php?clip="
LIVE_URL = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1596757,1,f,"

#URLs
URL_SITE = "http://svtplay.se"
URL_INDEX = URL_SITE + "/alfabetisk"
URL_INDEX_THUMB = URL_INDEX + "?am,,%d,thumbs"
URL_PLEX_PLAYER = "http://www.plexapp.com/player/player.php?&url="
 

#Texts
TEXT_LIVE_SHOWS = u'Livesändningar'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_TITLE = "SVT Play"
TEXT_NO_INFO = "Ingen information hittades"

#The page step function will only step this many pages deep. Can be changed / function call.
MAX_PAGINATE_PAGES = 100

ART = "art-default.jpg"

CACHE_TIME_LONG    = 60*60*24*30 # Thirty days
CACHE_TIME_SHORT   = 60*10    # 5 minutes

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


def Paginate(startUrl, requestUrl, divId, callFunc, maxPages = MAX_PAGINATE_PAGES):
    Log("Pagination in progress...")
    menuItems = []
    pageElement = HTML.ElementFromURL(startUrl)
    xpathBase = TAG_DIV_ID  % (divId)
    paginationLinks = pageElement.xpath(xpathBase + "//div[@class='pagination']//li[@class='']/a")
    Log("Pagination links len: %d" % len(paginationLinks))
    start = 1
    linkPages = len(paginationLinks)
    if(linkPages > 0): 
        stop = int(paginationLinks[linkPages-1].text)
        stop = min(stop, maxPages)
    else:
        stop = 1

    Log("Start: %s, Stop: %s" % (start, stop))

    for i in range(start, stop + 1):
        nextUrl = requestUrl % i
        Log("Precaching %s" % nextUrl)
        HTTP.PreCache(nextUrl)

    for i in range(start, stop + 1):
        nextUrl = requestUrl % i
        Log(nextUrl)
        menuItems = menuItems + callFunc(nextUrl, divId)
    return menuItems

def FindPaginateUrl(url):
    pageElement = HTML.ElementFromURL(url)
    #Pick the first a href after the pagination div tag and treat it as the base link
    paginateUrl = pageElement.xpath("//div[@class='pagination']//a[starts-with(@href,'?')]")[0].get("href")
    #Replace the index number in the url to a %d so that we can easily loop over all the pages
    p2 = string.split(paginateUrl, ',')
    p2[len(p2) - 3] = "%d"
    paginateUrl =  string.join(p2, ',')
    return paginateUrl

def GetPaginatePages(url):
    paginateUrl = FindPaginateUrl(url)
    pageElement = HTML.ElementFromURL(url)
    xpathBase = TAG_DIV_ID  % "sb"
    paginationLinks = pageElement.xpath(xpathBase + "//div[@class='pagination']//li[@class='']/a")
    Log("Pagination links len: %d" % len(paginationLinks))
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
    
    for url in paginatePages:
        Log(url)
        HTTP.PreCache(nextUrl)
    
    return paginatePages

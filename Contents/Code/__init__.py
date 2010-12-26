# -*- coding: utf-8 -*
#from PMS import *
#from PMS.Objects import *

import re
import string

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION="1.3"

PLEX_PLAYER_URL = "http://www.plexapp.com/player/player.php?&url="
PLEX_CLIP_PLAYER_URL = "http://www.plexapp.com/player/player.php?clip="
PLUGIN_PREFIX	= "/video/svt"
SITE_URL		= "http://svtplay.se"
LATEST_SHOWS_URL = "http://svtplay.se/?/pb,a1364143,%d,f,-1"
MOST_VIEWED_URL = "http://svtplay.se/?/pb,a1364144,%d,f,-1"
RECOMMENDED_URL = "http://svtplay.se/?/pb,a1364142,%d,f,-1"
LATEST_VIDEOS_URL = "http://svtplay.se/?/cb,a1364145,%d,f,-1"
LATEST_NEWS_SHOWS_URL = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1527537,%d,f,-1"
LIVE_URL = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1596757,1,f,"
CATEGORIES_URL = SITE_URL + "/kategorier"
INDEX_URL = SITE_URL + "/alfabetisk?am,,%d,thumbs"


#Texts
NO_INFO = u'Beskrivning saknas.'
LATEST_SHOWS = u'Senaste program'
LATEST_NEWS_SHOWS = u'Senaste nyhetsprogram'
LATEST_VIDEOS = u'Senaste klipp'
RECOMMENDED = u'Rekommenderat'
MOST_VIEWED = u'Mest sedda'
LIVE_SHOWS = u'Livesändningar'
INDEX_SHOWS = u'Program A-Ö'

#The page step function will only step this many pages deep. Can be changed / function call.
MAX_PAGINATE_PAGES = 100

ART = "art-default.jpg"

CACHE_TIME_LONG    = 60*60*24*30 # Thirty days
CACHE_TIME_SHORT   = 60*10    # 5 minutes

# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def Start():
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, "SVT Play", "icon-default.png", "art-default.jpg")
    HTTP.CacheTime = CACHE_TIME_SHORT
    #HTTP.PreCache(INDEX_URL % 1)
    #HTTP.PreCache(LATEST_SHOWS_URL % 1)
    #HTTP.PreCache(MOST_VIEWED_URL % 1)
    #HTTP.PreCache(RECOMMENDED_URL % 1)
    #HTTP.PreCache(LATEST_VIDEOS_URL % 1)
    #HTTP.PreCache(LATEST_NEWS_SHOWS_URL % 1)
    #HTTP.PreCache(CATEGORIES_URL)
    MediaContainer.art = R(ART)

def CreateDict():
    Log("CreateDict")

def CreatePrefs():
    Log("CreatePrefs")

# Handler function called on each request
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def HandleRequest(pathNouns, count):

    # Initialize 
    # - - - - - - - - - - - - - - -
    menuItems = []
    viewGroup = "InfoList"
    Log.Add("\n\n\n- - - - - - - - - - - - - - - \nRequest %s %s" % (count,pathNouns))
    
    # Static menus (Hard-coded url)
    # - - - - - - - - - - - - - -
    if key == '': # No parameters, show main menu
        menuItems.extend(BuildMainMenu())
        viewGroup = "List"
    
    if key == "categories":
        menuItems.extend(BuildCategoriesMenu())
        viewGroup = "List"    
   
    if key == "most_viewed":
        menuItems.extend(Paginate(MOST_VIEWED_URL % 1, MOST_VIEWED_URL, "pb"))

    if key == "live":
        menuItems.extend(BuildLiveMenu())   
    
    # Dynamic menus (parametrized url)
    # - - - - - - - - - - - - - - - - -
    if key == "category":
        
        # Generally the contents are in the "pb" (program browser) div
        divIds = ["pb"]
        
        # Some special cases tho...
        if url.endswith("oppet_arkiv") or url.endswith("sport"):
            divIds = ["sb"]
        if url.endswith("nyheter"):
            divIds = ["sb","se"] # Separate divs for "nyheter" and "lokalnyheter"
        
        for divId in divIds:
           menuItems.extend(BuildGenericMenu(url,divId,paginate=True))
           
    if key == "program":
        menuItems.extend(BuildGenericMenu(url,"sb"))
        
    # Create and return mediacontainer    
    menu = MediaContainer('art-default.jpg', title1="SVT Play " + VERSION, title2=unicode(title,'utf-8'), viewGroup=viewGroup)
    for menuItem in menuItems:
        menu.AppendItem(menuItem)
    if (len(menuItems) == 0):
        menu.SetMessage(u'Innehåll saknas',u'Det finns inget innehåll under detta menyval för tillfället.\nPröva igen vid ett senare tillfälle.')
    
    Log.Add("%d items added to menu" % (len (menuItems)))
    return menu.ToXML()
   
    
 
    
# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def MainMenu():
    menu = MediaContainer(viewGroup="List")
    menu.Append(Function(DirectoryItem(ListRecommended, title=RECOMMENDED, thumb=R('main_rekommenderat.png'))))
    menu.Append(Function(DirectoryItem(ListMostViewed, title=MOST_VIEWED, thumb=R('main_mest_sedda.png'))))
    menu.Append(Function(DirectoryItem(ListLatestShows, title=LATEST_SHOWS, thumb=R('main_senaste_program.png'))))
    menu.Append(Function(DirectoryItem(ListLatestNewsShows, title=LATEST_NEWS_SHOWS, thumb=R('category_nyheter.png'))))
    #menu.Append(Function(DirectoryItem(ListLatestVideos, title=LATEST_VIDEOS, thumb=R('main_senaste_klipp.png'))))
    menu.Append(Function(DirectoryItem(ListAllShows, title=INDEX_SHOWS, thumb=R('main_index.png'))))
    menu.Append(PrefsItem(u"Inställningar"))
    #menuItems.append(DirectoryItem(BuildArgs("categories", "", u'Kategorier'), u'Välj kategori', Plugin.ExposedResourcePath('main_kategori.png')))
    #menuItems.append(DirectoryItem(BuildArgs("live", "",u'Livesändningar'), u'Livesändningar', Plugin.ExposedResourcePath('main_live.png')))
    return menu

def ListAllShows(sender):
    Log("ListAllShows")
    showsList = MediaContainer()
    showsList.Extend(Paginate(INDEX_URL % 1, INDEX_URL, "am", IndexShows))
    return showsList

def IndexShows(url, divId):
    Log("Index Shows...")
    # Note: must have "span" element, otherwise some wierd stuff can come along...
    xpathBase = "//div[@id='%s']" % (divId)
    pageElement = HTML.ElementFromURL(url)
    programLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href, '/t/')]/span/..")
    programUrls = [] 
    for programLink in programLinks:
        newUrl = SITE_URL + programLink.get("href")
        programUrls.append(newUrl)
        Log("Program URL!!! --> %s" % newUrl)
        HTTP.PreCache(newUrl)

    return BuildGenericMenu(url, divId)
    
def ListLatestShows(sender):
    Log("ListLatestShows")
    showsList = MediaContainer()
    #Paginate only a few pages...
    showsList.Extend(Paginate(LATEST_SHOWS_URL % 1, LATEST_SHOWS_URL, "pb", BuildGenericMenu, 3))
    return showsList

def ListLatestNewsShows(sender):
    Log("ListLatestNewsShows")
    showsList = MediaContainer()
    #Paginate only a few pages
    showsList.Extend(Paginate(LATEST_NEWS_SHOWS_URL % 1, LATEST_NEWS_SHOWS_URL, "pb", BuildGenericMenu, 3))
    return showsList

def ListLatestVideos(sender):
    Log("ListLatestVideos")
    showsList = MediaContainer()
    #Paginate only a few pages
    showsList.Extend(Paginate(LATEST_VIDEOS_URL % 1, LATEST_VIDEOS_URL, "cb", BuildGenericMenu, 3))
    Log("Clips %d" % len(showsList))
    return showsList

def ListRecommended(sender):
    Log("ListRecommended")
    showsList = MediaContainer()
    #Paginate only a few pages
    showsList.Extend(Paginate(RECOMMENDED_URL % 1, RECOMMENDED_URL, "pb", BuildGenericMenu))
    return showsList

def ListMostViewed(sender):
    Log("ListMostViewed")
    showsList = MediaContainer()
    #Paginate only a few pages...
    showsList.Extend(Paginate(MOST_VIEWED_URL % 1, MOST_VIEWED_URL, "pb", BuildGenericMenu))
    return showsList



def BuildCategoriesMenu():
    menuItems = []
    for element in HTML.ElementFromURL(CATEGORIES_URL).xpath("//li/div[@class='container']/a"):
        categoryName = element.xpath("span[@class='category-header']/text()")[0]
        categoryUrl = SITE_URL + element.get("href")
        categoryIconName = "category_" + re.search(r'(\w+)$',categoryUrl).group(1) + ".png"
        Log("Icon name: " + categoryIconName)
        #categoryIcon = element.xpath("img")[0].get("src")
        menuItems.append(DirectoryItem(BuildArgs("category",categoryUrl,categoryName), categoryName, Plugin.ExposedResourcePath(categoryIconName)))
    return menuItems
    
def BuildLiveMenu():
    menuItems = []
    liveElements = HTML.ElementFromURL(LIVE_URL)
    for element in liveElements.xpath("//a[@class='tableau']"):
        liveName = strip_all(unicode(element.xpath("../../../h3/text()")[0]))        
        liveUrl = SITE_URL +  element.get("href")
       
        # Get the actual stream url from subpage and do some munging for the plex player to get it
        liveContentUrl = GetEpisodeInfo(liveUrl)[2]
        liveContentUrl = re.sub(r'^(.*)/(.*)$','\\1&clip=\\2', liveContentUrl)
        liveContentUrl = PLEX_PLAYER_URL + liveContentUrl +"&live=true&width=640&height=360"
       
        Log("Live content url: " + liveContentUrl)
        liveIcon = element.xpath("span/span[starts-with(@class,'flashcontent')]/img")[0].get("src")      
        liveDesc = strip_all(unicode(element.xpath("span[@class='description']/text()")[0]))
        menuItems.append(WebVideoItem(liveContentUrl, liveName,liveDesc, "0",liveIcon))
        
    return menuItems

def Paginate(startUrl, requestUrl, divId, callFunc, maxPages = MAX_PAGINATE_PAGES):
    Log("Pagination in progress...")
    menuItems = []
    pageElement = HTML.ElementFromURL(startUrl)
    xpathBase = "//div[@id='%s']" % (divId)
    paginationLinks = pageElement.xpath(xpathBase + "//div[@class='pagination']//li[@class='']/a")
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
        #menuItems = menuItems + BuildGenericMenu(nextUrl, divId)
        menuItems = menuItems + callFunc(nextUrl, divId)
    return menuItems

def BuildShowEpisodesMenu(showUrl, divId):
    #This section determines if we are on a page for a program (show)
    #If so it will extract all the shows episodes via paginating and then return the list
    Log("BuildShowEpisodesMenu")
    menuItems = []
    pageElement = HTML.ElementFromURL(showUrl)
    xpathBase = "//div[@id='%s']" % (divId)
    playerTest = pageElement.xpath("//div[@id='player']")
    Log(playerTest)
    if(len(playerTest)):
        Log("Found show page")
        showUrl = pageElement.xpath("//div[@id='player']//div[@class='layer']//div[@class='info']//a[starts-with(@href,'/t/')]")[0].get("href")
        #Pick the first a href after the pagination div tag and treat it as the base link
        paginateUrl = pageElement.xpath(xpathBase + "//div[@class='pagination']//a[starts-with(@href,'?')]")[0].get("href")
        #Replace the index number in the url to a %d so that we can easily loop over all the pages
        p2 = string.split(paginateUrl, ',')
        p2[len(p2) - 3] = "%d"
        paginateUrl =  string.join(p2, ',')
        #Compose the full URL
        completeUrl = SITE_URL + showUrl + paginateUrl
        Log("CompleteURL: %s" % completeUrl)
        menuItems = Paginate(completeUrl % 1, completeUrl, divId, BuildGenericMenu)
        return menuItems

# Main method for sucking out svtplay content
def BuildGenericMenu(url, divId, paginate=False):
    menuItems = []
    pageElement = HTML.ElementFromURL(url)
    Log("url: %s divId: %s" % (url, divId))
    xpathBase = "//div[@id='%s']" % (divId)
    Log("xpath expr: " + xpathBase)

    clipLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href,'/v/')]")
    for clipLink in clipLinks:
        clipName = clipLink.xpath("span/text()")[0].strip()
        Log("Clip : %s" % (clipName.encode('utf8')))
        clipUrl = SITE_URL + clipLink.get("href")
        Log("URL: " + clipUrl)
        clipIcon = clipLink.xpath("img")[0].get("src").replace("_thumb","_start")
        Log("Clip icon: >" + clipIcon + "<")
        (clipSummary, clipLength, contentUrl) = GetEpisodeInfo(clipUrl) 
        if (contentUrl.endswith('.flv')):
            Log("Old Content URL %s" % contentUrl)
            contentUrl = PLEX_CLIP_PLAYER_URL + contentUrl
            Log("New Content URL %s" % contentUrl)
            menuItems.append(Function(VideoItem(PlayFLV, clipName, clipSummary, clipLength,clipIcon), url=contentUrl))
        else:
            # should be rtmp url
            if (contentUrl.endswith('.mp4')):
               #special case rmpte stream with mp4 ending.
               contentUrl = PLEX_PLAYER_URL + contentUrl.replace("_definst_/","_definst_&clip=mp4:")
            else:
                contentUrl = PLEX_PLAYER_URL + contentUrl.replace("_definst_/","_definst_&clip=")
            menuItems.append(Function(VideoItem(PlayVideo, clipName, summary=clipSummary, thumb=clipIcon, duration=clipLength), url=contentUrl))
        
    # Note: must have "span" element, otherwise some wierd stuff can come along...
    programLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href, '/t/')]/span/..")
    for programLink in programLinks:
        programName = programLink.xpath("span/text()")[0].strip()
        Log("Program : %s" % (programName.encode('utf8')))
        programUrl = SITE_URL + programLink.get("href")
        programIcon = programLink.xpath("img")[0].get("src") #GetHiResIconFromSubPage(programUrl)
        programSummary = GetProgramInfo(programUrl)
        menuItems.append(Function(DirectoryItem(ListShowEpisodes, programName, summary=programSummary, thumb=programIcon), showName = programName, showUrl = programUrl))

    # Subcategories (used in "Bolibompa" and maybe more)
    subCategoryLinks = pageElement.xpath(xpathBase + "//a[@class='folder overlay tooltip']/span/..")
    for subCategoryLink in subCategoryLinks:
        subCategoryName = subCategoryLink.xpath("span/text()")[0].strip()
        subCategoryUrl = url + subCategoryLink.get("href")
        subCategoryImage = subCategoryLink.xpath("img[@class='folder-thumb']")[0].get("src")
        menuItems.append(DirectoryItem(BuildArgs("program",subCategoryUrl,subCategoryName),subCategoryName,subCategoryImage,NO_INFO))

    # Do pagination if requested 
    if (paginate):
        paginationLinks = pageElement.xpath(xpathBase + "//div[@class='pagination']//li[@class='']/a")
        # Max three pages will do... Getting more pages will be harder as not all page links are shown.
        for paginationLink in paginationLinks[:3]:
            pageUrl = url + "?" + paginationLink.get("href")
            Log("Paginating using url: %s" % (pageUrl))
            menuItems.extend(BuildGenericMenu(pageUrl, divId, paginate=False))
        
    return menuItems
    
def ListShowEpisodes(sender, showName, showUrl):
    Log("ListShowEpisodes: %s, %s" %  (showName, showUrl))
    epList = MediaContainer()
    episodes = BuildShowEpisodesMenu(showUrl, "sb")
    for ep in episodes:
        Log(ep)
        epList.Append(ep)
    Log("Added %s items" % len(epList))
    return epList

def PlayVideo(sender, url):
    Log("Request to play video: %s" % url)
    return Redirect(WebVideoItem(url))


def PlayFLV(sender, url):
    Log("Request to play FLV: %s" % url)
    return Redirect(VideoItem(url)) 

# Helpers
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
def GetProgramInfo(programUrl):
    programHtml = HTTP.Request(programUrl)
    infoElements = HTML.ElementFromString(programHtml).xpath("//div[@id='description-title']")
    if (len(infoElements) > 0):
        return infoElements[0].text.strip()
    return NO_INFO
     
def GetEpisodeInfo(episodeUrl):
    episodeHtml = HTTP.Request(episodeUrl)
    episodeElements = HTML.ElementFromString(episodeHtml)
    infoElements = episodeElements.xpath("//div[@id='description-episode']")
    episodeInfo = NO_INFO
    if (len(infoElements) > 0):
        episodeInfo = infoElements[0].text.strip()
    
    episodeLengthMillis=""    
    lengthElements = episodeElements.xpath(u"//div[@class='info']//span[contains(text(), 'Längd:')]")
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
    contentUrl = GetContentUrl(episodeElements)
    Log("Content url:" + contentUrl)
    return (episodeInfo, episodeLengthMillis, contentUrl)
    
def GetContentUrl(pageElement):
    flashvars = pageElement.xpath("//object[@id='playerSwf']/param[@name='flashvars']")[0].get("value")
    # return the pathflv OR the first dynamicStream URL. Never mind choosing what bitrate
    return re.search(r'(pathflv=|dynamicStreams=url:)(.*?)[,&$]',flashvars).group(2)    

# Replaces all running whitespace characters with a single space
def strip_all(str):
    return string.join(string.split(str), ' ')
    

        

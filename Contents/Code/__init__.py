# -*- coding: utf-8 -*

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
CATEGORIES = u'Kategorier'

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
#"values":["Högsta", "HD", "Hög", "Medel", "Låg"],
QUAL_T_HIGHEST = u"Högsta"
QUAL_T_HD = u"HD"
QUAL_T_HIGH = u"Hög"
QUAL_T_MED = u"Medel"
QUAL_T_LOW = u"Låg"


# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def Start():
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, "SVT Play", "icon-default.png", "art-default.jpg")
    HTTP.CacheTime = CACHE_TIME_SHORT
    #Locale.SetDefaultLocale(loc="se")
    #HTTP.PreCache(INDEX_URL % 1)
    #HTTP.PreCache(LATEST_SHOWS_URL % 1)
    #HTTP.PreCache(MOST_VIEWED_URL % 1)
    #HTTP.PreCache(RECOMMENDED_URL % 1)
    #HTTP.PreCache(LATEST_VIDEOS_URL % 1)
    #HTTP.PreCache(LATEST_NEWS_SHOWS_URL % 1)
    HTTP.PreCache(CATEGORIES_URL)
    MediaContainer.art = R(ART)
    
    Log("Quality Setting: %s" % Prefs['quality'])

# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def MainMenu():
    menu = MediaContainer(viewGroup="List")
    menu.Append(Function(DirectoryItem(ListRecommended, title=RECOMMENDED, thumb=R('main_rekommenderat.png'))))
    menu.Append(Function(DirectoryItem(ListMostViewed, title=MOST_VIEWED, thumb=R('main_mest_sedda.png'))))
    menu.Append(Function(DirectoryItem(ListCategories, title=CATEGORIES, thumb=R('main_kategori.png'))))
    menu.Append(Function(DirectoryItem(ListLatestShows, title=LATEST_SHOWS, thumb=R('main_senaste_program.png'))))
    menu.Append(Function(DirectoryItem(ListLatestNewsShows, title=LATEST_NEWS_SHOWS, thumb=R('category_nyheter.png'))))
    menu.Append(Function(DirectoryItem(ListLatestVideos, title=LATEST_VIDEOS, thumb=R('main_senaste_klipp.png'))))
    menu.Append(Function(DirectoryItem(ListLiveMenu, title=LIVE_SHOWS, thumb=R('main_live.png'))))
    menu.Append(Function(DirectoryItem(ListAllShows, title=INDEX_SHOWS, thumb=R('main_index.png'))))
    menu.Append(PrefsItem(u"Inställningar"))
    return menu

def ListCategories(sender):
    Log("ListCategories")
    pageElement = HTML.ElementFromURL(CATEGORIES_URL).xpath("//li/div[@class='container']/a")
    categories = []
    for element in pageElement:
        categoryName = element.xpath("span[@class='category-header']/text()")[0]
        categoryUrl = SITE_URL + element.get("href") 
        categoryIconName = "category_" + re.search(r'(\w+)$',categoryUrl).group(1) + ".png"
        Log("Name %s, URL %s" % (categoryName, categoryUrl))
        Log("Icon: %s " % categoryIconName)
        icon = element.xpath("img")[0]
        categories.append((categoryName, categoryUrl, categoryIconName))

    catList = MediaContainer()
    for category in categories:
        HTTP.PreCache(category[1])
        catList.Append(Function(DirectoryItem(ListCategory, title=category[0], thumb=R(category[2])), name=category[0], url=category[1]))

    return catList

def ListCategory(sender, name, url):
    Log("Name: %s Url: %s" % (name,url))
    showsList = MediaContainer()
    paginateUrl= FindPaginateUrl(url)
    paginateUrl = url + '/' + paginateUrl 

    if name == 'Barn':
        showsList.Extend(Paginate(paginateUrl % 1, paginateUrl, "pb", IndexShows))
    elif name == 'Film & drama':
        showsList.Extend(Paginate(paginateUrl % 1, paginateUrl, "pb", IndexShows))
    elif name == 'Kultur & nöje':
        showsList.Extend(Paginate(paginateUrl % 1, paginateUrl, "pb", IndexShows))
    elif name == 'Samhälle & fakta':
        showsList.Extend(Paginate(paginateUrl % 1, paginateUrl, "pb", IndexShows))
    elif name == 'Nyheter':
        showsList.Extend(IndexShows(url, "sb"))
        showsList.Extend(IndexShows(url, "se"))
    elif name == 'Sport':
        showsList.Append(Function(DirectoryItem(key=ListSportShows, title="Sportprogram", subtitle="Lista alla sportprogram"), paginateUrl=paginateUrl))
        showsList.Append(Function(DirectoryItem(key=ListSports, title="Se sporter", subtitle="Lista alla sporter"), url=url))

    return showsList

def ListSports(sender, url):
    Log("FindSports: %s" % url)
    pageElement = HTML.ElementFromURL(url)
    xpath = "//div[@id='bs']//li//a[starts-with(@href, '/t/')]"
    sports = pageElement.xpath(xpath)
    sportsList = MediaContainer()
    for sport in sports:
        sportUrl = SITE_URL + sport.get("href")
        sportName = sport.xpath("text()")[0]
        Log("Name: %s, URL: %s " % (sportName, sportUrl))
        sportsList.Append(Function(DirectoryItem(key=ListSport, title=sportName), sportUrl=sportUrl))

    return sportsList

def ListSport(sender, sportUrl):
    Log(sportUrl)
    pageElement = HTML.ElementFromURL(sportUrl)
    sections = pageElement.xpath("//div[@id='sb']//div[@class='navigation player-header']//a[starts-with(@href, '?')]")
    Log("%d, %s" % (len(sections), sections))
    sectionsList = MediaContainer()
    for section in sections:
        sectionUrl=sportUrl + section.get("href")
        sectionName=section.xpath("text()")[0]
        Log("%s, Url: %s" % (sectionName, sectionUrl))
        sectionsList.Append(Function(DirectoryItem(key=ListSportSection, title=sectionName), url=sectionUrl, sportUrl=sportUrl))

    return sectionsList

def ListSportSection(sender, url, sportUrl):
    Log(url)
    paginateUrl = sportUrl + FindPaginateUrl(url)
    showsList = MediaContainer()
    showsList.Extend(Paginate(paginateUrl % 1, paginateUrl, "sb", IndexShows))
    return showsList


def ListSportShows(sender, paginateUrl):
    showsList = MediaContainer()
    Log("ListSportShows")
    Log(paginateUrl)
    showsList.Extend(Paginate(paginateUrl % 1, paginateUrl, "sb", IndexShows))
    return showsList

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

def ListShowEpisodes(sender, showName, showUrl):
    Log("ListShowEpisodes: %s, %s" %  (showName, showUrl))
    epList = MediaContainer()
    episodes = BuildShowEpisodesMenu(showUrl, "sb")
    for ep in episodes:
        Log(ep)
        epList.Append(ep)
    Log("Added %s items" % len(epList))
    return epList


def ListLiveMenu(sender):
    showsList = MediaContainer()
    liveElements = HTML.ElementFromURL(LIVE_URL)
    for element in liveElements.xpath("//span[@class='thumbnail']//a[@class='tableau']"):
        liveName = strip_all(unicode(element.xpath("../../../../h3/text()")[0]))        
        Log("LiveName: %s" % liveName)
        liveUrl = SITE_URL +  element.get("href")
       
        # Get the actual stream url from subpage and do some munging for the plex player to get it
        liveContentUrl = GetEpisodeInfo(liveUrl)[2]
        liveContentUrl = re.sub(r'^(.*)/(.*)$','\\1&clip=\\2', liveContentUrl)
        liveContentUrl = PLEX_PLAYER_URL + liveContentUrl +"&live=true&width=640&height=360"
       
        Log("Live content url: " + liveContentUrl)
        liveIcon= element.xpath("descendant::img[starts-with(@class, 'thumbnail')]")[0].get("src")
        liveDesc = strip_all(unicode(element.xpath("../../span[@class='description']/text()")[0]))
        Log("Live icon % s" % liveIcon)
        Log("LiveDesc: %s" % liveDesc)
        showsList.Append(WebVideoItem(url=liveContentUrl, title=liveName, summary=liveDesc, duration="0", thumb=liveIcon))
        
    return showsList 

def Paginate(startUrl, requestUrl, divId, callFunc, maxPages = MAX_PAGINATE_PAGES):
    Log("Pagination in progress...")
    menuItems = []
    pageElement = HTML.ElementFromURL(startUrl)
    xpathBase = "//div[@id='%s']" % (divId)
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

def BuildShowEpisodesMenu(url, divId):
    #This section determines if we are on a page for a program (show)
    #If so it will extract all the shows episodes via paginating and then return the list
    Log("BuildShowEpisodesMenu")
    menuItems = []
    pageElement = HTML.ElementFromURL(url)
    xpathBase = "//div[@id='%s']" % (divId)
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

# Main method for sucking out svtplay content
def BuildGenericMenu(url, divId):
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
            v = VideoItem(key=contentUrl, title=clipName, summary=clipSummary, duration=clipLength,thumb=clipIcon)
            menuItems.append(v)
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
        menuItems.append(Function(DirectoryItem(key=HierarchyDown, title=subCategoryName, thumb=subCategoryImage), url=subCategoryUrl, baseUrl=url, divId = divId))

    return menuItems
    
def PlayVideo(sender, url):
    Log("Request to play video: %s" % url)
    return Redirect(WebVideoItem(url))


def HierarchyDown(sender, url, baseUrl, divId):
    Log("HD: %s" % url)
    menu = MediaContainer()
    paginateUrl = FindPaginateUrl(url)
    paginateUrl = baseUrl + paginateUrl
    menu.Extend(Paginate(paginateUrl % 1, paginateUrl, divId, BuildGenericMenu))

    return menu


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
    d = GetUrlQualitySelection(flashvars)
    Log("Url selection: %s" % d[Prefs['quality']])
    return re.search(r'(pathflv=|dynamicStreams=url:)(.*?)[,&$]',flashvars).group(2)    

def GetUrlQualitySelection(flashvars):
    links = re.findall("rtmpe.*?,", flashvars)
    d = dict()
    d[QUAL_T_HIGHEST] = links[0] 
    d[QUAL_T_HD] = links[0]
    if(len(links) > 0):
        d[QUAL_T_HIGH] = links[1]
    if(len(links) > 1):
        d[QUAL_T_MED] = links[2]
    if(len(links) > 2):
        d[QUAL_T_LOW] = links[3]

    Log(d)
    return d
    
# Replaces all running whitespace characters with a single space
def strip_all(str):
    return string.join(string.split(str), ' ')
    

        

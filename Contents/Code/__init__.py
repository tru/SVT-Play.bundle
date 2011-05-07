# -*- coding: utf-8 -*

import re
import string
from indexshows import *
from common import *

# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def Start():
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, TEXT_TITLE, "icon-default.png", "art-default.jpg")
    HTTP.CacheTime = CACHE_TIME_SHORT
    HTTP.PreCache(URL_INDEX)
    MediaContainer.art = R(ART)
    
    #Create thread to reindex shows in the background
    #Thread.Create(ReindexShows, MAX_PAGINATE_PAGES)
    Log("Quality Setting: %s" % Prefs[PREF_QUALITY])

# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def MainMenu():
    menu = MediaContainer(viewGroup="List", title1= TEXT_TITLE + " " + VERSION)
    menu.Append(Function(DirectoryItem(ListIndexShows, title=TEXT_INDEX_SHOWS, thumb=R('main_index.png'))))
    #menu.Append(Function(DirectoryItem(ListLiveMenu, title=LIVE_SHOWS, thumb=R('main_live.png'))))
    menu.Append(PrefsItem(u"Inställningar"))
    return menu

def ListIndexShows(sender):
    Log("ListIndexShows")
    showsList = MediaContainer(title1=TEXT_INDEX_SHOWS)
    xpathBase = "//div[@class='tab active']"
    pageElement = HTML.ElementFromURL(URL_INDEX)
    programLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href,'/t/')]")
    for programLink in programLinks:
        showUrl = URL_SITE + programLink.get("href")
        showName = programLink.xpath("text()")[0]
        Log("Program Link: %s" % showName)
        if(Data.Exists(showName)):
            si = Data.LoadObject(showName)
            Log("SHOW: %s " % si.name)
            Log("subtitle: %s" % si.info)
            Log("thumbnail: %s " % si.thumbnailUrl)
            showsList.Append(Function(DirectoryItem(key=ListShowEpisodes,title=showName, summary=si.info,
                thumb=si.thumbnailUrl), showName=showName, showUrl=showUrl))
        else:
            showsList.Append(Function(DirectoryItem(key=ListShowEpisodes,title=showName), showName=showName, showUrl=showUrl))
            
    return showsList
   
def ListShowEpisodes(sender, showName, showUrl):
    Log("ListShowEpisodes: %s, %s" %  (showName, showUrl))
    epList = MediaContainer()
    #episodes = BuildShowEpisodesMenu(showUrl, "sb")
    #for ep in episodes:
        #Log(ep)
        #epList.Append(ep)
    #Log("Added %s items" % len(epList))
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

    #sections = pageElement.xpath("//div[@id='sb']//div[@class='navigation player-header']//a[starts-with(@href, '?')]")
    #if(len(sections) > 0):
        #d = Function(DirectoryItem(BuildSectionsMenu, title="Sektioner", subtitle="Undersektioner:", summary="summary"), url=url)
        #Log("Appending sections with len: %d" % len(sections))
        #menuItems.append(d)

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
    programHtml = HTTP.Request(url=programUrl, cacheTime=CACHE_TIME_LONG)
    infoElements = HTML.ElementFromString(programHtml).xpath("//div[@id='description-title']")
    if (len(infoElements) > 0):
        return infoElements[0].text.strip()
    return NO_INFO
     
def GetEpisodeInfo(episodeUrl):
    Log(episodeUrl)
    episodeHtml = HTTP.Request(url=episodeUrl, cacheTime=CACHE_TIME_LONG)
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
    
    #If it's an rtmp stream, try to find the different qualities
    if(flashvars.find("rtmp") > -1):
        d = GetUrlQualitySelection(flashvars)
        try: 
            url = d[Prefs['quality']]
        except KeyError:
            url = d[QUAL_T_HIGHEST]
        Log("Url selection: %s" % url) 
        return url 
    else:
        Log("Flashvars not found! Using first found stream")
    
    return re.search(r'(pathflv=|dynamicStreams=url:)(.*?)[,&$]',flashvars).group(2)    

def GetUrlQualitySelection(flashvars):
    #You could make this more sophisticated by checking that the link you select also
    #match the correct bitrate and not just assume they are in descending order
    Log("flashvars: %s" % flashvars)
    links = re.findall("rtmp.*?,", flashvars)

    cleanLinks = [link.replace(',','') for link in links]
    links = cleanLinks
    d = dict()
    d[QUAL_T_HIGHEST] = links[0]
    d[QUAL_T_HD] = links[0]
    Log("Dict len: %d" % len(links))
    if(len(links) > 1):
        d[QUAL_T_HIGH] = links[1]
    if(len(links) > 2):
        d[QUAL_T_MED] = links[2]
    if(len(links) > 3):
        d[QUAL_T_LOW] = links[3]

    Log(d)
    return d
    
# Replaces all running whitespace characters with a single space
def strip_all(str):
    return string.join(string.split(str), ' ')
    

        

# -*- coding: utf-8 -*
# 
from PMS import Plugin, Log, XML, HTTP, JSON, Prefs
from PMS.MediaXML import MediaContainer, DirectoryItem, WebVideoItem, SearchDirectoryItem, VideoItem
from PMS.FileTypes import PLS
from PMS.Shorthand import _L, _E, _D
import lxml.html
import re
import datetime
import os
import string


# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION="1.2"

PLEX_PLAYER_URL = "http://www.plexapp.com/player/player.php?&url="
PLUGIN_PREFIX	= "/video/svt"
SITE_URL		= "http://svtplay.se"
LATEST_SHOWS_URL = "http://svtplay.se/?/pb,a1364143,1,f,-1"
MOST_VIEWED_URL = "http://svtplay.se/?/pb,a1364144,1,f,-1"
RECOMMENDED_URL = "http://svtplay.se/?/pb,a1364142,1,f,-1"
LATEST_VIDEOS_URL = "http://svtplay.se/?/cb,a1364145,1,f,-1"
LIVE_URL = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1596757,1,f,"
CATEGORIES_URL = SITE_URL + "/kategorier"
INDEX_URL		= SITE_URL + "/alfabetisk?am,,%d,thumbs"
NO_INFO = "Beskrivning saknas."

CACHE_TIME_LONG    = 60*60*24*30 # Thirty days
CACHE_TIME_SHORT   = 60*60*5    # 5 minutes

# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def Start():
    Plugin.AddRequestHandler(PLUGIN_PREFIX, HandleRequest, "SVT Play", "icon-default.png", "art-default.jpg")
    Plugin.AddViewGroup("InfoList", viewMode="InfoList", contentType="items")
    Plugin.AddViewGroup("List", viewMode="List", contentType="items")
    


# Handler function called on each request
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def HandleRequest(pathNouns, count):
  
    # Cache bug workaround
    Plugin.Dict["Now"] = datetime.datetime.now()
    
    # Initialize 
    # - - - - - - - - - - - - - - -
    menuItems = []
    viewGroup = "InfoList"
    Log.Add("\n\n\n- - - - - - - - - - - - - - - \nRequest %s %s" % (count,pathNouns))
    (key, url, title) = GetArgs(pathNouns)
    
    # Static menus (Hard-coded url)
    # - - - - - - - - - - - - - -
    if key == '': # No parameters, show main menu
        menuItems.extend(BuildMainMenu())
        viewGroup = "List"
    
    if key == "categories":
        menuItems.extend(BuildCategoriesMenu())
        viewGroup = "List"    
           
    if key =="latest_shows":
        menuItems.extend(BuildGenericMenu(LATEST_SHOWS_URL,"Senaste program","pb"))
   
    if key == "most_viewed":
        menuItems.extend(BuildGenericMenu(MOST_VIEWED_URL,"Mest sedda","pb"))
    
    if key == "latest_videos":
        menuItems.extend(BuildGenericMenu(LATEST_VIDEOS_URL,"Senaste klipp","cb"))
    
    if key == "recommended":
        menuItems.extend(BuildGenericMenu(RECOMMENDED_URL,"Rekommenderat","pb"))    
        
    if key == "index":
        for i in range(1,10):
            menuItems.extend(BuildGenericMenu(INDEX_URL % (i),title,"am"))
    
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
           menuItems.extend(BuildGenericMenu(url,title,divId,paginate=True))
           
    if key == "program":
        menuItems.extend(BuildGenericMenu(url,title,"sb"))
        
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
def BuildMainMenu():
    menuItems = []
    menuItems.append(DirectoryItem(BuildArgs("most_viewed", "","Mest sedsssda"), "Mest sedda", Plugin.ExposedResourcePath('main_mest_sedda.png')))
    menuItems.append(DirectoryItem(BuildArgs("categories", "", u'Kategorier'), u'Välj kategori', Plugin.ExposedResourcePath('main_kategori.png')))
    menuItems.append(DirectoryItem(BuildArgs("recommended", "", 'Rekommenderat'), 'Rekommenderat', Plugin.ExposedResourcePath('main_rekommenderat.png')))
    menuItems.append(DirectoryItem(BuildArgs("latest_shows", "", 'Senaste program'), "Senaste program", Plugin.ExposedResourcePath('main_senaste_program.png')))
    menuItems.append(DirectoryItem(BuildArgs("latest_videos", "", 'Senaste klipp' ), "Senaste klipp", Plugin.ExposedResourcePath('main_senaste_klipp.png')))
    menuItems.append(DirectoryItem(BuildArgs("index", "",u'Program A-Ö'), u'Program A-Ö', Plugin.ExposedResourcePath('main_index.png')))
    menuItems.append(DirectoryItem(BuildArgs("live", "",u'Livesändningar'), u'Livesändningar', Plugin.ExposedResourcePath('main_live.png')))
    return menuItems
    
def BuildCategoriesMenu():
    menuItems = []
    for element in XML.ElementFromURL(CATEGORIES_URL, True).xpath("//li/div[@class='container']/a"):
        categoryName = element.xpath("span[@class='category-header']/text()")[0]
        categoryUrl = SITE_URL + element.get("href")
        categoryIconName = "category_" + re.search(r'(\w+)$',categoryUrl).group(1) + ".png"
        Log.Add("Icon name: " + categoryIconName)
        #categoryIcon = element.xpath("img")[0].get("src")
        menuItems.append(DirectoryItem(BuildArgs("category",categoryUrl,categoryName), categoryName, Plugin.ExposedResourcePath(categoryIconName)))
    return menuItems
    
def BuildLiveMenu():
    menuItems = []
    liveElements = XML.ElementFromURL(LIVE_URL, True)
    for element in liveElements.xpath("//a[@class='tableau']"):
        liveName = strip_all(unicode(element.xpath("../../../h3/text()")[0]))        
        liveUrl = SITE_URL +  element.get("href")
       
        # Get the actual stream url from subpage and do some munging for the plex player to get it
        liveContentUrl = GetEpisodeInfo(liveUrl)[2]
        liveContentUrl = re.sub(r'^(.*)/(.*)$','\\1&clip=\\2', liveContentUrl)
        liveContentUrl = PLEX_PLAYER_URL + liveContentUrl +"&live=true&width=640&height=360"
       
        Log.Add("Live content url: " + liveContentUrl)
        liveIcon = element.xpath("span/span[starts-with(@class,'flashcontent')]/img")[0].get("src")      
        liveDesc = strip_all(unicode(element.xpath("span[@class='description']/text()")[0]))
        menuItems.append(WebVideoItem(liveContentUrl, liveName,liveDesc, "0",liveIcon))
        
    return menuItems
            
# Main method for sucking out svtplay content
def BuildGenericMenu(url, title, divId, paginate=False):
    menuItems = []
    pageElement = XML.ElementFromURL(url, True)
    Log.Add("url: %s divId: %s" % (url, divId))
    xpathBase = "//div[@id='%s']" % (divId)
    Log.Add("xpath expr: " + xpathBase)
    
    clipLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href,'/v/')]")
    for clipLink in clipLinks:
        clipName = clipLink.xpath("span/text()")[0].strip()
        Log.Add("Clip : %s" % (clipName.encode('utf8')))
        clipUrl = SITE_URL + clipLink.get("href")
        Log.Add("URL: " + clipUrl)
        clipIcon = clipLink.xpath("img")[0].get("src").replace("_thumb","_start")
        Log.Add("Clip icon: >" + clipIcon + "<")
        (clipSummary, clipLength, contentUrl) = GetEpisodeInfo(clipUrl) 
        if (contentUrl.endswith('.flv')):
            menuItems.append(VideoItem(contentUrl, clipName, clipSummary, clipLength,clipIcon))
        else:
            # should be rtmp url
            if (contentUrl.endswith('.mp4')):
               #special case rmpte stream with mp4 ending.
               contentUrl = PLEX_PLAYER_URL + contentUrl.replace("_definst_/","_definst_&clip=mp4:")
            else:
               contentUrl = PLEX_PLAYER_URL + contentUrl.replace("_definst_/","_definst_&clip=")
            menuItems.append(WebVideoItem(contentUrl, clipName, clipSummary, clipLength,clipIcon))
        
    # Note: must have "span" element, otherwise some wierd stuff can come along...
    programLinks = pageElement.xpath(xpathBase + "//a[starts-with(@href, '/t/')]/span/..")
    for programLink in programLinks:
        programName = programLink.xpath("span/text()")[0].strip()
        Log.Add("Program : %s" % (programName.encode('utf8')))
        programUrl = SITE_URL + programLink.get("href")
        programIcon = programLink.xpath("img")[0].get("src") #GetHiResIconFromSubPage(programUrl)
        programSummary = GetProgramInfo(programUrl)
        menuItems.append(DirectoryItem(BuildArgs("program",programUrl,programName), programName, programIcon, programSummary))
    
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
            Log.Add("Paginating using url: %s" % (pageUrl))
            menuItems.extend(BuildGenericMenu(pageUrl, title, divId, paginate=False))
        
    return menuItems
    


# Helpers
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Returns the key, url and title from the "pathNouns" structure
def GetArgs(pathNouns):   
    # Empty args, should only happen in main menu
    if len(pathNouns) == 0:
        return ('','','')
    
    # We only care about the last pathNoun (index -1), it should have the format "key||encodedUrl||title".
    (key, url, title) = pathNouns[-1].split('||')
    return (key, _D(url), title)

    
# Builds a "pathNoun" structure
def BuildArgs(key, url='', title=''):
    return "%s||%s||%s" % (key, _E(url), title)
    
def GetProgramInfo(programUrl):
    programHtml = HTTP.GetCached(programUrl, CACHE_TIME_LONG)
    infoElements = XML.ElementFromString(programHtml, True).xpath("//div[@id='description-title']")
    if (len(infoElements) > 0):
        return infoElements[0].text.strip()
    return NO_INFO
     
def GetEpisodeInfo(episodeUrl):
    episodeHtml = HTTP.GetCached(episodeUrl, CACHE_TIME_LONG)
    episodeElements = XML.ElementFromString(episodeHtml, True)
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
        
        Log.Add("Episode length: %s %s %s" % (hours, minutes, seconds))
        episodeLengthMillis = "%d" % (1000 * (hours*60*60 + minutes*60 + seconds))
    
    # Get the url for the stream
    contentUrl = GetContentUrl(episodeElements)
    Log.Add("Content url:" + contentUrl)
    return (episodeInfo, episodeLengthMillis, contentUrl)
    
def GetContentUrl(pageElement):
    flashvars = pageElement.xpath("//object[@id='playerSwf']/param[@name='flashvars']")[0].get("value")
    # return the pathflv OR the first dynamicStream URL. Never mind choosing what bitrate
    return re.search(r'(pathflv=|dynamicStreams=url:)(.*?)[,&$]',flashvars).group(2)    

# Replaces all running whitespace characters with a single space
def strip_all(str):
    return string.join(string.split(str), ' ')
    

        

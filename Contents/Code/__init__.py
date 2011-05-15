# -*- coding: utf-8 -*

import re
import string
import cerealizer
from show import *
from common import *
from episode import *
from category import *

# Initializer called by the framework
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
def Start():
    Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, TEXT_TITLE, "icon-default.png", "art-default.jpg")
    Plugin.AddViewGroup(name="List")
    HTTP.CacheTime = CACHE_TIME_SHORT
    HTTP.PreCache(URL_INDEX)
    MediaContainer.art = R(ART)

    cerealizer.register(ShowInfo)
    cerealizer.register(EpisodeInfo)
    cerealizer.register(CategoryInfo)

    Thread.Create(ReindexShows)
    Log("Quality Setting: %s" % Prefs[PREF_QUALITY])

# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def MainMenu():
    menu = MediaContainer(viewGroup="List", title1= TEXT_TITLE + " " + VERSION)
    menu.Append(Function(DirectoryItem(GetIndexShows, title=TEXT_INDEX_SHOWS, thumb=R('main_index.png'))))
    menu.Append(Function(DirectoryItem(GetRecommendedShows, title=TEXT_RECOMMENDED_SHOWS,
        thumb=R('main_rekommenderat.png'))))
    menu.Append(Function(DirectoryItem(GetLatestClips, title=TEXT_LATEST_CLIPS, thumb=R('main_senaste_klipp.png'))))
    menu.Append(Function(DirectoryItem(GetLatestShows, title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png'))))
    menu.Append(Function(DirectoryItem(GetMostViewed, title=TEXT_MOST_VIEWED, thumb=R('main_mest_sedda.png'))))
    menu.Append(Function(DirectoryItem(GetCategories, title=TEXT_CATEGORIES, thumb=R('main_kategori.png'))))
    #menu.Append(Function(DirectoryItem(ListLiveMenu2, title=TEXT_LIVE_SHOWS, thumb=R('main_live.png'))))
    menu.Append(PrefsItem(title=TEXT_PREFERENCES, thumb=R('icon-prefs.png')))
    return menu


def GetCategories(sender):
    Log("GetCategories")
    catMenu = MediaContainer(viewGroup="List", title1 = sender.title1, title2=TEXT_CATEGORIES)
    catMenu.Append(Function(DirectoryItem(key=GetCategoryShows, title=TEXT_CAT_CHILD, thumb=R("category_barn.png")),
        catUrl=URL_CAT_CHILD, catName=TEXT_CAT_CHILD))
    catMenu.Append(Function(DirectoryItem(key=GetCategoryShows, title=TEXT_CAT_MOVIE_DRAMA, thumb=R("category_film_och_drama.png")),
        catUrl=URL_CAT_MOVIE_DRAMA, catName=TEXT_CAT_MOVIE_DRAMA))
    catMenu.Append(Function(DirectoryItem(key=GetCategoryShows, title=TEXT_CAT_FACT,
        thumb=R("category_samhalle_och_fakta.png")),
        catUrl=URL_CAT_FACT, catName=TEXT_CAT_FACT))
    catMenu.Append(Function(DirectoryItem(key=GetCategoryNewsShows, title=TEXT_CAT_NEWS,
        thumb=R("category_nyheter.png")),
        catUrl=URL_CAT_NEWS, catName=TEXT_CAT_NEWS))
    catMenu.Append(Function(DirectoryItem(key=GetCategoryNewsShows, title=TEXT_CAT_SPORT,
        thumb=R("category_sport.png")),
        catUrl=URL_CAT_SPORT, catName=TEXT_CAT_SPORT))

    return catMenu

def GetMostViewed(sender):
    Log("GetMostViewed")
    showsList = MediaContainer(title1 = sender.title1, title2 = TEXT_MOST_VIEWED)
    pages = GetPaginatePages(url=URL_MOST_VIEWED, divId='pb', maxPaginateDepth = 5)
    linksList = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        links = pageElement.xpath("//div[@id='pb']//div[@class='content']//a")
        linksList = linksList + links

    showsList.Extend(CreateShowList(linksList, True))
 
    return showsList

def GetLatestShows(sender):
    Log("GetLatestShows")
    showsList = MediaContainer(title1 = sender.title1, title2 = TEXT_LATEST_SHOWS)
    pages = GetPaginatePages(url=URL_LATEST_SHOWS, divId='pb', maxPaginateDepth = 5)
    linksList = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        links = pageElement.xpath("//div[@id='pb']//div[@class='content']//a")
        linksList = linksList + links

    showsList.Extend(CreateShowList(linksList, True))
    return showsList
   
def GetLatestClips(sender):
    Log("GetLatestClips")
    clipsList = MediaContainer(title1 = sender.title1, title2 = TEXT_LATEST_CLIPS)
    clipsPages = GetPaginatePages(url=URL_LATEST_CLIPS, divId='cb', maxPaginateDepth = 5)
    clipLinks = []
    for page in clipsPages:
        pageElement = HTML.ElementFromURL(page)
        links = pageElement.xpath("//div[@id='cb']//div[@class='content']//a/@href")
        for link in links:
            clipLink = URL_SITE + link
            clipLinks.append(clipLink)
            Log("clipLink: %s" % clipLink)

    for clipLink in clipLinks:
        epInfo = GetEpisodeInfo(clipLink)        
        clipsList.Append(epInfo.GetMediaItem())

    return clipsList


def ValidatePrefs():
    Log("Validate prefs")
    global MAX_PAGINATE_PAGES
    try:
         MAX_PAGINATE_PAGES = int(Prefs[PREF_PAGINATE_DEPTH])
    except ValueError:
        pass

    Log("max paginate %d" % MAX_PAGINATE_PAGES)

def ListLiveMenu2(sender):
    liveList = MediaContainer()
    pageElement = HTML.ElementFromURL(URL_LIVE)
    activeLinks = pageElement.xpath("//span[@class='description']/a/@href")
    for link in activeLinks:
        newLink = URL_SITE + link
        Log("Link: %s " % newLink)
        epInfo = GetEpisodeInfo(newLink)
        liveList.Append(epInfo.GetMediaItem())

    return liveList

def ListLiveMenu(sender):
    showsList = MediaContainer()
    liveElements = HTML.ElementFromURL(URL_LIVE)
    for element in liveElements.xpath("//span[@class='thumbnail']//a[@class='tableau']"):
        liveName = strip_all(unicode(element.xpath("../../../../h3/text()")[0]))        
        Log("LiveName: %s" % liveName)
        liveUrl = URL_SITE +  element.get("href")
       
        # Get the actual stream url from subpage and do some munging for the plex player to get it
        epInfo = GetEpisodeInfo(liveUrl)
        liveContentUrl = GetContentUrlFromUserQualSettings(epInfo)
        liveContentUrl = re.sub(r'^(.*)/(.*)$','\\1&clip=\\2', liveContentUrl)
        liveContentUrl = URL_PLEX_PLAYER + liveContentUrl +"&live=true&width=640&height=360"
       
        Log("Live content url: " + liveContentUrl)
        liveIcon= element.xpath("descendant::img[starts-with(@class, 'thumbnail')]")[0].get("src")
        liveDesc = strip_all(unicode(element.xpath("../../span[@class='description']/text()")[0]))
        Log("Live icon % s" % liveIcon)
        Log("LiveDesc: %s" % liveDesc)
        showsList.Append(WebVideoItem(url=liveContentUrl, title=liveName, summary=liveDesc, duration="0", thumb=liveIcon))
        
    return showsList 


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

    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(THUMB)

    cerealizer.register(ShowInfo)
    cerealizer.register(EpisodeInfo)
    cerealizer.register(CategoryInfo)

#    Thread.Create(ReindexShows)

# Menu builder methods
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def MainMenu():
    menu = ObjectContainer(view_group="List", title1= TEXT_TITLE + " " + VERSION)
    menu.add(DirectoryObject(key=Callback(GetIndexShows), title=TEXT_INDEX_SHOWS, thumb=R('main_index.png')))
    menu.add(DirectoryObject(key=Callback(GetRecommendedShows), title=TEXT_RECOMMENDED_SHOWS,
        thumb=R('main_rekommenderat.png')))
    #menu.add(WebVideoItem(url="http://svtplay.se/t/102782/mitt_i_naturen", title="PauseTest"))
    menu.add(DirectoryObject(key=Callback(GetLatestNews), title=TEXT_LATEST_NEWS, thumb=R('main_senaste_nyhetsprogram.png')))
    menu.add(DirectoryObject(key=Callback(GetLatestClips), title=TEXT_LATEST_CLIPS, thumb=R('main_senaste_klipp.png')))
    menu.add(DirectoryObject(key=Callback(GetLatestShows), title=TEXT_LATEST_SHOWS, thumb=R('main_senaste_program.png')))
    menu.add(DirectoryObject(key=Callback(GetMostViewed), title=TEXT_MOST_VIEWED, thumb=R('main_mest_sedda.png')))
    menu.add(DirectoryObject(key=Callback(GetCategories), title=TEXT_CATEGORIES, thumb=R('main_kategori.png')))
    menu.add(DirectoryObject(key=Callback(ListLiveMenu), title=TEXT_LIVE_SHOWS, thumb=R('main_live.png')))
#    menu.add(PrefsItem(title=TEXT_PREFERENCES, thumb=R('icon-prefs.png')))
    return menu


def GetCategories():
    Log("GetCategories")
    catMenu = ObjectContainer(view_group="List", title2=TEXT_CATEGORIES)
    catMenu.add(DirectoryObject(key=Callback(GetCategoryShows, catUrl=URL_CAT_CHILD, catName=TEXT_CAT_CHILD),
                                   title=TEXT_CAT_CHILD, thumb=R("category_barn.png")))
    catMenu.add(DirectoryObject(key=Callback(GetCategoryShows,catUrl=URL_CAT_MOVIE_DRAMA, catName=TEXT_CAT_MOVIE_DRAMA),
                                   title=TEXT_CAT_MOVIE_DRAMA, thumb=R("category_film_och_drama.png")))
    catMenu.add(DirectoryObject(key=Callback(GetCategoryShows, catUrl=URL_CAT_FACT, catName=TEXT_CAT_FACT),
                                   title=TEXT_CAT_FACT, thumb=R("category_samhalle_och_fakta.png")))
    catMenu.add(DirectoryObject(key=Callback(GetCategoryNewsShows, catUrl=URL_CAT_NEWS, catName=TEXT_CAT_NEWS), 
                                   title=TEXT_CAT_NEWS, thumb=R("category_nyheter.png")))
    catMenu.add(DirectoryObject(key=Callback(GetCategoryNewsShows, catUrl=URL_CAT_SPORT, catName=TEXT_CAT_SPORT),
                                   title=TEXT_CAT_SPORT, thumb=R("category_sport.png")))

    return catMenu

def GetLatestNews():
    Log("GetLatestNews")
    newsList = ObjectContainer(title2 = TEXT_LATEST_NEWS)
    pages = GetPaginatePages(url=URL_LATEST_NEWS, divId='pb')
    linksList = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        links = pageElement.xpath("//div[@id='pb']//div[@class='content']//a/@href")
        for link in links:
            newsLink = URL_SITE + link
            linksList.append(newsLink)

    for link in linksList:
        epInfo = GetEpisodeInfo(link)        
        newsList.add(epInfo.GetMediaItem())

    return newsList

def GetMostViewed():
    Log("GetMostViewed")
    showsList = ObjectContainer(title2 = TEXT_MOST_VIEWED)
    pages = GetPaginatePages(url=URL_MOST_VIEWED, divId='pb', maxPaginateDepth = MAX_PAGINATE_PAGES)
    linksList = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        links = pageElement.xpath("//div[@id='pb']//div[@class='content']//a")
        linksList = linksList + links

    showsList += CreateShowList(linksList, True)
 
    return showsList

def GetLatestShows():
    Log("GetLatestShows")
    showsList = ObjectContainer(title2 = TEXT_LATEST_SHOWS)
    pages = GetPaginatePages(url=URL_LATEST_SHOWS, divId='pb', maxPaginateDepth = MAX_PAGINATE_PAGES)
    linksList = []
    for page in pages:
        pageElement = HTML.ElementFromURL(page)
        links = pageElement.xpath("//div[@id='pb']//div[@class='content']//a")
        linksList = linksList + links

    showsList += CreateShowList(linksList, True)
    return showsList
   
def GetLatestClips():
    Log("GetLatestClips")
    clipsList = ObjectContainer(title2 = TEXT_LATEST_CLIPS)
    clipsPages = GetPaginatePages(url=URL_LATEST_CLIPS, divId='cb', maxPaginateDepth = MAX_PAGINATE_PAGES)
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
        clipsList.add(epInfo.GetMediaItem())

    return clipsList


def ValidatePrefs():
    Log("Validate prefs")
    global MAX_PAGINATE_PAGES
    try:
         MAX_PAGINATE_PAGES = int(Prefs[PREF_PAGINATE_DEPTH])
    except ValueError:
        pass

    Log("max paginate %d" % MAX_PAGINATE_PAGES)

def ListLiveMenu():
    liveList = ObjectContainer()
    pageElement = HTML.ElementFromURL(URL_LIVE, cacheTime = 0)
    activeLinks = pageElement.xpath("//span[@class='description']/a/@href")
    for link in activeLinks:
        newLink = URL_SITE + link
        Log("Link: %s " % newLink)
        epInfo = GetEpisodeInfo(newLink, True)
        liveList.add(epInfo.GetMediaItem())

    return liveList


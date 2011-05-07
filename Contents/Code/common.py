# -*- coding: utf-8 -*

# Global constants
# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
VERSION="3.1"
PLUGIN_PREFIX	= "/video/svt"

PLEX_PLAYER_URL = "http://www.plexapp.com/player/player.php?&url="
PLEX_CLIP_PLAYER_URL = "http://www.plexapp.com/player/player.php?clip="
SITE_URL		= "http://svtplay.se"
LIVE_URL = "http://svtplay.se/?cb,a1364145,1,f,-1/pb,a1596757,1,f,"
INDEX_URL = SITE_URL + "/alfabetisk"
INDEX_URL_THUMB = INDEX_URL + "?am,,%d,thumbs"

#URLs
URL_SITE = "http://svtplay.se"
URL_INDEX = URL_SITE + "/alfabetisk"
URL_INDEX_THUMB = URL_INDEX + "?am,,%d,thumbs"
 

#Texts
TEXT_LIVE_SHOWS = u'Livesändningar'
TEXT_INDEX_SHOWS = u'Program A-Ö'
TEXT_TITLE = "SVT Play"

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

class ShowInfo:
    def __init__(self):
        self.thumbnailUrl = None
        self.name = None
        self.info = None
        self.showUrl = None

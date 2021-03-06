# -*- coding: utf-8 -*-
import re
import os
import sys
import time
import urllib
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import CommonFunctions as common
import resources.lib.helper as helper
import resources.lib.svt as svt

MODE_CHANNELS = "kanaler"
MODE_A_TO_O = "a-o"
MODE_PROGRAM = "pr"
MODE_CLIPS = "clips"
MODE_LIVE_PROGRAMS = "live"
MODE_LATEST = "latest"
MODE_LATEST_NEWS = 'news'
MODE_POPULAR = "popular"
MODE_LAST_CHANCE = "last_chance"
MODE_VIDEO = "video"
MODE_CATEGORIES = "categories"
MODE_CATEGORY = "ti"
MODE_LETTER = "letter"
MODE_SEARCH = "search"
MODE_VIEW_TITLES = "view_titles"
MODE_VIEW_EPISODES = "view_episodes"
MODE_VIEW_CLIPS = "view_clips"

S_DEBUG = "debug"
S_HIDE_SIGN_LANGUAGE = "hidesignlanguage"
S_SHOW_SUBTITLES = "showsubtitles"
S_USE_ALPHA_CATEGORIES = "alpha"

PLUGIN_HANDLE = int(sys.argv[1])

addon = xbmcaddon.Addon("plugin.video.svtplay")
localize = addon.getLocalizedString
xbmcplugin.setContent(PLUGIN_HANDLE, "tvshows")

DEFAULT_FANART = os.path.join(
  xbmc.translatePath(addon.getAddonInfo("path")+"/resources/images/").decode("utf-8"),
  "background.png")

common.plugin = addon.getAddonInfo('name') + ' ' + addon.getAddonInfo('version')
common.dbg = helper.getSetting(S_DEBUG)


def viewStart():

  addDirectoryItem(localize(30009), {"mode": MODE_POPULAR})
  addDirectoryItem(localize(30003), {"mode": MODE_LATEST})
  addDirectoryItem(localize(30004), {"mode": MODE_LATEST_NEWS})
  addDirectoryItem(localize(30010), {"mode": MODE_LAST_CHANCE})
  addDirectoryItem(localize(30002), {"mode": MODE_LIVE_PROGRAMS})
  addDirectoryItem(localize(30008), {"mode": MODE_CHANNELS})
  addDirectoryItem(localize(30000), {"mode": MODE_A_TO_O})
  addDirectoryItem(localize(30001), {"mode": MODE_CATEGORIES})
  addDirectoryItem(localize(30006), {"mode": MODE_SEARCH})

def viewAtoO():
  programs = svt.getAtoO()

  for program in programs:
    folder = True
    mode = MODE_PROGRAM
    if program["type"] == "video":
      mode = MODE_VIDEO
      folder = False
    addDirectoryItem(program["title"],
                {"mode": mode, "url": program["url"]},
                thumbnail=program["thumbnail"], folder=folder)

def viewCategories():
  categories = svt.getCategories()

  for category in categories:
    addDirectoryItem(category["title"],
                {"mode": MODE_CATEGORY, "url": category["genre"]})

def viewAlphaDirectories():
  alphas = svt.getAlphas()
  if not alphas:
    return
  for alpha in alphas:
    addDirectoryItem(alpha, {"mode": MODE_LETTER, "letter": alpha})

def viewProgramsByLetter(letter):
  programs = svt.getProgramsByLetter(letter)

  for program in programs:
    addDirectoryItem(program["title"], {"mode": MODE_PROGRAM, "url": program["url"]}, thumbnail=program["thumbnail"])

def viewSection(section, page):
  (items, more_items) = svt.getItems(section, page)
  if not items:
    return
  for item in items:
    mode = MODE_VIDEO
    if item["type"] == "program":
      mode = MODE_PROGRAM
    createDirItem(item, mode)
  if more_items:
    addNextPageItem(page+1, section)

def viewChannels():
  channels = svt.getChannels()
  if not channels:
    return
  for channel in channels:
    createDirItem(channel, MODE_VIDEO)

def viewLatestNews():
    items = svt.getLatestNews()
    if not items:
      return
    for item in items:
      createDirItem(item, MODE_VIDEO)

def viewCategory(genre):
  programs = svt.getProgramsForGenre(genre)
  if not programs:
    return
  for program in programs:
    mode = MODE_PROGRAM
    if program["type"] == "video":
      mode = MODE_VIDEO
    createDirItem(program, mode)

def viewEpisodes(url):
  """
  Displays the episodes for a program with URL 'url'.
  """
  episodes = svt.getEpisodes(url)
  if episodes is None:
    helper.errorMsg("No episodes found!")
    return

  for episode in episodes:
    createDirItem(episode, MODE_VIDEO)

def addClipDirItem(url):
  """
  Adds the "Clips" directory item to a program listing.
  """
  params = {}
  params["mode"] = MODE_CLIPS
  params["url"] = url
  addDirectoryItem(localize(30108), params)

def viewClips(url):
  """
  Displays the latest clips for a program
  """
  clips = svt.getClips(url)
  if not clips:
    helper.errorMsg("No clips found!")
    return

  for clip in clips:
    createDirItem(clip, MODE_VIDEO)

def viewSearch():
  keyword = common.getUserInput(localize(30102))
  if keyword == "" or not keyword:
    viewStart()
    return
  keyword = urllib.quote(keyword)
  helper.infoMsg("Search string: " + keyword)

  keyword = re.sub(r" ", "+", keyword)

  results = svt.getSearchResults(keyword)
  for result in results:
    mode = MODE_VIDEO
    if result["type"] == "program":
      mode = MODE_PROGRAM
    createDirItem(result["item"], mode)

def createDirItem(article, mode):
  """
  Given an article and a mode; create directory item
  for the article.
  """
  if not helper.getSetting(S_HIDE_SIGN_LANGUAGE) or (not article["title"].lower().endswith("teckentolkad") and article["title"].lower().find("teckenspråk".decode("utf-8")) == -1):

    params = {}
    params["mode"] = mode
    params["url"] = article["url"]
    folder = False

    if mode == MODE_PROGRAM:
      folder = True
    info = None
    if "info" in article.keys():
      info = article["info"]
    addDirectoryItem(article["title"], params, article["thumbnail"], folder, False, info)

def addNextPageItem(next_page, section):
  addDirectoryItem("Next page",
                   {"page": next_page,
                    "mode": section})

def startVideo(url):
  if "m3u8" not in url:
    video_json = svt.getVideoJSON(url)
    if video_json is None:
      common.log("ERROR: Could not get video JSON")
      return
    try:
      show_obj = helper.resolveShowJSON(video_json)
    except ValueError:
      common.log("Could not decode JSON for "+url)
      return
  else:
    show_obj = {"videoUrl": url, "subtitleUrl": ""}
  if show_obj["videoUrl"]:
    playVideo(show_obj)
  else:
    dialog = xbmcgui.Dialog()
    dialog.ok("SVT Play", localize(30100))

def playVideo(show_obj):
  player = xbmc.Player()
  start_time = time.time()

  xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, xbmcgui.ListItem(path=show_obj["videoUrl"]))

  if show_obj["subtitleUrl"]:
    while not player.isPlaying() and time.time() - start_time < 10:
      time.sleep(1.)

    player.setSubtitles(show_obj["subtitleUrl"])

    if not helper.getSetting(S_SHOW_SUBTITLES):
      player.showSubtitles(False)


def addDirectoryItem(title, params, thumbnail=None, folder=True, live=False, info=None):

  list_item = xbmcgui.ListItem(title)

  if thumbnail:
    list_item.setThumbnailImage(thumbnail)

  if live:
    list_item.setProperty("IsLive", "true")

  if not folder:
    if params["mode"] == MODE_VIDEO:
      list_item.setProperty("IsPlayable", "true")
      if not thumbnail:
        thumbnail = ""

  fanart = DEFAULT_FANART
  if info:
    list_item.setInfo("Video", info)
    if "fanart" in info:
      fanart = info["fanart"]

  list_item.setArt({"fanart": fanart})
  xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, sys.argv[0] + '?' + urllib.urlencode(params), list_item, folder)

# Main segment of script
ARG_PARAMS = helper.getUrlParameters(sys.argv[2])
common.log("params: " + str(ARG_PARAMS))
ARG_MODE = ARG_PARAMS.get("mode")
ARG_URL = urllib.unquote_plus(ARG_PARAMS.get("url", ""))
ARG_PAGE = ARG_PARAMS.get("page")
if not ARG_PAGE:
  ARG_PAGE = "1"

if not ARG_MODE:
  viewStart()
elif ARG_MODE == MODE_A_TO_O:
  if helper.getSetting(S_USE_ALPHA_CATEGORIES):
    viewAlphaDirectories()
  else:
    viewAtoO()
elif ARG_MODE == MODE_CATEGORIES:
  viewCategories()
elif ARG_MODE == MODE_CATEGORY:
  viewCategory(ARG_URL)
elif ARG_MODE == MODE_PROGRAM:
  viewEpisodes(ARG_URL)
  addClipDirItem(ARG_URL)
elif ARG_MODE == MODE_CLIPS:
  viewClips(ARG_URL)
elif ARG_MODE == MODE_VIDEO:
  startVideo(ARG_URL)
elif ARG_MODE == MODE_POPULAR or \
     ARG_MODE == MODE_LATEST or \
     ARG_MODE == MODE_LAST_CHANCE or \
     ARG_MODE == MODE_LIVE_PROGRAMS:
  viewSection(ARG_MODE, int(ARG_PAGE))
elif ARG_MODE == MODE_LATEST_NEWS:
  viewLatestNews()
elif ARG_MODE == MODE_CHANNELS:
  viewChannels()
elif ARG_MODE == MODE_LETTER:
  viewProgramsByLetter(ARG_PARAMS.get("letter"))
elif ARG_MODE == MODE_SEARCH:
  viewSearch()

xbmcplugin.endOfDirectory(PLUGIN_HANDLE)

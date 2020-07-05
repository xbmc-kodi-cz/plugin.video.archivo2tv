# -*- coding: utf-8 -*-

import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc

from urllib import quote
from datetime import datetime 
import time

from o2tv.o2api import call_o2_api
from o2tv import o2api
from o2tv.utils import get_url, get_color
from o2tv import utils

_url = sys.argv[0]
_handle = int(sys.argv[1])

addon = xbmcaddon.Addon(id='plugin.video.archivo2tv')
addon_userdata_dir = xbmc.translatePath( addon.getAddonInfo('profile') ) 


def list_search(label):
    xbmcplugin.setPluginCategory(_handle, label)
    list_item = xbmcgui.ListItem(label="Nové hledání")
    url = get_url(action='program_search', query = "-----", label = label + " / " + "Nové hledání")  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    history = load_search_history()
    for item in history:
      list_item = xbmcgui.ListItem(label=item)
      url = get_url(action='program_search', query = item, label = label + " / " + item.encode("utf-8"))  
      xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle,cacheToDisc = False)

def program_search(query, label):
    xbmcplugin.setPluginCategory(_handle, label)
    if query == "-----":
      input = xbmc.Keyboard("", "Hledat")
      input.doModal()
      if not input.isConfirmed(): 
        return
      query = input.getText()
      if len(query) == 0:
        xbmcgui.Dialog().notification("Sledování O2TV","Je potřeba zadat vyhledávaný řetězec", xbmcgui.NOTIFICATION_ERROR, 4000)
        return   
      else:
        save_search_history(query)
        
    max_ts = int(time.mktime(datetime.now().timetuple()))
    data = call_o2_api(url = "https://www.o2tv.cz/unity/api/v1/search/tv/depr/?groupLimit=1&maxEnd=" + str(max_ts*1000) + "&q=" + quote(query), data = None, header = o2api.header_unity)
    if "err" in data:
      xbmcgui.Dialog().notification("Sledování O2TV","Problém při hledání", xbmcgui.NOTIFICATION_ERROR, 4000)
      sys.exit()  
    
    if "groupedSearch" in data and "groups" in data["groupedSearch"] and len(data["groupedSearch"]["groups"]) > 0:
      for item in data["groupedSearch"]["groups"]:
        programs = item["programs"][0]
        startts = programs["start"]
        start = datetime.fromtimestamp(programs["start"]/1000)
        endts = programs["end"]
        end = datetime.fromtimestamp(programs["end"]/1000)
        epgId = programs["epgId"]
        
        if addon.getSetting("details") == "true":
          img, plot, ratings, cast, directors = o2api.get_epg_details(str(epgId))
        list_item = xbmcgui.ListItem(label = programs["name"] + " (" + programs["channelKey"] + " | " + utils.day_translation_short[start.strftime("%A")].decode("utf-8") + " " + start.strftime("%d.%m %H:%M") + " - " + end.strftime("%H:%M") + ")")
        list_item.setProperty("IsPlayable", "true")
        if addon.getSetting("details") == "true":  
          list_item.setArt({'thumb': "https://www.o2tv.cz/" + img, 'icon': "https://www.o2tv.cz/" + img})
          list_item.setInfo("video", {"mediatype":"movie", "title":programs["name"], "plot":plot})
          if len(directors) > 0:
            list_item.setInfo("video", {"director" : directors})
          if len(cast) > 0:
            list_item.setInfo("video", {"cast" : cast})
          for rating_name,rating in ratings.items():
            list_item.setRating(rating_name, int(rating)/10)
        else:
          list_item.setInfo("video", {"mediatype":"movie", "title":programs["name"]})
        list_item.setContentLookup(False)          
        url = get_url(action='play_archiv', channelKey = programs["channelKey"].encode("utf-8"), start = startts, end = endts, epgId = epgId)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
      xbmcplugin.endOfDirectory(_handle)
    else:
      xbmcgui.Dialog().notification("Sledování O2TV","Nic nenalezeno", xbmcgui.NOTIFICATION_INFO, 3000)

def save_search_history(query):
    max_history = int(addon.getSetting("search_history"))
    cnt = 0
    history = []
    filename = addon_userdata_dir + "search_history.txt"
    
    try:
      with open(filename, "r") as file:
        for line in file:
          item = line[:-1]
          history.append(item)
    except IOError:
      history = []
      
    history.insert(0,query)

    with open(filename, "w") as file:
      for item  in history:
        cnt = cnt + 1
        if cnt <= max_history:
            file.write('%s\n' % item)

def load_search_history():
    history = []
    filename = addon_userdata_dir + "search_history.txt"
    try:
      with open(filename, "r") as file:
        for line in file:
          item = line[:-1]
          history.append(item)
    except IOError:
      history = []
    return history

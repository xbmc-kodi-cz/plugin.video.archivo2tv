# -*- coding: utf-8 -*-
import sys
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc

try:
    from urllib import quote, urlencode
except ImportError:
    from urllib.parse import quote, urlencode

from datetime import datetime

from o2tv.o2api import call_o2_api, get_header, get_header_unity
from o2tv.session import Session
from o2tv.utils import plugin_id, get_url, encode

_url = sys.argv[0]
_handle = int(sys.argv[1])

def list_settings(label):
    xbmcplugin.setPluginCategory(_handle, label)

    list_item = xbmcgui.ListItem(label='Kanály')
    url = get_url(action='list_channels_list', label = 'Kanály')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label='Služby')
    url = get_url(action='list_services', label = 'Služby')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label='Zařízení')
    url = get_url(action='list_devices', label = 'Zařízení')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    list_item = xbmcgui.ListItem(label='Nastavení doplňku')
    url = get_url(action='addon_settings', label = 'Nastavení doplňku')  
    xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    xbmcplugin.endOfDirectory(_handle)

def list_services(label):
    xbmcplugin.setPluginCategory(_handle, label)   
    session = Session()
    first = 1
    for serviceid in session.get_services(filtered = 0):
        offers = ''
        menuitems = []
        for offer in session.services[serviceid]['offers']:
            offers = offers + offer + ' '
        offers = '(' + offers + ')'        
        
        if session.services[serviceid]['enabled'] == 1:
            list_item = xbmcgui.ListItem(label=session.services[serviceid]['description'] + ' ' + offers )
        else:
            list_item = xbmcgui.ListItem(label='[COLOR=gray]' + session.services[serviceid]['description'] + ' ' + offers + '[/COLOR]')

        if session.services[serviceid]['enabled'] == 1:
            if len(session.get_services()) > 1:
                menuitems.append(('Zakázat službu', 'RunPlugin(plugin://' + plugin_id + '?action=disable_service&serviceid=' + serviceid + ')',))
        else:
            menuitems.append(('Povolit službu', 'RunPlugin(plugin://' + plugin_id + '?action=enable_service&serviceid=' + serviceid + ')',))
        if first == 0:
            menuitems.append(('Posunout nahoru', 'RunPlugin(plugin://' + plugin_id + '?action=move_service&serviceid=' + serviceid + ')',))
        if len(menuitems) > 0:
            list_item.addContextMenuItems(menuitems)

        xbmcplugin.addDirectoryItem(_handle, None , list_item, False)  
        first = 0
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

def enable_service(serviceid):
    session = Session()
    if serviceid in session.get_services(filtered = 0):
        session.enable_service(serviceid)
    xbmc.executebuiltin('Container.Refresh')   

def disable_service(serviceid):
    session = Session()
    if serviceid in session.get_services():
        session.disable_service(serviceid)
    xbmc.executebuiltin('Container.Refresh')  

def move_service(serviceid):
    session = Session()
    if serviceid in session.get_services(filtered = 0):
        service = session.get_service(serviceid)
        old_order = service['order']
        new_order = old_order - 1
        for replaced_serviceid in session.get_services(filtered = 0):
            replaced_service = session.get_service(replaced_serviceid)
            if replaced_service['order'] == new_order:
                session.set_service_order(replaced_serviceid, old_order)
        session.set_service_order(serviceid, new_order)
    xbmc.executebuiltin('Container.Refresh')  

def list_devices(label):
    xbmcplugin.setPluginCategory(_handle, label)   
    session = Session()
    for serviceid in session.get_services():
        data = call_o2_api(url = 'https://api.o2tv.cz/unity/api/v1/devices/', data = None, header = get_header_unity(session.services[serviceid]))
        if 'err' in data:
            xbmcgui.Dialog().notification('Sledování O2TV','Problém při zjištování spárovaných zařízení', xbmcgui.NOTIFICATION_ERROR, 4000)
            sys.exit()   
        if 'pairedDeviceAddLimit' in data and 'sessionLimit' in data and 'result' in data:
            list_item = xbmcgui.ListItem(label='Limit souběžných přehrávání: ' + str(int(data['sessionLimit'])))
            xbmcplugin.addDirectoryItem(_handle, None, list_item, False)               
        else:
            xbmcgui.Dialog().notification('Sledování O2TV','Problém při zjištování spárovaných zařízení', xbmcgui.NOTIFICATION_ERROR, 4000)
            sys.exit() 

        data = call_o2_api(url = 'https://app.o2tv.cz/sws/subscription/settings/subscription-configuration.json', data = None, header = get_header(session.services[serviceid]))        
        if 'err' in data:
            xbmcgui.Dialog().notification('Sledování O2TV','Problém při zjištování spárovaných zařízení', xbmcgui.NOTIFICATION_ERROR, 4000)
            sys.exit()     
        if 'pairedDevicesLimit' in data and 'pairedDevices' in data:
            list_item = xbmcgui.ListItem(label='Spárovaných zařízení: ' + str(len(data['pairedDevices'])) + '/' + str(int(data['pairedDevicesLimit'])))
            xbmcplugin.addDirectoryItem(_handle, None, list_item, False)    
            if len(data['pairedDevices']) > 0:
                devices = sorted(data['pairedDevices'], key=lambda k: k['lastLoginTimestamp'])
                for device in devices:
                    list_item = xbmcgui.ListItem(label=device['deviceName'] + ' (' + str(device['deviceId']) +  ') - ' + datetime.fromtimestamp(device['lastLoginTimestamp']/1000).strftime('%d.%m.%Y') + ' z ' + device['lastLoginIpAddress'])
                    list_item.addContextMenuItems([('Smazat zařízení', 'RunPlugin(plugin://' + plugin_id + '?action=unpair_device&deviceId=' + quote(encode(str(device['deviceId']))) + '&deviceName=' + quote(encode(device['deviceName'])) + '&serviceid=' + serviceid + ')',)])       
                    xbmcplugin.addDirectoryItem(_handle, None , list_item, False)  
        else:
            xbmcgui.Dialog().notification('Sledování O2TV','Problém při zjištování spárovaných zařízení', xbmcgui.NOTIFICATION_ERROR, 4000)
            sys.exit()         
    xbmcplugin.endOfDirectory(_handle, cacheToDisc = False)

 #   post = {'deviceId' : '71ac1c50-b622-4243-84ac-e66603c4935e', 'deviceName' : 'Prohlížeč Firefox'}
 #   data = call_o2_api(url = 'https://app.o2tv.cz/sws/subscription/settings/set-device-name.json', data = urlencode(post), header = o2api.header)        

def unpair_device(deviceId, deviceName, serviceid):
    session = Session()
    if deviceId == 'None':
        deviceId = ''
    response = xbmcgui.Dialog().yesno('Smazání zařízení', 'Opravdu smazat spárované zařízení ' + deviceName + ' (' + deviceId + ')'+ '?', nolabel = 'Ne', yeslabel = 'Ano')
    if response:
        post = {'deviceId' : deviceId}
        data = call_o2_api(url = 'https://app.o2tv.cz/sws/subscription/settings/remove-device.json', data = post, header = get_header(session.services[serviceid]))        
        if data != None and 'err' in data:
            xbmcgui.Dialog().notification('Sledování O2TV','Problém při smazání spárovaného zařízení', xbmcgui.NOTIFICATION_ERROR, 4000)
            sys.exit()     
        xbmcgui.Dialog().notification('Sledování O2TV','Může trvat i cca. hodinu, než se změna projeví', xbmcgui.NOTIFICATION_INFO, 4000)
        xbmc.executebuiltin('Container.Refresh')
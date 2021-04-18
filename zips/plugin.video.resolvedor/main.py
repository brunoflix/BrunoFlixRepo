# -*- coding: utf-8 -*-

import sys
try:
    import cookielib
except ImportError:
    import http.cookiejar as cookielib
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
import re
import os
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import ntpath
import resolveurl
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
home = xbmc.translatePath(__addon__.getAddonInfo('path').decode('utf-8'))


def notify(message, timeShown=5000):
    #xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (__addonname__, message, timeShown, __icon__))
    xbmc.executebuiltin('Notification(%s, %s, %d)' % (__addonname__, message, timeShown))


def getRequest(url, ref):
    try:
        if ref > '':
            ref2 = ref
        else:
            ref2 = url
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders=[('Accept-Language', 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'),('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'),('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'), ('Referer', ref2)]
        data = opener.open(url).read()
        response = data.decode('utf-8')
        return response
    except:
        response = ''
        return response
        

def player(name,url,sub):
    liz = xbmcgui.ListItem(name)
    if name > '':
        liz.setInfo(type='Video', infoLabels={'Title':name})
    liz.setProperty("IsPlayable","true")
    liz.setPath(str(url))
    if sub !=[]:
        liz.setSubtitles(sub)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
    


def streamtape(url,subtitle):
    correct_url = url.replace('streamtape.com/v/', 'streamtape.com/e/')
    data = getRequest(correct_url, '')
    link_part1_re = re.compile('videolink.+?style="display:none;">(.*?)&token=').findall(data)
    link_part2_re = re.compile("<script>.+?token=(.*?)'.+?</script>").findall(data)
    name_re = re.compile('meta.+?name="og:title".+?content="(.+?)"').findall(data)
    subs = re.compile('<track.+?label.+?src="(.+?)".+?kind="captions".+?default.+?/>').findall(data)
    if link_part1_re !=[] and link_part2_re !=[]:
        link = 'https:'+link_part1_re[0]+'&token='+link_part2_re[0]
    else:
        link = ''
    if name_re !=[]:
        name = name_re[0]
    else:
        name = 'Streamtape'
    if subs !=[]:
        sub = subs           
    else:
        sub = []
        if subtitle > '':
            sub.append(subtitle)       
    if link > '':
        player(name,link,sub)
    else:
        notify('Não foi possivel reproduzir o video.')
        

        
def netcine(url):
    data = getRequest(url, '')
    idioma_re = re.compile('<iframe.+?src="(.+?)".+?</iframe>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    title1_re = re.compile('<div class="datos episodio">.+?<h1>(.+?)</h1>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    title2_re = re.compile('<div class="dataplus">.+?<h1>(.+?)</h1>', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    if title1_re !=[]:
        title = title1_re[0]
    elif title2_re !=[]:
        title = title2_re[0]
    else:
        title = ''
    if idioma_re !=[]:
        names = []
        links = []
        for url_idioma in idioma_re:
            if re.search("Dub",url_idioma,re.IGNORECASE):
                names.append('Dublado')
                links.append(url_idioma)
            elif re.search("Leg",url_idioma,re.IGNORECASE) and not int(url_idioma.count("LEG")) > 1 and not int(url_idioma.count("leg")) > 1:
                names.append('Legendado')
                links.append(url_idioma)
            elif re.search("Leg",url_idioma,re.IGNORECASE) and not re.search("Dub",url_idioma,re.IGNORECASE):
                names.append('Legendado')
                links.append(url_idioma)
            else:
                names.append('Dublado')
                links.append(url_idioma)
        dialog = xbmcgui.Dialog()
        index = dialog.select('Escolha um tipo', names)
        if index >= 0:
            playname=names[index]
            playlink=links[index]
            stream = netcine_resolve(playlink)
            if title > '':
                fullname = title+' - '+playname
            else:
                fullname = playname
            if stream > '':
                sub = []
                player(fullname,stream,sub)
            else:
                notify('Não foi possivel reproduzir o video.')
    else:
        notify('Não foi possivel reproduzir o video.')
                
                
                
def netcine_resolve(url,LOG=False):
    data = getRequest(url, '')
    if LOG:
        try:
            f = open(xbmc.translatePath(home+'/LOG-URLRESOLVE.txt'),'w')
            f.write(data)
            f.close()
        except:
            pass
    page_select = re.compile('iframe.+?src="(.+?)"', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    page1 = re.compile("location.href='(.+?)'", re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    page2 = re.compile('<div.+?class="itens">.+?<a.+?href.+?=".+?data=(.+?)"', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    if page_select !=[]:
        for url_iframe in page_select:
            if url_iframe.find('selec') >= 0:
                data_iframe = getRequest(url_iframe, '')
                data_iframe_RE = re.compile('data=(.+?)"', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data_iframe)
                if data_iframe_RE !=[]:
                    try:
                        player = data_iframe_RE[0]
                        resolved = netcine_resolve(player)
                    except:
                        resolved = ''
                else:
                    resolved = ''
            elif url_iframe.find('camp') >= 0:
                data_iframe = getRequest(url_iframe, '')
                data_iframe_RE = re.compile('data=(.+?)"', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data_iframe)
                if data_iframe_RE !=[]:
                    try:
                        player = data_iframe_RE[0]
                        resolved = netcine_resolve(player)
                    except:
                        resolved = ''
                else:
                    resolved = ''            
            else:
                data_iframe = getRequest(url_iframe, '')
                data_iframe_RE = re.compile('data=(.+?)"', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data_iframe)
                if data_iframe_RE !=[]:
                    try:
                        player = data_iframe_RE[0]
                        resolved = netcine_resolve(player)
                    except:
                        resolved = ''
                else:
                    resolved = ''       
    elif page1 !=[]:
        for player_url in page1:
            if player_url.find('desktop') >= 0:
                page2 = getRequest(player_url, '')
                video_url_RE = re.compile("file':'(.+?)'", re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(page2)
                if video_url_RE !=[]:
                    for video_url in video_url_RE:
                        if video_url.find('-ALTO') >= 0:
                            resolved = video_url
                        else:
                            resolved = ''
                else:
                    resolved = ''
            #else:
            #    try:
            #        resolved = urlresolve(page1[0])
            #    except:
            #        resolved = ''
    elif page2 !=[]:
        try:
            player = page2[0]
            data = getRequest(player, '')
            video_url_RE = re.compile('file:.+?"(.+?)"', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
            if video_url_RE !=[]:
                for video_url in video_url_RE:
                    if video_url.find('-ALTO') >= 0:
                        resolved = video_url
                    else:
                        resolved = ''
            else:
                resolved = ''
        except:
            resolved = '' 
    else:
        video_url_RE = re.compile("file':'(.+?)'", re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
        if video_url_RE !=[]:
            for video_url in video_url_RE:
                if video_url.find('-ALTO') >= 0:
                    resolved = video_url
                else:
                    resolved = ''
        else:
            resolved = ''
    return resolved          
        

def videobin(name,url,subtitle):
    data = getRequest(url, '')
    source_re = re.compile('sources:.+?"(.+?)"', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    sub_re = re.compile("subtitle.+?src:.+?'(.+?)',", re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    if sub_re !=[]:
        sub = []
        sub.append(sub_re[0])
    else:
        sub = []
        if subtitle > '':
            sub.append(subtitle)
    if source_re !=[]:
        link = source_re[0]
    else:
        link = ''
    if link > '':
        player(name,link,sub)
    else:
        notify('Não foi possivel reproduzir o video.')


def clipwatching(name,url,subtitle):
    data = getRequest(url, '')
    source_re = re.compile('sources.+?src.+?"(.+?)",', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    if subtitle > '':
        sub = []
        sub.append(subtitle)
    else:
        sub = []
    if source_re !=[]:
        link = source_re[0]
    else:
        link = ''
    if link > '':
        player(name,link,sub)
    else:
        notify('Não foi possivel reproduzir o video.')
        

def vidoza(name,url,subtitle):
    data = getRequest(url, '')
    name_re = re.compile('var.+?curFileName.+?=.+?"(.+?)";', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    source_re = re.compile('sourcesCode.+?src.+?"(.+?)",', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    subs_re = re.compile('<track.+?kind="subtitles".+?src="(.+?)".+?srclang.+?label.+?>').findall(data)
    if name_re !=[]:
        name2 = name_re[0]
    else:
        name2 = name
    if subs_re !=[]:
        parsed_uri = urlparse(url)
        hostname = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        sub = []
        for subs in subs_re:
            sub.append(hostname+subs)
    else:
        sub = []
        if subtitle > '':
            sub.append(subtitle) 
    if source_re !=[]:
        link = source_re[0]
    else:
        link = ''
    if link > '':
        player(name2,link,sub)
    else:
        notify('Não foi possivel reproduzir o video.')
                

def vidlox(name,url,subtitle):
    data = getRequest(url, '')
    source_re = re.compile('sources:.+?,"(.+?)"', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    sub_re = re.compile("subtitle.+?src:.+?'(.+?)',", re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    if sub_re !=[]:
        sub = []
        sub.append(sub_re[0])
    else:
        sub = []
        if subtitle > '':
            sub.append(subtitle)
    if source_re !=[]:
        link = source_re[0]
    else:
        link = ''
    if link > '':
        player(name,link,sub)
    else:
        notify('Não foi possivel reproduzir o video.')


def topflix(name,url,subtitle):
    try:
        code_re = re.compile('code=(.+?);', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(url)
        url2 = url.replace(';', '')
        new_url = url2.replace(code_re[0],code_re[0]+';')
    except:
        new_url = ''
    data = getRequest(new_url, 'https://topflix.tv/')
    source_re = re.compile('source.+?src="(.+?)".+?type', re.MULTILINE|re.DOTALL|re.IGNORECASE).findall(data)
    subs_re = re.compile("<track.+?kind='captions'.+?src='(.+?)'.+?srclang.+?label.+?default></track>").findall(data)
    if subs_re !=[]:
        parsed_uri = urlparse(url)
        hostname = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        sub = []
        for subs in subs_re:
            sub1 = subs.replace('../..','')
            sub.append(hostname+sub1)
    else:
        sub = []
        if subtitle > '':
            sub.append(subtitle)
    if source_re !=[]:
        link = source_re[0]+'|Referer=https://topflix.tv/'
    else:
        link = ''
    if link > '':
        player(name,link,sub)
    else:
        notify('Não foi possivel reproduzir o video.')
    

def video_sub(name,link,subtitle):
    sub = []
    if subtitle > '':
        sub.append(subtitle)
    if link > '':
        player('',link,sub)
    else:
        notify('Não foi possivel reproduzir o video.')
        
def resolver(url,subtitle):
    try:
        resolved = resolveurl.resolve(url)
    except:
        resolved = ''
    sub = []
    if subtitle > '':
        sub.append(subtitle)
    if resolved > '':
        player('',resolved,sub)
    else:
        notify('Não foi possivel reproduzir o video.')
    
    
def addDir(name,mode,iconimage,fanart,description):
    u=sys.argv[0]+"?mode="+mode
    liz=xbmcgui.ListItem(name)
    liz.setArt({'icon': 'DefaultFolder.png', 'thumb': iconimage})
    liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': description})
    if fanart > '':
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', home+'/fanart.jpg')
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    
def menu():
    addDir('[B]Tutorial[/B]','tutorial',__icon__,'','Tutorial do Resolvedor')
    addDir('[B]Abrir Repositório[/B]','repositorio',__icon__,'','Repositório')
    addDir('[B]Sobre[/B]','sobre',__icon__,'','')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def repositorio():
    import webbrowser
    link = 'https://github.com/zoreu/resolvedor'
    if xbmc.getCondVisibility('system.platform.windows'):
        webbrowser.open(link)
    if xbmc.getCondVisibility('system.platform.android'):
        xbmc.executebuiltin('StartAndroidActivity(,android.intent.action.VIEW,,%s)' %(link))
    



def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param
    
params=get_params()

try:
    mode = params['mode']
except:
    mode = None
try:
    name = params['nome']
except:
    name = 'Resolvedor'
try:
    url = params['url']
except:
    try:
        url_re = re.compile('url=(.+?)&amp;').findall(str(sys.argv[2]))
        url_re2 = re.compile('url=(.*)').findall(str(sys.argv[2]))
        if url_re !=[]:
            url = url_re[0]
        elif url_re2 !=[]:
            url = url_re2[0]
        else:
            url = ''
    except:
        url = ''
try:
    sub = params['subtitle']
except:
    sub = ''


if url > '':
    #streamtape.com
    if 'streamtape' in url:
        streamtape(url,sub)
    #netcine.info
    elif 'netcine' in url:
        netcine(url)
    #videobin.co
    elif 'videobin' in url:
        #videobin(name,url,sub)
        videobin('',url,sub)
    #clipwatching.com
    elif 'clipwatching' in url:
        clipwatching('',url,sub)
    #vidoza.net
    elif 'vidoza' in url:
        vidoza('',url,sub)
    #vidlox.me    
    elif 'vidlox' in url:
        vidlox('',url,sub)
    elif 'topflix' in url:
        topflix('',url,sub)
    else:
        #video_sub(name,link,sub)
        resolver(url,sub)

          
elif mode == None and url == '':
    menu()
elif mode == 'tutorial' and url == '':
    xbmcgui.Dialog().textviewer('Tutorial', '#Como Utilizar Resolvedor para Legendas:\nplugin://plugin.video.resolvedor?url=<url-do-video>&amp;subtitle=<url-da-legenda>\n\n#Servidor Streamtape.com\nplugin://plugin.video.resolvedor?url=https://streamtape.com/v/86vvg0G9egTXr6/\n\n#Servidor videobin.co\nplugin://plugin.video.resolvedor?url=<url-do-videobin>&amp;nome=TESTE\n\n#Servidor clipwatching.com\nplugin://plugin.video.resolvedor?url=<url-do-clipwatching>&amp;nome=TESTE\n\n#Servidor vidoza.net\nplugin://plugin.video.resolvedor?url=https://vidoza.net/embed-w89e9fo2si4c.html\n\n#Servidor vidlox.me\nplugin://plugin.video.resolvedor?url=<url-do-vidlox>&amp;nome=TESTE')
elif mode == 'repositorio' and url == '':
    repositorio()
elif mode == 'sobre' and url == '':
    xbmcgui.Dialog().textviewer('Sobre', 'Resolvedor é um complemento para addons que trata links para reprodução podendo adicionar legendas externas ao kodi')
else:
    pass
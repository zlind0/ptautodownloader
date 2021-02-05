import requests, os
from bs4 import BeautifulSoup
import shutil,json
from time import sleep
import argparse, re

parser = argparse.ArgumentParser(description='Download automatically from PT Tracker.')
parser.add_argument("--dry", action='store_true')
args = parser.parse_args()


downloaded=set()
torrent_dir=os.getcwd()

conf_lemon={
    "domain":"https://lemonhd.org/",
    "page":["torrents_new.php"],
    "col_sz":5,
    "max_uploader":2,
    "max_concurrent":1,
    "disk_save":8000,
    "max_size":15000,
    "headers":{
    }
}

conf_opencd={
    "domain":"https://open.cd/",
    "page":["torrents.php"],
    "col_sz":7,
    "max_uploader":15,
    "max_concurrent":5,
    "max_size":8000,
    "disk_save":2000,
    "headers":{
    }

}
# response = requests.get('https://lemonhd.org/torrents_music.php', headers=headers)

def getpages(conf):
    retval=[]
    for p in conf["page"]:
        response=requests.get(conf["domain"]+p, headers=conf["headers"])
        retval.append(response)
    return retval
        
# units = {"B": 1, "KB": 2**10, "MB": 2**20, "GB": 2**30}
def parse_size(size):
    if size is not None:
        unit_GB=1024 if "GB" in size else 1
        return int(float(re.search(r'[0-9.]+', size).group())*unit_GB)
    else: 
        return 0

def getlist(response, conf):
    retval=[]
    soup = BeautifulSoup(response.text,'html.parser')
    
#     table_header=soup.select("table.torrents > tr > td.colhead")
#     table_header=[i.text for i in table_header]
#     print(table_header)
    
    for item in soup.select(".torrentname"):
#         try:
            title=item.text.strip()
            free=True if len(item.select(".pro_free"))>0 or len(item.select(".pro_free2up"))>0 else False
            cols=item.parent.parent.select_one(f"td.rowfollow:nth-of-type({conf['col_sz']})")
            size=parse_size(cols.text)

            up=int(item.parent.parent.select_one(f"td.rowfollow:nth-of-type({conf['col_sz']+1})").text)
            down=int(item.parent.parent.select_one(f"td.rowfollow:nth-of-type({conf['col_sz']+2})").text)

            links=item.select("a")
            for l in links:
                if "download.php" in l["href"]:
                    link=conf["domain"]+l["href"]
            itemmeta={"title":title, "free":free, "link":link, "size_mb":size,"up":up,"down":down}
            retval.append(itemmeta)
#         except: pass
    return retval

def wgettr(downloadtr,conf,filename="test.torrent"):
    with open(os.path.join(torrent_dir, filename),"wb") as f:
        f.write(requests.get(downloadtr["link"], headers=conf["headers"]).content)


def download_best_from_conf(conf,filename="test.torrent",prevent_realdownload=False):
    trpages=getpages(conf)
    print("[Info] Get Webpage")
    trlist=getlist(trpages[0], conf)
    print("[Info] Get Torrent list, length=%s"%len(trlist))
    free_mb=shutil.disk_usage(torrent_dir).free/2**20
    wantlist=list(filter(lambda x: x["up"]<conf["max_uploader"] and\
                         x["size_mb"]<min(conf["max_size"], free_mb-conf["disk_save"]) and\
                         x["free"]==True, trlist))
    sortlist=sorted(wantlist, key=lambda x: x["down"],reverse=True)
    
    downloadleft=conf["max_concurrent"]
    for downloadtr in sortlist:
        if downloadtr["link"] not in downloaded and downloadleft>0:
            downloadleft-=1
            downloaded.add(downloadtr["link"])
            free_mb-=downloadtr['size_mb']
            print(f"[Info] Select {downloadtr['title']}")
            print(f"[Info] Size {downloadtr['size_mb']}MB/{free_mb}MB Free. [Up {downloadtr['up']}/{downloadtr['down']} Down]")
            if not prevent_realdownload:
                wgettr(downloadtr, conf, filename)
            
while True:
    download_best_from_conf(conf_opencd, prevent_realdownload=args.dry)
    sleep(300)

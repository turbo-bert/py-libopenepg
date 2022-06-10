from pprint import pprint as PP
#import requests
import datetime
import time
import re
import os.path
import json
import zoneinfo

import logging
import time
#FORMAT = '%(asctime)s+00:00 %(levelname)10s: %(message)-80s    (%(filename)s,%(funcName)s:%(lineno)s)'
FORMAT = '%(asctime)s+00:00 %(levelname)10s: %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logging.Formatter.converter = time.gmtime


#notes: ARD and RTL handle days differently, in ARD post 00:00 features are from the next day. previous are mssing


def list_channels():
    """Return all known broadcast channel name identifiers."""
    return ['ard', 'wdr', 'arte', 'br', 'rbb', 'mdr', 'ndr', 'rbtv', 'sr', 'swrbw', 'swrrp', 'ardalpha', 'one', 'kika', 'phoenix', 'rtl', 'tagesschau24', 'vox', 'zdf', 'sat1', 'kabel1', 'rtl2', 'wdr2.fm', 'wdr5.fm']


def get_livestream_site(channel_name):
    if channel_name == 'zdf':
        return 'https://www.zdf.de/live-tv'
    return None


def ultracompat(src):
    """Trim down a string to the minimum character set needed to understand what was inside."""
    tr_ok = "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
    tr = {
        "&": ' und ',
        "ä": 'ae',
        "ü": 'ue',
        "ö": 'oe',
        "Ä": 'Ae',
        "Ü": 'Ue',
        "Ö": 'Oe',
        "ß": "ss",
        "(": " ",
        ")": " "
    }
    for ok in tr_ok:
        tr[ok] = ok
    
    n=""
    for c in src:
        if c in tr.keys():
            n+= tr[c]
    n = n.strip()
    n = re.sub(' +', ' ', n)
    return n


def ultratime4digit(src):
    s = re.sub('[^0-9]', '', src)
    h = int(s[0:2])
    m = int(s[2:4])
    return "%02d%02d" % (h, m)


def transparent_get(url, filename, cfg):
    """Proxy function for download HTTP content via GET to a local file (cfg will decide if curl or requests is used)."""
    logging.info("retrieve [%s] to [%s]" % (url, filename))
    http_get_via_requests(url, filename)


def http_get_via_curl(url, filename):
    """Not implemented - downlaod via curl."""
    pass


def http_get_via_requests(url, filename):
    """Download http/get url to local file with requests."""
    import requests
    if os.path.isfile(filename):
        logging.info("CACHED")
        return
    with open(filename, 'w') as f:
        f.write(requests.get(url).text)


def generate_forecast_dates_de(day_count=7):
    """Create an array of strings with german formatted days starting from today."""
    res=[]
    unow = datetime.datetime.utcnow()
    unext = unow - datetime.timedelta(hours=24)
    for i in range(0,day_count):
        unext = unext + datetime.timedelta(hours=24)
        x=unext.isoformat().split("T")[0].split("-")
        next_en=unext.isoformat().split("T")[0]
        next_de = ".".join(reversed(x))
        res.append(next_de)
    return res


def generate_forecast_dates_iso(day_count=7):
    """Create an array of strings with ISO formatted (pre-"T") days starting from today."""
    res=[]
    unow = datetime.datetime.utcnow()
    unext = unow - datetime.timedelta(hours=24)
    for i in range(0,day_count):
        unext = unext + datetime.timedelta(hours=24)
        x=unext.isoformat().split("T")[0].split("-")
        next_en=unext.isoformat().split("T")[0]
        res.append(next_en)
    return res


def get_cachedir():
    """Return the name of the cache directory and create it if necessary."""
    d = os.path.expanduser(os.path.join('~', '.openepg_cache'))
    if not os.path.isdir(d):
        os.makedirs(d)
    return d


def empty_conf_lines():
    """Create lines for an default config."""
    return """{
    "channels": [ "ard" ]
}
"""


def get_conf_lines():
    """Load all ~/.openepg_config lines."""
    filename = os.path.expanduser(os.path.join('~', '.openepg_config'))
    if not os.path.isfile(filename):
        with open(filename, 'w') as f:
            f.write('')
    lines=[]
    with open(filename, 'r') as f:
        lines = f.read().strip().replace("\r\n", "\n").split("\n")
    if len(lines) == 1 and lines[0]=='':
        lines = empty_conf_lines().split("\n")
    return lines


def get_conf():
    """Load the program config."""
    return json.loads("\n".join(get_conf_lines()))


def retrieve_raw_data_for_date(date_de, date_en):
    #transparent_get()
    pass


def run_update():
    """Run a full update/refresh on all channels or configured ones."""
    cache_dir = get_cachedir()
    cfg = get_conf()
    days = 7;
    logging.info("Running update")
    dates_de = generate_forecast_dates_de(day_count=days)
    dates_iso = generate_forecast_dates_iso(day_count=days)
    for i in range(0, len(dates_de)):
        logging.info("processing day %s" % dates_de[i])
        for c in list_channels():
            logging.info("processing day %s for channel %s" % (dates_de[i], c))
            filename = c + "-" + dates_iso[i]
            filename = os.path.join(cache_dir, filename)
            url = url_generator_day_program(c, dates_iso[i])
            transparent_get(url, filename, cfg)
            process_data(c, filename, dates_iso[i], url)


def process_data(channel_name, filename, iso_day, url):
    logging.info("Extracting program data...")
    filename_out = filename + ".txt"
    
    data = None
    raw_data = None
    with open(filename, 'r') as f:
        raw_data = f.read().strip()
        raw_data = raw_data.replace('&amp;', ' und ')

    if channel_name in ['ard', 'wdr', 'arte', 'br', 'rbb', 'mdr', 'ndr', 'rbtv', 'sr', 'swrbw', 'swrrp', 'ardalpha', 'one', 'kika', 'phoenix', 'tagesschau24']:
        data = processing_helper_ardclass(channel_name, raw_data, iso_day, url)

    if channel_name in ['rtl']:
        data = processing_helper_rtlclass(channel_name, raw_data, iso_day, url)

    if channel_name in ['sat1']:
        data = processing_helper_sat1class(channel_name, raw_data, iso_day, url)

    if channel_name in ['vox']:
        data = processing_helper_voxclass(channel_name, raw_data, iso_day, url)

    if channel_name in ['kabel1']:
        data = processing_helper_sat1class(channel_name, raw_data, iso_day, url)
        #data = processing_helper_kabel1class(channel_name, raw_data, iso_day, url)

    if channel_name in ['rtl2']:
        data = processing_helper_sat1class(channel_name, raw_data, iso_day, url)

    if channel_name in ['zdf']:
        data = processing_helper_zdfclass(channel_name, raw_data, iso_day, url)

    if channel_name in ['wdr2.fm']:
        data = processing_helper_wdr2class(channel_name, raw_data, iso_day, url)

    if channel_name in ['wdr5.fm']:
        data = processing_helper_wdr5class(channel_name, raw_data, iso_day, url)

    if data == None:
        data = "unprocessed"

    with open(filename_out, 'w') as f:
        f.write(data)


def iso2dedate(iso_date):
    """Convert a string "YYYY-MM-DD" to "DD.MM.YYYY"."""
    x=iso_date.split("-")
    return ".".join(reversed(x))


def url_generator_day_program(channel_name, iso_day):
    """Generate the URL for the daily program overview for a given date."""
    if channel_name == 'ard':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28106'
    if channel_name == 'wdr':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=-28111'
    if channel_name == 'arte':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28724'
    if channel_name == 'br':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=-28107'
    if channel_name == 'rbb':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=-28205'
    if channel_name == 'mdr':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=-28229'
    if channel_name == 'ndr':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=-28226'
    if channel_name == 'rbtv':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28385'
    if channel_name == 'sr':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28486'
    if channel_name == 'swrbw':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28113'
    if channel_name == 'swrrp':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28231'
    if channel_name == 'ardalpha':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28231'
    if channel_name == 'one':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28722'
    if channel_name == 'kika':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28008'
    if channel_name == 'phoenix':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28725'
    if channel_name == 'tagesschau24':
        return 'https://programm.ard.de/TV/Programm/Sender?datum='+iso2dedate(iso_day)+'&hour=0&sender=28721'
    if channel_name == 'wdr2.fm':
        return 'https://www.wdr.de/programmvorschau/wdr2/uebersicht/'+iso_day+'/'
    if channel_name == 'wdr5.fm':
        return 'https://www.wdr.de/programmvorschau/wdr5/uebersicht/'+iso_day+'/'
    if channel_name == 'vox':
        return 'https://www.vox.de/fernsehprogramm/' + iso_day
    if channel_name == 'rtl':
        return 'https://www.rtl.de/fernsehprogramm/' + iso_day
    if channel_name == 'sat1':
        #return 'https://www.sat1.de/fernsehprogramm/' + iso_day
        #return 'https://magellan-api.p7s1.io/epg-broadcast/sat1.de/graphql?operationName=&query=%20query%20EpgQuery($domain:%20String!,%20$type:%20EpgType!,%20$date:%20DateTime)%20{%20site(domain:%20$domain)%20{%20epg(type:%20$type,%20date:%20$date)%20{%20items%20{%20...fEpgItem%20tvShowTeaser(timeSlot:%20PRIMETIME)%20{%20...fTeaserItem%20}%20teaser(timeSlot:%20PRIMETIME)%20{%20...fTeaserItem%20}%20}%20}%20}%20}fragment%20fEpgItem%20on%20EpgItem%20{%20id%20title%20description%20startTime%20endTime%20episode%20{%20number%20}%20season%20{%20number%20}%20tvShow%20{%20title%20id%20}%20images%20{%20url%20title%20copyright%20}%20links%20{%20href%20contentType%20title%20}%20}%20fragment%20fTeaserItem%20on%20TeaserItem%20{%20id%20url%20info%20headline%20contentType%20channel%20{%20...fChannelInfo%20}%20branding%20{%20...fBrand%20}%20site%20picture%20{%20url%20}%20pictures%20{%20url%20dimension%20name%20title%20copyright%20description%20orientation%20imageOverlayTarget%20imageOverlayType%20kicker%20}%20videoType%20orientation%20date%20flags%20fsk%20videoId%20valid%20{%20from%20to%20}%20epg%20{%20episode%20{%20...fEpisode%20}%20season%20{%20...fSeason%20}%20duration%20nextEpgInfo%20{%20...fEpgInfo%20}%20}%20}%20fragment%20fChannelInfo%20on%20ChannelInfo%20{%20title%20shortName%20cssId%20cmsId%20}%20fragment%20fBrand%20on%20Brand%20{%20id,%20name%20}%20fragment%20fEpisode%20on%20Episode%20{%20number%20}%20fragment%20fSeason%20on%20Season%20{%20number%20}%20fragment%20fEpgInfo%20on%20EpgInfo%20{%20time%20endTime%20primetime%20branding%20{%20name%20}%20}%20&variables={%22date%22:%22' + iso_day + 'T00:00:00.000Z%22,%22domain%22:%22sat1.de%22,%22type%22:%22FULL%22}&initialcv=browser-p7s1-1'
        #return 'https://magellan-api.p7s1.io/epg-broadcast/sat1.de/graphql?operationName=&query=%20query%20EpgQuery($domain:%20String!,%20$type:%20EpgType!,%20$date:%20DateTime)%20{%20site(domain:%20$domain)%20{%20epg(type:%20$type,%20date:%20$date)%20{%20items%20{%20...fEpgItem%20tvShowTeaser(timeSlot:%20PRIMETIME)%20{%20...fTeaserItem%20}%20teaser(timeSlot:%20PRIMETIME)%20{%20...fTeaserItem%20}%20}%20}%20}%20}fragment%20fEpgItem%20on%20EpgItem%20{%20id%20title%20description%20startTime%20endTime%20episode%20{%20number%20}%20season%20{%20number%20}%20tvShow%20{%20title%20id%20}%20images%20{%20url%20title%20copyright%20}%20links%20{%20href%20contentType%20title%20}%20}%20fragment%20fTeaserItem%20on%20TeaserItem%20{%20id%20url%20info%20headline%20contentType%20channel%20{%20...fChannelInfo%20}%20branding%20{%20...fBrand%20}%20site%20picture%20{%20url%20}%20pictures%20{%20url%20dimension%20name%20title%20copyright%20description%20orientation%20imageOverlayTarget%20imageOverlayType%20kicker%20}%20videoType%20orientation%20date%20flags%20fsk%20videoId%20valid%20{%20from%20to%20}%20epg%20{%20episode%20{%20...fEpisode%20}%20season%20{%20...fSeason%20}%20duration%20nextEpgInfo%20{%20...fEpgInfo%20}%20}%20}%20fragment%20fChannelInfo%20on%20ChannelInfo%20{%20title%20shortName%20cssId%20cmsId%20}%20fragment%20fBrand%20on%20Brand%20{%20id,%20name%20}%20fragment%20fEpisode%20on%20Episode%20{%20number%20}%20fragment%20fSeason%20on%20Season%20{%20number%20}%20fragment%20fEpgInfo%20on%20EpgInfo%20{%20time%20endTime%20primetime%20branding%20{%20name%20}%20}%20&variables={%22date%22:%222022-06-08T00:00:00.000Z%22,%22domain%22:%22sat1.de%22,%22type%22:%22FULL%22}&queryhash=7c95c3c04723a62f6cc4f6045a342ba50d5922a59faa6cfa6c62b105fb784a48&initialcv=browser-p7s1-1'
        return 'https://www.tvspielfilm.de/tv-programm/sendungen/?page=1&order=time&date='+iso_day+'&cat%5B%5D=SP&cat%5B%5D=SE&cat%5B%5D=RE&cat%5B%5D=U&cat%5B%5D=KIN&cat%5B%5D=SPO&time=day&channel=SAT1'
    if channel_name == 'kabel1':
        return 'https://www.tvspielfilm.de/tv-programm/sendungen/?page=1&order=time&date='+iso_day+'&cat%5B%5D=SP&cat%5B%5D=SE&cat%5B%5D=RE&cat%5B%5D=U&cat%5B%5D=KIN&cat%5B%5D=SPO&time=day&channel=K1'
    if channel_name == 'rtl2':
        return 'https://www.tvspielfilm.de/tv-programm/sendungen/?page=1&order=time&date='+iso_day+'&cat%5B%5D=SP&cat%5B%5D=SE&cat%5B%5D=RE&cat%5B%5D=U&cat%5B%5D=KIN&cat%5B%5D=SPO&time=day&channel=RTL2'
    if channel_name == 'zdf':
        return 'https://www.zdf.de/live-tv?airtimeDate=' + iso_day
    return None


def processing_helper_zdfclass(channel_name, raw_data, iso_day, url):
    h3_parts = raw_data.replace("\r", "").replace("\n", " ").split('<h3 id="timeline')[1:]
    h3_parts_cleaner = []

    zdf = None
    sendungen = None

    for p in h3_parts:
        pp = re.sub('^[^>]*>', '', p)
        h3_head = pp.split("</h3>")[0]
        if h3_head == "ZDF Programm":
            zdf = re.sub(' +', ' ', pp).strip()
            zdf = re.sub('> +<', '><', zdf)
    
    if zdf:
        all_transmissions = zdf.split("aria-label=")[1:]
        start_times = []
        for t in all_transmissions:
            time_part = t.split('<span class="time">')[1].split("<")[0]
            if time_part is None or time_part == "":
                continue
            time_part = ultratime4digit(time_part)
            title_part = ultracompat(t[1:].split('"')[0])
            start_times.append(time_part.replace(":", "")[0:4] + "/" + title_part)
    
    return json.dumps(start_times, indent=4)


def processing_helper_kabel1class(channel_name, raw_data, iso_day, url):
    return ""


def processing_helper_voxclass(channel_name, raw_data, iso_day, url):
    """Process a typical day overview HTML file from vox."""
    lines = []
    time_parts = raw_data.replace("\r", "").replace("\n", " ").split('<h3 class="time">')[1:]

    for tp in time_parts:
        items = tp.split("</h3>")
        str_time = items[0].replace(":", "")
        str_title = items[1]
        str_title = re.sub('<h3[^>]+>', '', str_title)
        str_title = re.sub('<span[^>]+>[^<]*</span>', '', str_title).strip()
        str_title = ultracompat(str_title)


        lines.append(str_time + "/" + str_title)

    return "\n".join(lines)


def processing_helper_rtlclass(channel_name, raw_data, iso_day, url):
    """Process a typical day overview HTML file from rtl.de."""
    title_parts = raw_data.replace("</br>", " ").split('<p class="title')
    titles = []
    for t in title_parts:
        inner = t.split(">")[1].split("<")[0].strip().replace("\n", " ").strip()
        inner = re.sub(' +', ' ', inner).strip()
        timespec = inner[0:2]+inner[3:5]
        #todo:check time
        title = ultracompat(inner[6:])
        if inner is not None and inner != "":
            titles.append(timespec + "/" + title)

    return "\n".join(titles)


def processing_helper_wdr2class(channel_name, raw_data, iso_day, url):
    return ""

def processing_helper_wdr5class(channel_name, raw_data, iso_day, url):
    return ""

def processing_helper_sat1class(channel_name, raw_data, iso_day, url):
    """Process a typical day overview HTML file from sat1.de."""
    items = raw_data.replace("\r", "").replace("\n", " ").split('saveRef();" class="js-track-link" title="')[1:]
    all_titles=[]
    all_times=[]
    combined_items=[]

    for item in items:
        the_title = ultracompat(item.split('"')[0])
        all_titles.append(the_title)
        the_time = ultratime4digit("".join(item.split('broadcastTime":"')[1].split('"')[0].split("T")[1].split(':')[0:2]))
        all_times.append(the_time)
        combined_items.append(the_time + "-" + the_title)


    return "\n".join(combined_items)


def processing_helper_ardclass(channel_name, raw_data, iso_day, url):
    """Process a typical day overview HTML file from programm.ard.de which works for multiple channels."""
    text_content = raw_data
    self_ref = url
    self_sender = channel_name

    self_base = self_ref.split(":")[0] + "://" + self_ref.split("/")[2]
    data = text_content.replace("\t", " ").replace("\r", "")
    data = data.split('<div class="print-headline">')[1]
    data = data.split('</ul')[0]
    items = data.split('<a class="sendungslink')[1:]

    objs = []
    for i in items:
        ij = i.replace("\n", " ")
        x = {}
        tmp = i.split(' href="')[1].split('"')[0]
        x["sender"] = self_sender
        x["parent_url"] = url
        x["info_url"] = self_base + tmp
        y = ij.split('<span class="date')[1].split(">")[1].split("<")[0].strip().replace(":", "")
        x["t"] = y
        x["d"] = iso_day
        x["tf"] = iso_day + "T" + x["t"][0:2] + ":" + x["t"][2:4] + ":00+CET"
        y = ij.split('<span class="title')[1].split(">")[1].split("<")[0].strip()
        x["title"] = y
        y = ij.split('<span class="subtitle')[1].split(">")[1].split("<")[0].strip()
        if y != "":
            x["title"] += " - " + y
        x["title"] = ultracompat(x["title"])
        objs.append(x)

    return (json.dumps(objs, indent=4))

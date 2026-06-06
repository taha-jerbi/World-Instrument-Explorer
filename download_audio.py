"""
download_audio.py — Download samples for ALL instruments from the frontend map
===============================================================================
Reads every instrument name from index.html and downloads the best matching
sample from Freesound.org. Uses fallback search terms for obscure instruments.

1. Get a free API key: https://freesound.org/apiv2/apply
2. Paste it below where it says YOUR_API_KEY_HERE
3. Run:  python download_audio.py

Re-running is safe — already downloaded files are skipped.
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import time
import re
import os
import sys
import ssl
from pathlib import Path

# ── PASTE YOUR API KEY HERE ──────────────────────────────────────────────────
API_KEY = os.environ.get("FREESOUND_API_KEY", "QudLR0dSbKMpWBtBRgevN5qLCVoTuVqUEkdUYT9J")
# ─────────────────────────────────────────────────────────────────────────────

AUDIO_DIR = Path(__file__).parent / "audio"
AUDIO_DIR.mkdir(exist_ok=True)

HEADERS = {"User-Agent": "WorldInstrumentsExplorer/2.0"}
DELAY   = 1.2

try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl._create_unverified_context()


# ── Fallback search terms for instruments Freesound doesn't know by name ─────
# Format: "exact instrument name" -> list of fallback queries to try in order
FALLBACKS = {
    # African
    "Adungu":           ["arched harp africa", "bow harp uganda"],
    "Akogo":            ["thumb piano africa", "kalimba"],
    "Alumiiu":          ["thumb piano malawi", "mbira"],
    "Apinti":           ["suriname drum", "african drum"],
    "Atenteben":        ["bamboo flute ghana", "african flute"],
    "Atoke":            ["iron bell ghana", "african bell percussion"],
    "Babadok":          ["frame drum cameroon", "african frame drum"],
    "Bangwe":           ["trough zither malawi", "african zither"],
    "Bata":             ["bata drum yoruba", "african sacred drum"],
    "Bodu Beru":        ["maldives drum", "island drum"],
    "Boduberu":         ["maldives drum", "island drum"],
    "Bolon":            ["harp lute guinea", "african harp"],
    "Bung'o":           ["slit drum africa", "log drum"],
    "Davui":            ["conch shell trumpet pacific", "shell horn"],
    "Derua":            ["double bell ghana", "african bell"],
    "Dipela":           ["reed flute botswana", "african flute"],
    "Ekipa":            ["xylophone equatorial guinea", "african xylophone"],
    "Endere":           ["end blown flute uganda", "african flute"],
    "Endongo":          ["lyre uganda", "african lyre"],
    "Engoma":           ["drum uganda", "african drum"],
    "Epara":            ["harp cameroon", "african harp"],
    "Feku":             ["musical bow south africa", "mouth bow"],
    "Fidjeri":          ["gulf singing bahrain", "gulf vocal music"],
    "Fontomfrom":       ["akan drum ghana", "ceremonial drum ghana"],
    "Garamut":          ["slit drum papua new guinea", "log drum oceania"],
    "Garawoun":         ["garifuna drum belize", "central america drum"],
    "Gan":              ["iron bell benin voodoo", "african iron bell"],
    "Gyil":             ["xylophone ghana dagara", "african xylophone"],
    "Hazolahy":         ["madagascar drum", "malagasy drum"],
    "Hebu mataro":      ["tanzania flute", "african flute"],
    "Hindewhu":         ["central africa whistle flute", "african whistle"],
    "Hungu":            ["musical bow angola", "african bow"],
    "Ikembe":           ["thumb piano burundi", "mbira"],
    "Inanga":           ["trough zither rwanda", "african zither"],
    "Ingoma":           ["burundi royal drum", "african ceremonial drum"],
    "Iningiri":         ["bow lute burundi", "african bow lute"],
    "Isukuti":          ["kenya drum luhya", "african drum"],
    "Kaban":            ["uzbek percussion", "central asia drum"],
    "Kakalo":           ["mozambique guitar", "african plucked string"],
    "Kakaki":           ["long trumpet nigeria hausa", "ceremonial trumpet africa"],
    "Kidi":             ["ewe drum ghana", "akan drum"],
    "Kinde":            ["bow harp chad", "african harp"],
    "Kirar":            ["eritrea lyre", "ethiopian lyre"],
    "Kissange":         ["lamellaphone angola", "thumb piano africa"],
    "Kombu":            ["kerala horn india", "south india horn"],
    "Kpelle Harp":      ["harp liberia", "african harp"],
    "Kudyapi":          ["philippine boat lute", "philippine string"],
    "Kulintang":        ["gong philippines", "southeast asia gong"],
    "Kuntigi":          ["plucked lute gambia", "west africa string"],
    "Lesiba":           ["musical bow lesotho", "south africa bow"],
    "Likembe":          ["thumb piano congo", "mbira africa"],
    "Lokole":           ["slit drum congo", "african log drum"],
    "Makhoyana":        ["musical bow swaziland", "south africa bow"],
    "Manman":           ["haiti drum", "caribbean drum"],
    "Maraka":           ["rattle west africa", "african shaker"],
    "Masenqo":          ["one string fiddle ethiopia", "ethiopian fiddle"],
    "Mbira Dzavadzimu": ["mbira zimbabwe spirit", "zimbabwe thumb piano"],
    "Molo":             ["one string lute senegal", "west africa string"],
    "Moropa":           ["drum botswana", "southern africa drum"],
    "Mvet":             ["cameroon harp zither", "central africa string"],
    "Ndzendze":         ["comoros zither", "island zither"],
    "Ngbaka Drum":      ["slit drum central africa", "log drum africa"],
    "Ngombi":           ["harp gabon", "central africa harp"],
    "Ngoni":            ["west africa lute", "mali string instrument"],
    "Nguru":            ["nose flute new zealand", "maori flute"],
    "Nsansi":           ["thumb piano mozambique", "mbira africa"],
    "Nyahbinghi Drum":  ["rastafari drum jamaica", "nyabinghi percussion"],
    "Nyatiti":          ["lyre kenya luo", "east africa lyre"],
    "Odi":              ["musical bow south africa zulu", "south africa bow"],
    "Orutu":            ["one string fiddle kenya", "east africa fiddle"],
    "Pahu":             ["polynesian drum", "pacific island drum"],
    "Pōi":              ["maori poi percussion", "new zealand percussion"],
    "Pūkāea":           ["maori trumpet wood", "new zealand horn"],
    "Rabana":           ["frame drum sri lanka", "south asia frame drum"],
    "Rada Drum":        ["haiti vodou drum", "caribbean sacred drum"],
    "Sabar":            ["senegal drum wolof", "west africa drum"],
    "Sangban":          ["dunun bass drum", "west africa bass drum"],
    "Sanza":            ["thumb piano central africa", "mbira"],
    "Segankure":        ["musical bow botswana", "africa bow"],
    "Seketi":           ["madagascar xylophone", "malagasy xylophone"],
    "Sekhankula":       ["musical bow lesotho", "south africa musical bow"],
    "Setinkane":        ["thumb piano botswana", "southern africa mbira"],
    "Shak-Shak":        ["gourd rattle caribbean", "maraca caribbean"],
    "Sidlodlo":         ["musical bow zulu", "south africa bow"],
    "Siinbiir":         ["somali lute", "east africa string"],
    "Silimba":          ["xylophone zambia", "african xylophone"],
    "Soomaali Flute":   ["somali flute", "east africa flute"],
    "Tama":             ["talking drum senegal", "west africa talking drum"],
    "Thomo":            ["musical bow south africa", "bow south africa"],
    "Timbila":          ["xylophone mozambique chopi", "african xylophone"],
    "Tidinit":          ["mauritania lute", "west africa lute"],
    "Udu":              ["clay pot drum nigeria", "udu drum igbo"],
    "Umakhweyana":      ["musical bow zulu south africa", "zulu bow"],
    "Vaksin":           ["bamboo trumpet haiti", "caribbean trumpet"],
    "Valiha":           ["tube zither madagascar", "malagasy instrument"],
    "Waracaba":         ["guyana flute indigenous", "south america flute"],
    "Washint":          ["bamboo flute ethiopia", "ethiopian flute"],
    "Wata":             ["drum ethiopia", "east africa drum"],
    "Xitende":          ["musical bow mozambique", "africa bow"],
    "Zeze":             ["one string fiddle east africa", "african spike fiddle"],
    # Asian / Middle East
    "Ardin":            ["harp mauritania", "west africa harp"],
    "Bangsi":           ["bamboo flute malaysia", "southeast asia flute"],
    "Besak":            ["drum brunei", "borneo drum"],
    "Birbynė":          ["lithuanian clarinet folk", "baltic reed instrument"],
    "Bocona":           ["bass drum latin america", "latin percussion"],
    "Boben":            ["drum east timor", "southeast asia drum"],
    "Buzuq":            ["long neck lute levant", "arabic lute"],
    "Chonguri":         ["georgian lute string", "caucasus string"],
    "Choor":            ["end blown flute kyrgyz", "central asia flute"],
    "Cimbalom":         ["hammered dulcimer hungary", "cimbalom"],
    "Cobza":            ["romanian lute", "eastern europe lute"],
    "Dabakan":          ["philippine goblet drum", "southeast asia drum"],
    "Daegeum":          ["korean transverse flute", "korean flute"],
    "Daudytė":          ["lithuanian horn", "baltic horn"],
    "Dobulbas":         ["kazakh drum", "central asia drum"],
    "Doli":             ["georgian drum", "caucasus drum"],
    "Dombra":           ["kazakh lute two string", "central asia lute"],
    "Domra":            ["russian plucked lute", "russian folk string"],
    "Dotara":           ["two string lute bangladesh", "south asia lute"],
    "Dungchen":         ["tibetan long horn", "himalayan trumpet"],
    "Durbaan":          ["somali drum", "east africa drum"],
    "Dutaar":           ["afghan two string lute", "central asia lute"],
    "Fujarka":          ["slovak flute", "central europe flute"],
    "Gabusi":           ["comoros lute", "island lute"],
    "Gasba":            ["algerian open flute", "north africa flute"],
    "Ghaita":           ["moroccan oboe", "north africa reed"],
    "Gonje":            ["one string fiddle chad", "west africa fiddle"],
    "Gočevi":           ["bosnian drum", "balkan drum"],
    "Gyjak":            ["uzbek fiddle spike", "central asia spike fiddle"],
    "Hackbrett":        ["swiss hammered dulcimer", "alpine dulcimer"],
    "Haegeum":          ["korean bowed string", "korean fiddle"],
    "Harmonikka":       ["scandinavian accordion", "nordic accordion"],
    "Hnè":              ["myanmar oboe", "southeast asia reed"],
    "Horanewa":         ["sri lanka horn", "south asia horn"],
    "Husle":            ["czech folk fiddle", "slavic fiddle"],
    "Janggu":           ["korean hourglass drum", "korean drum"],
    "Jouhikko":         ["finnish bowed lyre", "nordic bowed lyre"],
    "Joza":             ["iraqi spike fiddle", "arabic fiddle"],
    "Kacapi":           ["sundanese zither", "indonesian zither"],
    "Kamancha":         ["spike fiddle caucasus", "persian fiddle"],
    "Kandyan Drum":     ["sri lanka drum", "south asia drum"],
    "Kankles":          ["lithuanian zither", "baltic zither"],
    "Kannel":           ["estonian zither", "baltic zither"],
    "Kanon":            ["armenian zither plucked", "caucasus zither"],
    "Kanun":            ["arabic zither plucked", "middle east zither"],
    "Kebero":           ["ethiopian drum", "east africa drum"],
    "Kendang":          ["indonesian drum", "javanese drum"],
    "Khaen":            ["mouth organ laos", "southeast asia mouth organ"],
    "Khim":             ["thai hammered dulcimer", "southeast asia dulcimer"],
    "Khui":             ["mongolian flute", "central asia flute"],
    "Koboz":            ["hungarian lute", "eastern europe lute"],
    "Kobyz":            ["kazakh spike fiddle", "central asia fiddle"],
    "Kokle":            ["latvian zither", "baltic zither"],
    "Kompang":          ["malay frame drum", "southeast asia drum"],
    "Komuz":            ["kyrgyz lute", "central asia string"],
    "Krar":             ["eritrea lyre bowl", "east africa lyre"],
    "Kudyapi":          ["philippine lute boat", "southeast asia lute"],
    "Langeleik":        ["norwegian zither drone", "scandinavian zither"],
    "Langspil":         ["icelandic zither", "nordic zither"],
    "Lijerica":         ["croatian fiddle", "balkan bowed string"],
    "Lingm":            ["bhutan flute bamboo", "himalayan flute"],
    "Lira":             ["belarusian hurdy gurdy", "slavic hurdy gurdy"],
    "Lodër":            ["albanian frame drum", "balkan drum"],
    "Lur":              ["bronze age horn nordic", "ancient horn scandinavian"],
    "Lúðr":             ["icelandic horn", "norse horn"],
    "Madal":            ["nepali drum", "himalayan drum"],
    "Mejoranera":       ["panama guitar folk", "central america guitar"],
    "Mezoued":          ["tunisian bagpipe", "north africa bagpipe"],
    "Mijwiz":           ["double reed levant", "arabic reed"],
    "Mizan":            ["moroccan drum", "north africa drum"],
    "Nago":             ["benin drum voodoo", "west africa drum"],
    "Nai":              ["romanian pan flute", "eastern europe pan flute"],
    "Nga":              ["bhutan ceremonial drum", "himalayan drum"],
    "Ngoma":            ["african drum ngoma", "east africa drum"],
    "Nose Flute":       ["nose flute oceania", "polynesian nose flute"],
    "Ooz Komuz":        ["jaw harp kyrgyz", "mouth harp central asia"],
    "Oporo":            ["horn nigeria", "west africa horn"],
    "Organetto":        ["italian button accordion", "italian folk accordion"],
    "Panduri":          ["georgian lute three string", "caucasus lute"],
    "Pastirska Piščal": ["shepherd flute balkans", "balkan wooden flute"],
    "Pat Wain":         ["drum circle myanmar", "southeast asia drum"],
    "Pattala":          ["myanmar xylophone bamboo", "southeast asia xylophone"],
    "Pi Nai":           ["thai oboe quadruple reed", "thai reed instrument"],
    "Pilli":            ["south india flute folk", "carnatic flute"],
    "Pingullo":         ["andean flute peru", "south america flute"],
    "Pito":             ["bolivian flute", "andean flute"],
    "Qanun":            ["arabic zither middle east", "kanun"],
    "Quijongo":         ["musical bow costa rica", "central america bow"],
    "Rababa":           ["one string fiddle arab", "middle east fiddle"],
    "Ranat":            ["thai xylophone", "southeast asia xylophone"],
    "Ranat Ek":         ["thai xylophone treble", "thailand mallet instrument"],
    "Roneat":           ["cambodian xylophone", "southeast asia xylophone"],
    "Sabar":            ["senegalese drum", "west africa drum sabar"],
    "Santur":           ["persian hammered dulcimer", "middle east dulcimer"],
    "Sarangi":          ["indian bowed fiddle", "north india fiddle"],
    "Saung Gauk":       ["myanmar harp arched", "burmese harp"],
    "Serunai":          ["malay oboe", "southeast asia oboe"],
    "Shaman Drum":      ["siberian shaman drum", "central asia ritual drum"],
    "Shambko":          ["somali frame drum", "east africa frame drum"],
    "Shareero":         ["somali string", "east africa string"],
    "Sidlodlo":         ["musical bow zulu", "south africa bow"],
    "Sikor Thom":       ["cambodian large drum", "southeast asia drum"],
    "Skor Thom":        ["cambodian drum large barrel", "khmer drum"],
    "Slit Drum":        ["slit drum log", "wooden slit drum"],
    "So U":             ["thai fiddle bowed", "southeast asia fiddle"],
    "Sodina":           ["madagascar flute", "malagasy flute"],
    "Sopilka":          ["ukrainian flute folk", "slavic flute"],
    "Sralai":           ["cambodian quadruple reed", "khmer oboe"],
    "Stabule":          ["latvian birch flute", "baltic flute"],
    "Sybyzgy":          ["kazakh flute", "central asia flute"],
    "Sáo trúc":         ["vietnamese bamboo flute", "southeast asia flute"],
    "Takuara":          ["guarani flute bamboo", "south america flute"],
    "Talharpa":         ["estonian bowed lyre", "nordic bowed lyre"],
    "Tambora":          ["dominican drum", "caribbean drum"],
    "Tambur":           ["turkish lute folk", "balkan long neck lute"],
    "Tanbur":           ["persian long neck lute", "middle east lute"],
    "Tasa":             ["bahrain kettle drum", "middle east kettle drum"],
    "Tassa Drum":       ["trinidadian tassa drum", "caribbean drum"],
    "Tbal":             ["moroccan drum", "north africa drum"],
    "Tekerőlant":       ["hungarian hurdy gurdy", "eastern europe hurdy gurdy"],
    "Teponaztli":       ["aztec slit drum mexico", "mesoamerican drum"],
    "Thaara":           ["maldives frame drum", "island frame drum"],
    "Thon":             ["thai goblet drum", "southeast asia goblet drum"],
    "Tobă":             ["romanian drum folk", "eastern europe drum"],
    "Tombak":           ["persian goblet drum", "middle east drum"],
    "Torupill":         ["estonian bagpipe", "baltic bagpipe"],
    "Trekkspill":       ["norwegian accordion", "scandinavian accordion"],
    "Trembita":         ["ukrainian alpine horn", "slavic horn"],
    "Tro Khmer":        ["cambodian bowed string", "khmer fiddle"],
    "Trutruka":         ["mapuche trumpet chile", "south america trumpet"],
    "Trống cơm":        ["vietnamese drum cooked rice", "vietnamese drum"],
    "Tsuur":            ["mongolian flute overtone", "central asia flute"],
    "Tuiduk":           ["kyrgyz double flute", "central asia double flute"],
    "Tum-Tum":          ["trinidad steel band drum", "caribbean drum"],
    "Tun":              ["mayan slit drum", "mesoamerican drum"],
    "Tzicolaj":         ["guatemalan flute maya", "mesoamerican flute"],
    "Tzouras":          ["greek lute small", "greek string"],
    "Tárogató":         ["hungarian reed woodwind", "eastern europe clarinet"],
    "Vaksin":           ["haitian bamboo trumpet", "caribbean horn"],
    "Vielle à roue":    ["hurdy gurdy french", "vielle roue"],
    "Vihuela":          ["mexican guitar historic", "latin guitar"],
    "Viola Baixo":      ["portuguese bass guitar", "portuguese string"],
    "Waistdrum":        ["waist drum china", "chinese drum"],
    "Waldhorn":         ["german hunting horn", "natural horn forest"],
    "Wata":             ["ethiopian drum", "east africa drum"],
    "Yatga":            ["mongolian zither", "central asia zither"],
    "Zampogna":         ["italian bagpipe", "southern italy bagpipe"],
    "Zampoña":          ["andean pan flute", "pan flute south america"],
    "Zerbaghali":       ["afghan goblet drum", "central asia goblet drum"],
    "Zhetigen":         ["kazakh zither seven string", "central asia zither"],
    "Zokra":            ["algerian bagpipe", "north africa bagpipe"],
    "Zukra":            ["tunisian bagpipe", "north africa reed"],
    "Zumarë":           ["albanian double reed", "balkan reed"],
    "Zurla":            ["macedonian oboe", "balkan double reed"],
    "Çifteli":          ["albanian two string lute", "balkan lute"],
    "Đàn bầu":          ["vietnamese monochord zither", "vietnam string"],
    "Đàn tranh":        ["vietnamese zither sixteen string", "vietnam zither"],
    "Šargija":          ["bosnian lute folk", "balkan long neck lute"],
    "Żaqq":             ["maltese bagpipe", "mediterranean bagpipe"],
    "Gočevi":           ["bosnian cylindrical drum", "balkan drum"],
    # European
    "Adufe":            ["portuguese square frame drum", "iberian drum"],
    "Cimbál":           ["czech hammered dulcimer", "slavic dulcimer"],
    "Cimpoi":           ["romanian bagpipe", "eastern europe bagpipe"],
    "Citre":            ["swiss zither folk", "alpine zither"],
    "Draaiorgel":       ["dutch barrel organ street", "street organ"],
    "Dragspel":         ["swedish accordion", "scandinavian accordion"],
    "Diatonična Harmonika": ["slovenian diatonic accordion", "balkan accordion"],
    "Dudka":            ["belarusian wooden flute", "slavic flute"],
    "Dudy":             ["czech bagpipe", "slavic bagpipe"],
    "Fiðla":            ["icelandic fiddle", "nordic fiddle"],
    "Frula":            ["serbian shepherd flute", "balkan flute"],
    "Fujara":           ["slovak shepherd flute large", "central europe overtone flute"],
    "Gajde":            ["serbian bagpipe", "balkan bagpipe"],
    "Gajdy":            ["polish bagpipe highlander", "slavic bagpipe"],
    "Hoorntje":         ["dutch horn folk", "netherlands horn"],
    "Jouhikko":         ["finnish bowed lyre kantele", "nordic bowed lyre"],
    "Klompendans":      ["dutch clog dance music", "netherlands folk"],
    "Koboz":            ["hungarian lute short neck", "eastern europe lute"],
    "Lur":              ["scandinavian bronze horn ancient", "nordic ancient horn"],
    "Lyra":             ["greek lyra bowed", "mediterranean fiddle"],
    "Musette":          ["french bagpipe musette", "french baroque bagpipe"],
    "Nyckelharpa":      ["swedish keyed fiddle", "nyckelharpa"],
    "Pastirska Piščal": ["slovenian shepherd flute", "balkan wooden flute"],
    "Rebab":            ["arabic rebab bowed", "middle east spike fiddle"],
    "Sopilka":          ["ukrainian folk flute", "slavic recorder"],
    "Suka Biłgorajska": ["polish fiddle folk regional", "polish string folk"],
    "Trekkspill":       ["norwegian button accordion", "nordic accordion"],
    "Trembita":         ["ukrainian long horn mountain", "carpathian horn"],
    "Vielle à roue":    ["french hurdy gurdy medieval", "hurdy gurdy"],
    # Americas
    "Appalachian Dulcimer": ["mountain dulcimer appalachian", "american folk dulcimer"],
    "Arpa Llanera":     ["colombian venezuelan harp", "plains harp latin"],
    "Bandoneón":        ["tango accordion bandoneon", "argentinian bandoneón"],
    "Bandurria":        ["spanish mandolin bandurria", "iberian plucked string"],
    "Berimbau":         ["capoeira berimbau brazil", "musical bow brazil"],
    "Bombo":            ["andean bass drum", "south america drum"],
    "Bombo Leguero":    ["argentine folkloric drum", "argentina drum"],
    "Cajón":            ["peruvian cajon box drum", "cajon"],
    "Caja":             ["bolivian drum andean", "south america drum"],
    "Caja Drum":        ["andean drum folk", "south america drum"],
    "Candombe Drum":    ["uruguayan candombe drum", "afro uruguayan drum"],
    "Chirimía":         ["colombian double reed", "latin america oboe"],
    "Cuatro":           ["venezuelan cuatro guitar", "latin america string"],
    "Gaita de Foles":   ["portuguese galician bagpipe", "iberian bagpipe"],
    "Guitarrón":        ["mexican bass guitar", "mariachi guitarron"],
    "Guitarrón Chileno":["chilean guitarron folk", "chilean guitar large"],
    "Güira":            ["dominican scraper metal", "caribbean scraper"],
    "Güiro":            ["gourd scraper latin", "cuban guiro"],
    "Jaw Harp":         ["jew harp jaw harp", "mouth harp"],
    "Kultrún":          ["mapuche sacred drum chile", "south america ritual drum"],
    "Mariachi Trumpet": ["mariachi trumpet mexican", "mexican brass"],
    "Marfa":            ["yemeni drum large", "middle east drum"],
    "Pandeiro":         ["brazilian pandeiro tambourine", "brazil frame drum"],
    "Paraguayan Harp":  ["harp paraguay latin america", "south america harp"],
    "Pingullo":         ["andean duct flute", "peru flute"],
    "Pito":             ["andean end flute", "south america flute"],
    "Quena":            ["andean quena notched flute", "peru flute"],
    "Quijongo":         ["musical bow central america", "costa rica bow"],
    "Shak-Shak":        ["gourd rattle caribbean", "caribbean shaker"],
    "Siku (Zampoña)":   ["andean pan flute siku", "pan pipes bolivia"],
    "Takuara":          ["paraguayan bamboo flute", "south america flute"],
    "Tambora":          ["dominican bass drum", "caribbean bass drum"],
    "Tres":             ["cuban tres guitar", "cuban string"],
    "Trutruka":         ["mapuche horn natural", "chile indigenous horn"],
    "Tun":              ["maya wooden drum", "mesoamerican slit drum"],
    "Tzicolaj":         ["maya flute guatemala", "central america flute"],
    "Vaksin":           ["haitian trumpet bamboo", "caribbean wind"],
    "Waracaba":         ["guyana bamboo flute", "south america flute"],
    # Generic fallbacks for common descriptive names
    "Drum":             ["talking drum africa", "african hand drum"],
    "Flute":            ["folk flute wooden", "traditional flute"],
    "Frame Drum":       ["frame drum folk", "hand frame drum"],
    "Frame drum":       ["frame drum folk", "hand frame drum"],
    "Horn":             ["natural horn folk", "animal horn instrument"],
    "Lute":             ["acoustic lute medieval", "plucked lute"],
    "Trumpet":          ["natural trumpet folk", "ceremonial trumpet"],
    "Violin":           ["folk violin string", "violin folk"],
    "Shaker":           ["gourd shaker rattle", "percussion shaker"],
    "Guitar":           ["acoustic guitar folk", "folk guitar"],
    "Ukulele":          ["ukulele hawaii", "ukulele strumming"],
    "Bass Guitar":      ["bass guitar electric", "bass guitar"],
    "Saxophone":        ["saxophone jazz", "alto saxophone"],
    "Melodica":         ["melodica keyboard wind", "melodica playing"],
    "Concertina":       ["concertina english folk", "concertina squeeze"],
    "Castanets":        ["castanets spanish flamenco", "castanets percussion"],
    "Bongos":           ["bongo drums latin", "bongos percussion"],
    "Conga":            ["conga drum afrocuban", "conga latin"],
    "Maracas":          ["maracas shaker latin", "maracas gourd"],
    "Trumpet (Jazz)":   ["jazz trumpet blues", "trumpet jazz"],
    "Brass Band":       ["brass band march", "brass ensemble"],
    "Steel Guitar":     ["lap steel guitar", "hawaiian steel guitar"],
    "Saz (Baglama)":    ["saz baglama turkish", "baglama lute"],
    "Cor de chasse":    ["french hunting horn baroque", "cor de chasse"],
    "Pow Wow Drum":     ["native american pow wow drum", "first nations drum"],
    "Diatonic Accordion": ["diatonic button accordion folk", "folk accordion"],
    "Vallenato Accordion": ["vallenato accordion colombia", "colombian accordion"],
    "Hardanger Fiddle": ["hardingfele norwegian", "hardanger fiddle norway"],
    "Kantele":          ["kantele finnish string", "finnish kantele zither"],
}


def extract_instruments_from_html() -> list[str]:
    html_path = Path(__file__).parent / "index.html"
    if not html_path.exists():
        print("  ❌  index.html not found.")
        sys.exit(1)
    html = html_path.read_text(encoding="utf-8")
    names = re.findall(r'name:\s*"([^"]+)"', html)
    return sorted(set(n.strip() for n in names if n.strip() and not n.startswith("//")))


def api_get(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15, context=SSL_CONTEXT) as resp:
        return json.loads(resp.read())


def search_sound(query: str) -> dict | None:
    q = urllib.parse.quote(query)
    url = (
        f"https://freesound.org/apiv2/search/text/"
        f"?query={q}"
        f"&filter=duration:[1+TO+30]"
        f"&fields=id,name,previews,avg_rating,num_ratings"
        f"&sort=rating_desc"
        f"&page_size=5"
        f"&token={API_KEY}"
    )
    data = api_get(url)
    results = data.get("results", [])
    if not results:
        return None
    for r in results:
        if r.get("num_ratings", 0) >= 3:
            return r
    return results[0]


def search_with_fallbacks(instrument: str) -> tuple[dict | None, str]:
    """Try the instrument name, then any fallback queries. Returns (sound, query_used)."""
    queries = [instrument] + FALLBACKS.get(instrument, [])
    for q in queries:
        sound = search_sound(q)
        time.sleep(DELAY)
        if sound:
            return sound, q
    return None, instrument


def download_preview(sound: dict, dest: Path) -> bool:
    previews = sound.get("previews", {})
    preview_url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")
    if not preview_url:
        return False
    req = urllib.request.Request(preview_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20, context=SSL_CONTEXT) as resp:
        dest.write_bytes(resp.read())
    return True


def download_all():
    if API_KEY == "YOUR_API_KEY_HERE":
        print("\n  ❌  No API key set!")
        print("      1. Get a free key at: https://freesound.org/apiv2/apply")
        print("      2. Open download_audio.py and paste it where it says YOUR_API_KEY_HERE\n")
        sys.exit(1)

    instruments = extract_instruments_from_html()
    total = len(instruments)
    success, skipped, not_found, errors = 0, 0, [], []

    print(f"\n🎵  World Instruments — Freesound Downloader (with fallbacks)")
    print(f"    {total} instruments found in index.html")
    print(f"    Saving to: {AUDIO_DIR.resolve()}\n")

    for i, name in enumerate(instruments, 1):
        safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_').lower()
        dest_path = AUDIO_DIR / f"{safe_name}.mp3"
        prefix    = f"  [{i:03d}/{total}]"

        if dest_path.exists():
            print(f"{prefix} ⏭  {dest_path.name}")
            skipped += 1
            continue

        print(f"{prefix} 🔍  {name}  ...", end=" ", flush=True)

        try:
            sound, used_query = search_with_fallbacks(name)

            if not sound:
                print(f"— not found")
                not_found.append(name)
                continue

            fallback_note = f" [via: '{used_query}']" if used_query != name else ""
            print(f"⬇ '{sound['name'][:30]}'{fallback_note}  ...", end=" ", flush=True)
            download_preview(sound, dest_path)
            size_kb = dest_path.stat().st_size // 1024
            print(f"✅ ({size_kb} KB)")
            success += 1

        except urllib.error.HTTPError as e:
            if e.code == 401:
                print(f"\n\n  ❌  Invalid API key.\n")
                sys.exit(1)
            elif e.code == 429:
                print(f"⏳ rate limited, waiting 20s ...")
                time.sleep(20)
                try:
                    sound, used_query = search_with_fallbacks(name)
                    if sound:
                        download_preview(sound, dest_path)
                        print(f"  ✅ {dest_path.name}")
                        success += 1
                    else:
                        not_found.append(name)
                except Exception as e2:
                    print(f"❌ ({e2})")
                    errors.append((name, str(e2)))
            else:
                print(f"❌ HTTP {e.code}")
                errors.append((name, f"HTTP {e.code}"))

        except Exception as e:
            print(f"❌ ({e})")
            errors.append((name, str(e)))

    print(f"\n{'='*55}")
    print(f"  ✅  Downloaded  : {success}")
    print(f"  ⏭   Skipped    : {skipped}  (already existed)")
    print(f"  ❓  Not found   : {len(not_found)}  (no match even with fallbacks)")
    print(f"  ❌  Errors      : {len(errors)}")

    if not_found:
        print(f"\n  Still not found ({len(not_found)}) — these are very rare instruments:")
        for n in not_found:
            print(f"    • {n}")

    total_files = sum(1 for _ in AUDIO_DIR.glob("*.mp3"))
    print(f"\n  🎵  Total files in audio/ : {total_files}")
    if success > 0 or skipped > 0:
        print(f"  ✔   Restart start.bat to use all local audio.\n")


if __name__ == "__main__":
    download_all()

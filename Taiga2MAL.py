# LXML required for CDATA tags
import lxml.etree as ET

# Used so we can say when the export was made in a user-readable way
import datetime

# Required to actually fetch the APPDATA directory
from os import getenv
from os.path import join

# Change this if you're using portable Taiga or something.
DATA_DIRECTORY = join(getenv('APPDATA'),"Taiga", "data")

def convertStatus(status):
    newStatus = "Watching" # Safe default
    if status == '1':
        newStatus = "Watching"
    elif status == '2':
        newStatus = "Completed"
    elif status == '3':
        newStatus = "On-Hold"
    elif status == '4':
        newStatus = "Dropped"
    elif status == '5':
        newStatus = "Plan to Watch"

    return newStatus

def convertType(anime_type):
    newType = 'TV' # Safe default
    if anime_type == '1':
        newType = 'TV'
    elif anime_type == '2':
        newType = 'OVA'
    elif anime_type == '3':
        newType = "Movie"
    elif anime_type == '4':
        newType = "Special"
    elif anime_type == '5':
        newType = "ONA"
        
    return newType

def buildSubElement(parent, tag, text):
    element = ET.SubElement(parent, tag)
    element.text = text

def makeCDATA(tag):
    if tag == None:
        return ET.CDATA('')
    else:
        return ET.CDATA(str(tag))

def parse_no_meta(path):
    lines = []
    with open(path, 'r', encoding="utf-8") as file:
        ignore = False
        for line in file:
            if "<meta>" in line:
                ignore = True
            elif "</meta>" in line:
                ignore = False
            elif not ignore:
                lines.append(line)
    return ET.fromstring("".join(lines))

# We need to open the anime.xml database file to extract titles and episode counts
db_tree = parse_no_meta(join(DATA_DIRECTORY, "db", "anime.xml"))

# Returns a tuple of title, type, episode_count, which is exactly the format needed later
def lookup_anime(anime_id):
    element = db_tree.find("./anime[id='{0}']".format(anime_id))
    anime_title = element.find("title").text # This is already a CDATA, but we'll just reconstruct
    anime_type = convertType(element.find("type").text)
    
    try:
        episode_count = element.find("episode_count").text
    except AttributeError:
        # Shows of indeterminate length have no episode_count. In this case, default to 0
        episode_count = '0'
    return (anime_title, anime_type, episode_count)

def main():
    # Locate anime.xml, it's just in AppData somewhere
    username = input("What is your MAL username? (required to look in the right directory)\n")
    path= join(DATA_DIRECTORY, "user", username + "@myanimelist", "anime.xml")

    root = parse_no_meta(path)
    
    root2 = ET.Element('myanimelist')
    tree2 = ET.ElementTree(root2)
    
    for anime in root:
        # Extract required information from Taiga
        anime_id = anime.find('id').text
        progress = anime.find('progress').text
        start_date = anime.find('date_start').text
        end_date = anime.find('date_end').text

        # Adjust for Taiga storing scores out of 100
        raw_score = anime.find('score').text
        score = str(int(raw_score)//10) # Requires initial cast of Element to str
        
        status = convertStatus(anime.find('status').text)
        rewatched_times = anime.find('rewatched_times').text
        rewatching = anime.find('rewatching').text
        rewatching_ep = anime.find('rewatching_ep').text

        # Fetch required information from the Taiga anime db
        title, anime_type, episode_count = lookup_anime(anime_id)

        # CDATA types
        tags = anime.find('tags').text
        notes = anime.find('notes').text

        # Dump information into new tree
        newanime = ET.SubElement(root2, 'anime')

        buildSubElement(newanime, 'series_animedb_id', anime_id)

        buildSubElement(newanime, 'series_title', makeCDATA(title))

        buildSubElement(newanime, 'series_type', anime_type)

        buildSubElement(newanime, 'series_episodes', episode_count)
        
        buildSubElement(newanime, 'my_watched_episodes', progress)

        buildSubElement(newanime, 'my_start_date', start_date)
        
        buildSubElement(newanime, 'my_finish_date', end_date)

        buildSubElement(newanime, 'my_score', score)

        buildSubElement(newanime, 'my_status', status)

        buildSubElement(newanime, 'my_comments', makeCDATA(notes))

        buildSubElement(newanime, 'my_times_watched', rewatched_times)

        buildSubElement(newanime, 'my_rewatching', rewatching)
        
        buildSubElement(newanime, 'my_rewatching_ep', rewatching_ep)

        buildSubElement(newanime, 'my_tags', makeCDATA(tags))

        # Fields with default parameters
        # It's unpleasant, but all of these are either not stored by Taiga or not hugely important

        buildSubElement(newanime, 'my_id', "0")
        buildSubElement(newanime, 'my_fansub_group', makeCDATA('0'))
        buildSubElement(newanime, 'my_rated', "")
        buildSubElement(newanime, 'my_dvd', "")
        buildSubElement(newanime, 'my_storage', "")
        buildSubElement(newanime, 'my_rewatch_value', "")
        buildSubElement(newanime, 'my_downloaded_eps', '0')
        buildSubElement(newanime, 'update_on_import', '0')


    # Manually format date so it's in a form Windows can handle
    acceptable_time = datetime.datetime.now().strftime("%d-%m-%Y")
    tree2.write('Taiga2MAL_{0}_{1}.xml'.format(username, acceptable_time), xml_declaration=True, pretty_print=True)

main()

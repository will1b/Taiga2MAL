# LXML required for CDATA tags
import lxml.etree as ET
 
# Used so we can say when the export was made in a user-readable way
import datetime
 
# Required to actually fetch the APPDATA directory
from os import getenv
from os.path import join
 
# Change this if you're using portable Taiga or something.
DATA_DIRECTORY = join(getenv('APPDATA'), "Taiga", "data")
 
 
def convert_status(status):
    new_status = "Watching"  # Safe default
    if status == '1':
        new_status = "Watching"
    elif status == '2':
        new_status = "Completed"
    elif status == '3':
        new_status = "On-Hold"
    elif status == '4':
        new_status = "Dropped"
    elif status == '5':
        new_status = "Plan to Watch"
 
    return new_status
 
 
def convert_type(anime_type):
    new_type = 'TV'  # Safe default
    if anime_type == '1':
        new_type = 'TV'
    elif anime_type == '2':
        new_type = 'OVA'
    elif anime_type == '3':
        new_type = "Movie"
    elif anime_type == '4':
        new_type = "Special"
    elif anime_type == '5':
        new_type = "ONA"
 
    return new_type
 
 
def build_SubElement(parent, tag, text):
    element = ET.SubElement(parent, tag)
    element.text = text
 
 
def make_CDATA(tag):
    if tag is None:
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
 
 
# We need anime.xml for extracting titles and episode counts
db_tree = parse_no_meta(join(DATA_DIRECTORY, "db", "anime.xml"))
 
 
# Returns a tuple of title, type, episode_count
# Exactly the format needed later
def lookup_anime(anime_id):
    element = db_tree.find("./anime[id='{0}']".format(anime_id))
    
    # Title is already a CDATA, but we'll just reconstruct
    anime_title = element.find("title").text
    
    anime_type = convert_type(element.find("type").text)
 
    try:
        episode_count = element.find("episode_count").text
    except AttributeError:
        # Shows of indeterminate length have no episode_count
        # In this case, default to 0
        episode_count = '0'
    return anime_title, anime_type, episode_count
 
 
def main():
    # Locate anime.xml based on the root directory
    username = input("What is your MAL username? "
                     "(required to look in the right directory)\n")
    path = join(DATA_DIRECTORY, "user", username + "@myanimelist", "anime.xml")
 
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
        # Requires initial cast of Element to str
        score = str(int(raw_score) // 10)
 
        status = convert_status(anime.find('status').text)
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
 
        build_SubElement(newanime, 'series_animedb_id', anime_id)
 
        build_SubElement(newanime, 'series_title', make_CDATA(title))
 
        build_SubElement(newanime, 'series_type', anime_type)
 
        build_SubElement(newanime, 'series_episodes', episode_count)
 
        build_SubElement(newanime, 'my_watched_episodes', progress)
 
        build_SubElement(newanime, 'my_start_date', start_date)
 
        build_SubElement(newanime, 'my_finish_date', end_date)
 
        build_SubElement(newanime, 'my_score', score)
 
        build_SubElement(newanime, 'my_status', status)
 
        build_SubElement(newanime, 'my_comments', make_CDATA(notes))
 
        build_SubElement(newanime, 'my_times_watched', rewatched_times)
 
        build_SubElement(newanime, 'my_rewatching', rewatching)
 
        build_SubElement(newanime, 'my_rewatching_ep', rewatching_ep)
 
        build_SubElement(newanime, 'my_tags', make_CDATA(tags))
 
        # Fields with default parameters
        # It's unpleasant, but none of these are stored by Taiga
 
        build_SubElement(newanime, 'my_id', "0")
        build_SubElement(newanime, 'my_fansub_group', make_CDATA('0'))
        build_SubElement(newanime, 'my_rated', "")
        build_SubElement(newanime, 'my_dvd', "")
        build_SubElement(newanime, 'my_storage', "")
        build_SubElement(newanime, 'my_rewatch_value', "")
        build_SubElement(newanime, 'my_downloaded_eps', '0')
        build_SubElement(newanime, 'update_on_import', '0')
 
    # Manually format date so it's in a form Windows can handle
    acceptable_time = datetime.datetime.now().strftime("%d-%m-%Y")
    tree2.write('Taiga2MAL_{0}_{1}.xml'.format(username, acceptable_time),
                xml_declaration=True, pretty_print=True)
 
 
if __name__ == "__main__":
    main()

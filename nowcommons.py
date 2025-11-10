import pywikibot
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import requests
from pywikibot.data.api import Request
import os
import sys
import warnings

"""
Script to check for Commons duplicates in a list of files on Wikipedia

Created by:
- **MGA73** (Wikiverse Contributor)
- **ChatGPT** (AI Assistant by OpenAI)

"Uniting human creativity with AI efficiency. Together, we make the digital world more interconnected."
"""

# Configurable variables
FILENAME = 'file_list.txt'                # File to store the list of filenames
COMMONS_DUPLICATES_FILE = 'commons_duplicates.txt'  # File to store duplicates found on Commons
WIKI_LANGUAGE = 'uk'                      # Wiki language, e.g., 'en', 'br', etc.
WIKI_PROJECT = 'wikipedia'                # Wiki project, e.g., 'wikipedia'
BATCH_SIZE = 500                          # Number of files to process in one batch
REMOVE_PREFIX = 'Файл:'                  # Prefix to remove from file names during list creation

# Asynchronous function to check if the file has a link to Commons on its page
async def has_commons_link(session, page):
    url = page.full_url()
    try:
        async with session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                duplicates_list = soup.find('ul', {'class': 'mw-imagepage-duplicates'})
                if duplicates_list:
                    links = duplicates_list.find_all('a', class_='external')
                    for link in links:
                        href = link.get('href', '')
                        if 'commons.wikimedia.org' in href:
                            return True
    except Exception as e:
        print(f"Error fetching URL {url}: {e}", file=sys.stderr)
    return False

# Asynchronous function to process a batch of files
async def process_batch(lines, start, batch_size, site):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(start, min(start + batch_size, len(lines))):
            file_title = lines[i].strip()  # No prefix added
            page = pywikibot.FilePage(site, file_title)
            tasks.append(has_commons_link(session, page))

        results = await asyncio.gather(*tasks)

        duplicate_count = 0
        with open(COMMONS_DUPLICATES_FILE, 'a', encoding='utf-8') as commons_file:  # Append mode
            for i, exists_on_commons in enumerate(results):
                if exists_on_commons:
                    # Output in the "# [[:File:<Foo.jpg>]]" format
                    commons_file.write(f"# [[:File:{lines[start + i].strip()}]]\n")
                    print(f"# [[:File:{lines[start + i].strip()}]]")
                    duplicate_count += 1

        return duplicate_count

# Function to process the entire file list asynchronously
async def process_file_list(filename, batch_size, site):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_files = len(lines)
    total_duplicates = 0
    
    for start in range(0, total_files, batch_size):
        duplicates_in_batch = await process_batch(lines, start, batch_size, site)
        total_duplicates += duplicates_in_batch
        print(f"Checked {min(start + batch_size, total_files)} files")

    # Append the total duplicates count to the file
    with open(COMMONS_DUPLICATES_FILE, 'a', encoding='utf-8') as commons_file:
        commons_file.write(f"\nTotal duplicates found: {total_duplicates}\n")

    print(f"Total duplicates found: {total_duplicates}")

# Function to fetch files in batches
def fetch_files(site, start='!'):
    all_files = []
    last_file_name = None

    while True:
        request = Request(site, action='query', list='allimages', aifrom=start, ailimit='500')
        result = request.submit()
        files = result['query']['allimages']

        if not files:
            break

        for file_info in files:
            # Remove the prefix during file fetching
            file_title = file_info['title'].replace(REMOVE_PREFIX, '')
            all_files.append(file_title)
            last_file_name = file_title

        print(f"Last file in batch: {last_file_name}")

        if len(files) < 500 or last_file_name == start:
            break
        else:
            start = last_file_name

    return all_files

# Function to compare file list with API-reported total and save the file list
def check_file_list(site):
    all_files = fetch_files(site)

    unique_files = list(set(all_files))  # Remove duplicates

    # Compare with API-reported total
    api_url = f"https://{site.code}.{site.family.domain}/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json"
    api_response = requests.get(api_url)
    total_files_reported = api_response.json()['query']['statistics']['images']
    print(f"Total files reported by API: {total_files_reported}")
    print(f"Total unique files retrieved: {len(unique_files)}")

    if len(unique_files) != total_files_reported:
        print("Warning: There is a discrepancy between the retrieved files and the total reported by the API.")
    else:
        print("Success! The number of retrieved files matches the total reported by the API.")

    # Save the list of unique files to a file
    with open(FILENAME, 'w', encoding='utf-8') as file:
        for file_name in unique_files:
            file.write(f"{file_name}\n")

def main():
    site = pywikibot.Site(WIKI_LANGUAGE, WIKI_PROJECT)

    # Clear the commons_duplicates.txt file at the beginning of the script
    open(COMMONS_DUPLICATES_FILE, 'w').close()

    # Fetch file list and check for discrepancies
    check_file_list(site)

    # After fetching the files, check each for a Commons link using the first script
    try:
        asyncio.run(process_file_list(FILENAME, BATCH_SIZE, site))
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            # Handle the event loop closed error
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(process_file_list(FILENAME, BATCH_SIZE, site))
            finally:
                loop.close()
        else:
            # Log unexpected RuntimeErrors
            print(f"RuntimeError in main(): {e}", file=sys.stderr)
    except Exception as e:
        # Log unexpected exceptions
        print(f"An unexpected error occurred in main(): {e}", file=sys.stderr)

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=RuntimeWarning)  # Ignore specific warnings

    # Redirect stderr to suppress specific unwanted error messages
    class StreamSuppressor:
        def write(self, _):
            pass

        def flush(self):
            pass

    sys.stderr = StreamSuppressor()

    try:
        main()
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            # Suppress specific event loop errors
            pass
        else:
            # Log unexpected RuntimeErrors
            print(f"RuntimeError in __main__: {e}", file=sys.stderr)
    except Exception as e:
        # Log all other unexpected exceptions
        print(f"An unexpected error occurred in __main__: {e}", file=sys.stderr)
    finally:
        try:
            # Ensure any lingering event loop is cleaned up
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.stop()
            loop.close()
        except RuntimeError as e:
            if "There is no current event loop" in str(e):
                # Suppress error about no current event loop
                pass
            elif "Event loop is closed" in str(e):
                # Suppress event loop closed errors during final cleanup
                pass
            else:
                # Log unexpected RuntimeErrors during final cleanup
                print(f"RuntimeError during cleanup: {e}", file=sys.stderr)
        except Exception as e:
            # Log all other unexpected exceptions during final cleanup
            print(f"An unexpected error occurred during cleanup: {e}", file=sys.stderr)

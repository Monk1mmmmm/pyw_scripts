from __future__ import annotations

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ConfigParserBot,
    ExistingPageBot,
    SingleSiteBot,
)
import wikitextparser as wtp
from urllib.parse import urlparse
import tweetedat  # Import the tweetedat module
from datetime import datetime, timezone
import logging
import warnings

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*datetime.datetime.utcnow.*")

# Configure logging
def setup_logging(debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

websites = {}

class BasicBot(
    SingleSiteBot,
    ConfigParserBot,
    ExistingPageBot,
    AutomaticTWSummaryBot,
):

    use_redirects = False
    summary_key = 'basic-changing'

    update_options = {
        'replace': False,
        'summary': "Заміна Cite web, що цитує Твітер, на Cite tweet",
        'text': 'Test',
        'top': False,
    }

    def treat_page(self) -> None:
        text = self.current_page.text
        parsed = wtp.parse(text)
        templates = parsed.templates

        if templates is None:
            logging.warning("No templates found in the page.")
            return

        for template in templates:
            template_str = template.string
            try:
                if "cite web" in template.name.lower():
                    for argument in template.arguments:
                        if "url" in argument.name.strip().lower():
                            url = argument.value.strip()
                            if self.is_tweet_url(url):
                                tweet_info = self.extract_tweet_info(url)
                                if tweet_info:
                                    cite_tweet_template = self.create_cite_tweet_template(tweet_info, template)
                                    text = text.replace(template_str, cite_tweet_template)
            except Exception as e:
                logging.error(f"Error processing template: {e}")
                logging.error(f"Problematic template: {template_str}")
                continue
        self.put_current(text, summary=self.opt.summary)

    def is_tweet_url(self, url):
        # Check if the URL is a tweet URL
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')

        if "twitter.com" in parsed_url.hostname or "x.com" in parsed_url.hostname:
            if len(path_parts) >= 4 and path_parts[2] == 'status':
                return True
            if len(path_parts) >= 5 and path_parts[1] == 'i' and path_parts[2] == 'web' and path_parts[3] == 'status':
                return True
        return False

    def extract_tweet_info(self, url):
        # Extract tweet ID and user from the URL
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')

        logging.debug(f"Parsed URL: {parsed_url}")
        logging.debug(f"Path parts: {path_parts}")

        tweet_id = None
        user = None

        if len(path_parts) >= 4 and path_parts[2] == 'status':
            user = path_parts[1]
            tweet_id = path_parts[3]
        elif len(path_parts) >= 5 and path_parts[1] == 'i' and path_parts[2] == 'web' and path_parts[3] == 'status':
            user = path_parts[4]
            tweet_id = path_parts[5]

        if tweet_id and tweet_id.isdigit():
            # Extract date using tweetedat
            timestamp = tweetedat.find_tweet_timestamp(int(tweet_id))
            logging.debug(f"Timestamp for tweet ID {tweet_id}: {timestamp}")
            if timestamp != -1:
                date = datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
                logging.info(f"Extracted tweet info - User: {user}, Tweet ID: {tweet_id}, Date: {date}")
                return {'id': tweet_id, 'user': user, 'date': date}
        logging.warning(f"Failed to extract tweet info from URL: {url}")
        return None

    def create_cite_tweet_template(self, tweet_info, old_template):
        # Create a cite tweet template string
        tweet_id = tweet_info['id']
        user = tweet_info['user']
        date = tweet_info['date']

        # Preserve other parameters from the old template
        additional_params = []
        original_date = None

        for arg in old_template.arguments:
            if arg.name.strip().lower() == 'date':
                original_date = arg.value.strip()
                if original_date and original_date != date:
                    additional_params.append(f'|date={original_date}')
            elif arg.name.strip().lower() != 'url':
                additional_params.append(f'|{arg.name}={arg.value}')

        if not original_date or original_date == date:
            additional_params.append(f'|date={date}')

        additional_params_str = ' '.join(additional_params)

        logging.info(f"Creating cite tweet template with Tweet ID: {tweet_id}, User: {user}, Date: {date}")
        return f"{{{{cite tweet|user={user}|number={tweet_id}{additional_params_str}}}}}"

def main(*args: str) -> None:
    debug_mode = '-debug' in args
    setup_logging(debug_mode)

    options = {}
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)

    for arg in local_args:
        arg, _, value = arg.partition(':')
        option = arg[1:]
        if option in ('summary', 'text'):
            if not value:
                pywikibot.input('Please enter a value for ' + arg)
            options[option] = value
        else:
            options[option] = True

    gen = gen_factory.getCombinedGenerator(preload=True)
    if not pywikibot.bot.suggest_help(missing_generator=not gen):
        bot = BasicBot(generator=gen, **options)
        bot.run()

if __name__ == '__main__':
    main()

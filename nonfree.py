#!/usr/bin/env python3
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
import time

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

class NonFreeImageRemoverBot(
    SingleSiteBot,
    ConfigParserBot,
    ExistingPageBot,
    AutomaticTWSummaryBot,
):
    """
    A bot to remove non-free images from articles.
    """

    use_redirects = False  # treats non-redirects only
    summary_key = 'nonfree-image-removal'

    update_options = {
        'summary': "Видалення невільних зображень з статті ([[ВП:КДВ]])",  # your own bot summary
    }

    def __init__(self, generator, **kwargs):
        super().__init__(**kwargs)
        self.generator = generator
        self.non_free_category_title = 'Невільні файли'

    def treat_page(self) -> None:
        """Load the given page, remove non-free images, and save it."""
        print(f"Processing page: {self.current_page.title()}")

        text = self.current_page.text
        parsed = wtp.parse(text)

        modified = False
        for image in parsed.wikilinks:
            image_title = image.title.strip()
            #print(f"Processing image: {image_title}")

            if self.is_non_free_image(image_title):
                # Substitute the image link with an empty string
                text = text.replace(str(image), '')
                print(f"Removed non-free image {image_title} from page {self.current_page.title()}")
                modified = True

        # Save changes if the text was modified
        if modified:
            self.put_current(text, summary=self.opt.summary)
            print(f"Saved changes to page: {self.current_page.title()}")
        else:
            print(f"No changes made to page: {self.current_page.title()}")

    def is_non_free_image(self, image_title):
        """Check if the image belongs to the non-free category."""
        if not any(substring in image_title for substring in ["Файл:", "File:", "Зображення:", "файл:", "file:", "зображення:"]):
            #print("not an image")
            return False
        try:
            image_page = pywikibot.FilePage(self.site, image_title)
            categories = {cat.title(with_ns=False) for cat in image_page.categories()}
            return self.non_free_category_title in categories
        except Exception as e:
            print(f'Error: {e}')
            return False

    def put_current(self, text, **kwargs):
        """Save the current page with exponential backoff on failure."""
        retries = 3
        delay = 5  # initial delay in seconds

        for attempt in range(retries):
            try:
                super().put_current(text, **kwargs)
                return
            except Exception as e:
                print(f"Error encountered: {e}. Retrying ({attempt + 1}/{retries})...")
                time.sleep(delay)
                delay *= 2  # exponential backoff

        print(f"Failed to save page {self.current_page.title()} after {retries} attempts.")

def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)

    for arg in local_args:
        arg, _, value = arg.partition(':')
        option = arg[1:]
        if option in ('summary',):
            if not value:
                pywikibot.input('Please enter a value for ' + arg)
            options[option] = value
        else:
            options[option] = True

    gen = gen_factory.getCombinedGenerator(preload=True)

    if not pywikibot.bot.suggest_help(missing_generator=not gen):
        bot = NonFreeImageRemoverBot(generator=gen, **options)
        bot.run()

if __name__ == '__main__':
    main()

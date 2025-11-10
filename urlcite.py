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
import re
import os.path
from urllib.parse import urlparse
from urllib.request import urlopen, Request
#from bs4 import BeautifulSoup

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

websites = {}
"""
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'uk-UA,uk;q=0.8',
       'Connection': 'keep-alive'}
"""
class BasicBot(
    # Refer pywikobot.bot for generic bot classes
    SingleSiteBot,  # A bot only working on one site
    ConfigParserBot,  # A bot which reads options from scripts.ini setting file
    # CurrentPageBot,  # Sets 'current_page'. Process it in treat_page method.
    #                  # Not needed here because we have subclasses
    ExistingPageBot,  # CurrentPageBot which only treats existing pages
    AutomaticTWSummaryBot,  # Automatically defines summary; needs summary_key
):

    use_redirects = False  # treats non-redirects only
    summary_key = 'basic-changing'

    update_options = {
        'replace': False,  # delete old text and write the new text
        'summary': "Виправлення [[:Категорія:Помилки CS1: Сторінки із зовнішнім посиланням у невідповідних параметрах]]",  # your own bot summary
        'text': 'Test',  # add this text from option. 'Test' is default
        'top': False,  # append text on top of the page
    }

    def treat_page(self) -> None:
        text = self.current_page.text
        #print(text)

        parsed = wtp.parse(text)
        templates = parsed.templates
        
        for template in templates:
            template_str = template.string
            try:
                if "cite " in template.name.lower():
                    for argument in template.arguments:
                        #if not "url" in argument.name.strip().lower():
                        if argument.name.strip().lower() in ["веб-сайт", "видавець", "publisher"]:
                            if not "http" in argument.value.lower(): continue
                            try:
                                hostname = urlparse(argument.value).hostname
                            except Exception as e:
                                print(f"Error reading url: {e}")
                                continue
                            
                            """
                            if hostname in websites:
                                argument.value = websites[hostname]
                            else:
                            
                            """
                            print(template_str)
                            """
                            try:
                                req = Request(argument.value, headers=hdr)
                                soup = BeautifulSoup(urlopen(req), features="html.parser")
                                title = soup.title.string
                                print(f'title of the page: {title}; Press y to accept')
                                y = input()
                            except Exception as e:
                                print(f'Failed to load the page: {e}')
                                y = "n"
                            if y.strip().lower() == "y":
                                argument.value = title
                            else:
                            """
                            print(f'Argument {argument.name}')
                            
                            
                            suggested_value = ""
                            if hostname == None:
                                link = wtp.parse(argument.value)
                                if len(link.external_links) != 0:
                                    link = link.external_links[0]
                                    link_text = link.text
                                    if link_text is not None: suggested_value = link_text
                                    elif link.url is not None: suggested_value = urlparse(link.url).hostname
                            elif "." in hostname: suggested_value = hostname
                            
                            print(f'suggested value: {suggested_value}')
                            y = input()
                            if y.strip().lower() == "y":
                                argument.value = suggested_value
                            elif y.strip().lower() == "n":
                                continue
                            else:
                                print("Enter title:")
                                title = input()
                                argument.value = title
                                
                            #if argument.name.strip().lower() in ["website", "вебсайт"]:
                                #websites[hostname] = argument.value
                            #print(websites)
                    
                    text = text.replace(template_str, template.string)
            except Exception as e:
                print(e)
                continue
        self.put_current(text, summary=self.opt.summary)

def main(*args: str) -> None:
    options = {}
    # Process global arguments to determine desired site
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory()

    # Process pagegenerators arguments
    local_args = gen_factory.handle_args(local_args)

    # Parse your own command line arguments
    for arg in local_args:
        arg, _, value = arg.partition(':')
        option = arg[1:]
        if option in ('summary', 'text'):
            if not value:
                pywikibot.input('Please enter a value for ' + arg)
            options[option] = value
        # take the remaining options as booleans.
        # You will get a hint if they aren't pre-defined in your bot class
        else:
            options[option] = True

    # The preloading option is responsible for downloading multiple
    # pages from the wiki simultaneously.
    gen = gen_factory.getCombinedGenerator(preload=True)

    # check if further help is needed
    if not pywikibot.bot.suggest_help(missing_generator=not gen):
        # pass generator and private options to the bot
        bot = BasicBot(generator=gen, **options)
        bot.run()  # guess what it does


if __name__ == '__main__':
    main()
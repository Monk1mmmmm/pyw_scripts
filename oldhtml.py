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
import re
import difflib

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class BasicBot(
    # Refer pywikobot.bot for generic bot classes
    SingleSiteBot,  # A bot only working on one site
    ConfigParserBot,  # A bot which reads options from scripts.ini setting file
    # CurrentPageBot,  # Sets 'current_page'. Process it in treat_page method.
    #                  # Not needed here because we have subclasses
    ExistingPageBot,  # CurrentPageBot which only treats existing pages
    AutomaticTWSummaryBot,  # Automatically defines summary; needs summary_key
):

    """
    An incomplete sample bot.

    :ivar summary_key: Edit summary message key. The message that should be
        used is placed on /i18n subdirectory. The file containing these
        messages should have the same name as the caller script (i.e. basic.py
        in this case). Use summary_key to set a default edit summary message.

    :type summary_key: str
    """

    use_redirects = False  # treats non-redirects only
    summary_key = 'basic-changing'

    update_options = {
        'replace': False,  # delete old text and write the new text
        'summary': "Заміна старих тегів на актуальні аналоги ([[:en:Wikipedia:HTML5]])",  # your own bot summary
        'text': 'Test',  # add this text from option. 'Test' is default
        'top': False,  # append text on top of the page
    }

    def treat_page(self) -> None:
        """Load the given page, do some changes, and save it."""
        text = self.current_page.text
        text_to_add = self.opt.text
        
        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

        # If you find out that you do not want to edit this page, just return.
        # Example: This puts Text on a page.

        # Retrieve your private option
        # Use your own text or use the default 'Test'
        
        print(self.current_page.extract(lines=2))
        parsed = wtp.parse(text)
        
        for template in parsed.templates:
            if template.name.strip().lower() == 'bots' or template.name.strip().lower() == 'nobots': return None # don't do anything if the page is exempt
        
        tags = parsed.get_tags(name="font")
        tags_dict = {}
        for tag in tags:
            if tag.contents == "":
                text = text.replace(tag.string, "")
                continue
            
            style = ""
            
            if "style" in tag.attrs:
                style = tag.get_attr("style")
                
            if "face" in tag.attrs:
                style += "font-family: " + tag.get_attr("face") + ", sans-serif; "
            
            if "color" in tag.attrs:
                style += "color: " + tag.get_attr("color") + "; "
                
            if "size" in tag.attrs:
                match str(tag.get_attr("size")).strip():
                    case "-1":
                        style += "font-size:x-small;"
                    case "+1":
                        style += "font-size:medium;"
                    case "+2":
                        style += "font-size:medium;"
                    case "+3":
                        style += "font-size:large;"
                    case "+4":
                        style += "font-size:x-large;"
                    case "+5":
                        style += "font-size:xx-large;"
                    case "+6":
                        style += "font-size:xxx-large;"
                    case "0":
                        style += "font-size:x-small;"
                    case "1":
                        style += "font-size:x-small;"
                    case "2":
                        style += "font-size:small;"
                    case "3":
                        style += "font-size:medium;"
                    case "4":
                        style += "font-size:large;"
                    case "5":
                        style += "font-size:x-large;"
                    case "6":
                        style += "font-size:xx-large;"
                    case _:
                        style += f"font-size:{str(tag.get_attr("size")).strip()}"
            
            if style == "":
                new_tag = tag.contents
            else:
                new_tag = f'<span style="{style}">{tag.contents}</span>'
            text = text.replace(tag.string, new_tag)
            
        ''' # теги center часто ставились криво, поки приховано щоб не наламати дров
        for tag in parsed.get_tags(name="center"):
            if tag.contents == "":
                new_tag = tag.contents
            elif len(tag.get_tables()) > 0:
                continue
                #for table in tag.get_tables():
                    #pass
            else:
                text = text.replace(tag.string, f'{{{{center|{tag.contents}}}}}')
                '''
            
        for tag in parsed.get_tags(name="tt"):
            text = text.replace(tag.string, f'<span style="font-family:monospace,monospace;">{tag.contents}</span>')
            
        for tag in parsed.get_tags(name="strike"):
            text = text.replace(tag.string, f'<s>{tag.contents}</s>')
         
        # if summary option is None, it takes the default i18n summary from
        # i18n subdirectory with summary_key as summary key.
        self.put_current(text, summary=self.opt.summary)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
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

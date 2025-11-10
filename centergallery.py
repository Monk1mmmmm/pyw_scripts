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
        'summary': "[[:en:Wikipedia:HTML5#Parser_tags|Заміна застарілого центрування <gallery>]]",  # your own bot summary
        'text': 'Test',  # add this text from option. 'Test' is default
        'top': False,  # append text on top of the page
    }

    def treat_page(self) -> None:
        text = self.current_page.text
        parsed = wtp.parse(text)
        templates = parsed.templates
        """
        text = re.sub(
            r"(?i)<\/\s*center\s*>\s*<\/\s*gallery\s*>",
            "</gallery></center>",
            text,
        )
        """
        
        pattern = re.compile(
            r"<center>\s*(<gallery\b[^>]*>.*?<\/gallery>)\s*<\/center>",
            flags=re.DOTALL | re.IGNORECASE,
        )

        def replace_centered_gallery(match):
            gallery_html = match.group(1)
            g_parsed = wtp.parse(gallery_html)
            tag = g_parsed.get_tags("gallery")
            
            if not tag:
                return match.group(0)
                
            tag = tag[0]
            
            # Parse attributes safely using WTP
            if tag.has_attr("caption"):
                if tag.get_attr("caption") == "":
                    tag.del_attr("caption")
            
            if tag.has_attr("class"):
                tag.set_attr("class", tag.get_attr("class") + " center")
            else:
                tag.set_attr("class", "center")

            # Reconstruct the <gallery>...</gallery> tag with updated attributes
            new_gallery = tag.string
            return new_gallery

        new_text = re.sub(pattern, replace_centered_gallery, text)

        # Write changes back to the page text
        if new_text != text:
            self.put_current(new_text, summary=self.opt.summary)
        else:
            print("No changes made.")

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

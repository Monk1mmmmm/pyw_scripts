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
        'summary': "Підставлення [[:wmdoc:codex/latest/design-tokens/color.html|CSS-змінних Codex]]",  # your own bot summary
        'text': 'Test',  # add this text from option. 'Test' is default
        'top': False,  # append text on top of the page
    }

    def treat_page(self) -> None:
        text = self.current_page.text
        parsed = wtp.parse(text)
        #templates = parsed.templates
        
        vars = {"eaecf0": "background-color-neutral",
        "202122": "color-base",
        "404244": "color-base--hover",
        "101418": "color-emphasized",
        "54595d": "color-subtle",
        "72777d": "color-placeholder",
        "a2a9b1": "color-disabled",
        "ffffff": "background-color-base",
        "3366cc": "color-progressive",
        "233566": "color-progressive--active",
        "bf3c2c": "color-destructive",
        "9f3526": "color-destructive--hover",
        "612419": "color-destructive--active",
        "6a60b0": "color-visited",
        "534fa3": "color-visited--hover",
        "353262": "color-visited--active",
        "9f5555": "color-destructive--visited",
        "854848": "color-destructive--visited--hover",
        "512e2e": "color-destructive--visited--active",
        "886425": "color-warning",
        "177860": "color-success",
        "f54739": "color-icon-error",
        "ab7f2a": "color-icon-warning",
        "099979": "color-icon-success",
        "006400": "color-content-added",
        "8b0000": "color-content-removed",
        "eaecf0": "background-color-neutral",
        "f8f9fa": "background-color-neutral-subtle",
        "dadde3": "background-color-interactive--hover",
        "c8ccd1": "background-color-interactive--active",
        "d74032": "background-color-error--hover",        
        "ffe9e5": "background-color-error-subtle",
        "ffdad3": "background-color-error-subtle--hover",
        "ffc8bd": "background-color-error-subtle--active",
        "fdf2d5": "background-color-warning-subtle",
        "dff2eb": "background-color-success-subtle",
        "a3d3ff": "background-color-content-added",
        "ffe49c": "background-color-content-removed",
        "eeeeff": "ukwiki-background-color-paleblue",
        "ffffee": "ukwiki-background-color-paleyellow",
        "ccccff": "ukwiki-background-color-lavanderblue",
        "ffeecc": "ukwiki-background-color-paleorange",
        "f2f2f2": "ukwiki-background-color-midgray",
        }
        
        new_text = text
        for var in vars.keys():
            regex = r"#" + var + r"(?!\))" # no closing bracket on the end
            replacement = f"var(--{vars[var]}, #{var})"
            new_text = re.sub(regex, replacement, new_text, flags=re.IGNORECASE)

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

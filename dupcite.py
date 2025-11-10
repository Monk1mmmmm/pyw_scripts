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

    use_redirects = False  # treats non-redirects only
    summary_key = 'basic-changing'

    update_options = {
        'replace': False,  # delete old text and write the new text
        'summary': 'Виправлено примітку-дублікат зі схожою назвою',  # your own bot summary
        'text': 'Test',  # add this text from option. 'Test' is default
        'top': False,  # append text on top of the 
        'tlang': 'en',
    }

    def treat_page(self) -> None:
        """Load the given page, do some changes, and save it."""
        text = self.current_page.text
        summary = self.opt.summary

        parsed = wtp.parse(text)
        tags = parsed.get_tags(name="ref")
        tags_dict = {} # only ref tags
        empty_tags = {} # all tags; name (str): stringified tag/template (str)

        # Handle <ref> tags
        for tag in tags:
            if "name" in tag.attrs:
                #print("Tag: " + tag.string)
                name = tag.attrs["name"].replace("/", "")
                
                # Only update tags_dict if the tag's contents are not empty or not already in tags_dict
                if name not in tags_dict or len(tags_dict[name].contents) == 0:
                    if len(tag.contents) == 0:
                        empty_tags[name] = str(tag)
                        #print("added to empty")
                    tags_dict[name] = tag
                    #print("added to tags_dict")
                
                # Remove from empty_tags if we now have a tag with contents
                if name in empty_tags and len(tag.contents) != 0:
                    empty_tags.pop(name)
                    #print("removed from empty")

        # Handle {{R}} templates
        r_templates = parsed.templates
        empty_rs = {}
        for template in r_templates:
            if template.name.strip().lower() == 'bots' or template.name.strip().lower() == 'nobots': return None # don't do anything if the page is exempt
            if template.name.strip().lower() == 'r' and template.arguments:
                #print("R: " + template.string)
                name = template.arguments[0].value
                #print(name)
                empty_rs[name] = template
                if name not in tags_dict:
                    empty_tags[name] = str(template)
                    #print("added to empty")

        if len(empty_tags):
            #print(empty_tags)
            #print(tags_dict)
            
            stop_search = False
            for key in empty_tags.keys():
                if stop_search: break
                if key[:-1] in tags_dict:
                    print(f'Found content for {key}: {tags_dict[key[:-1]].string}')
                    print("Press y to accept replacement, n to decline, s to stop search")
                    
                    while True:
                        press_y = input().lower()
                        if press_y == "y":
                            new_ref = f'<ref name="{key[:-1]}"/>'
                            text = text.replace(empty_tags[key], new_ref, 1)
                            break
                        if press_y == "n":
                            break
                        if press_y == "s":
                            stop_search = True
                            break

        self.put_current(text, summary=summary)


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
        if option in ('summary', 'text', 'tlang'):
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

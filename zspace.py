from __future__ import annotations

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ConfigParserBot,
    ExistingPageBot,
    SingleSiteBot,
)
import mwparserfromhell
import re

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

invisible_chars_re = re.compile(
    r'[\u00A0\u200A\u200B-\u200D\u202F\uFEFF\u00AD\uFFFD\u007F\u0009]'
)
def replace_invisible(match):
    char = match.group()
    # Заміна на звичайний пробіл для більшості випадків
    if char in ('\u00A0', '\u202F', '\u200A', '\u0009'):
        return ' '
    elif char in ('\u00AD'):
        return '-'
    # Видалення нуль-ширинних пробілів та інших невидимих символів
    return ''

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
        'summary': "[[Вікіпедія:Завдання_для_ботів#Невидимі символи в шаблонах cite|Виправлення невидимих символів у шаблонах cite]]",  # your own bot summary
        'text': 'Test',  # add this text from option. 'Test' is default
        'top': False,  # append text on top of the page
    }
    def treat_page(self) -> None:
        text = self.current_page.text
        parsed = mwparserfromhell.parse(text)
        changed = False

        # Iterate through <ref> tags in the parsed content
        for ref_tag in parsed.filter_tags(matches=lambda tag: tag.tag.lower() == 'ref'):
            original_value = str(ref_tag.contents)
            new_value = invisible_chars_re.sub(replace_invisible, original_value)

            if new_value != original_value:
                ref_tag.contents = new_value
                changed = True

        if changed:
            text = str(parsed)

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

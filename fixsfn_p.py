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
        'summary': "Виправлення помилки цитувань із sfn (всі ці шаблони повинні мати однаковий параметр сторінки)",  # your own bot summary
        'text': 'Test',  # add this text from option. 'Test' is default
        'top': False,  # append text on top of the page
    }

    def treat_page(self) -> None:
        """Detect conflicting Cyrillic 'с', 's', and 'p' parameters in sfn templates."""
        text = self.current_page.text
        parsed = wtp.parse(text)
        templates = parsed.templates

        # Collect all sfn templates
        sfn_templates = [t for t in templates if t.name.strip().lower() == "sfn"]

        if not sfn_templates:
            print(f"No sfn templates found on {self.current_page.title()}")
            return

        # Map: normalized key (without 'с','s','p') -> list of template objects
        conflict_groups = {}

        for tmpl in sfn_templates:
            params = {p.name.strip(): p.value.strip() for p in tmpl.arguments}

            # Split params into 'special' and normal
            normal_params = {k: v for k, v in params.items() if k not in ('с', 's', 'p')}
            special_params = {k: v for k, v in params.items() if k in ('с', 's', 'p')}

            # Only care about templates that actually use one of these conflicting params
            if not special_params:
                continue

            # Create a normalized key based only on non-conflicting params + positional args
            key_parts = [tmpl.name.strip().lower()]
            key_parts.extend([f"{k}={v}" for k, v in sorted(normal_params.items())])
            key = "|".join(key_parts)

            conflict_groups.setdefault(key, []).append((tmpl, special_params))

        # Now analyze each group
        for key, group in conflict_groups.items():
            if len(group) < 2:
                continue  # no conflict, just one template

            # Collect which conflicting param types are present
            present_params = set()
            for _, specials in group:
                present_params.update(specials.keys())

            if len(present_params) <= 1:
                continue  # no real conflict, all use same key

            print("\n=== Potential conflict detected ===")
            print(f"Page: {self.current_page.title()}")
            print(f"Template group key: {key}")
            print("Found conflicting templates with parameters:", present_params)

            # Show the conflicting templates to user
            for tmpl, specials in group:
                print(f"- {tmpl.string}")

            # Prompt user to choose which parameter to standardize to
            while True:
                choice = input(f"Choose parameter to keep (с, s, p) for this group: ").strip()
                if choice == 'c': choice = 'с'
                if choice in ('с', 's', 'p'):
                    break
                print("Invalid choice. Please enter one of: с, s, p")

            # Apply the change
            for tmpl, specials in group:
                for old_param in specials.keys():
                    if old_param != choice:
                        # Replace the parameter name, keep the value
                        arg_value = specials[old_param]
                        tmpl.string = re.sub(
                            rf"\|\s*{old_param}\s*=\s*{re.escape(arg_value)}",
                            f"|{choice}={arg_value}",
                            tmpl.string
                        )

                print(f"Updated template: {tmpl.string}")

        # Write changes back to the page text
        new_text = parsed.string
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

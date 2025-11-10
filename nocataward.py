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

class AwardTemplateBot(
    SingleSiteBot,
    ConfigParserBot,
    ExistingPageBot,
    AutomaticTWSummaryBot,
):
    """
    A bot to add 'nocat=true' to award templates.
    """

    use_redirects = False  # treats non-redirects only
    summary_key = 'award-template-nocat'

    update_options = {
        'summary': "Додавання 'nocat=true' до шаблонів нагород",  # your own bot summary
    }

    def __init__(self, generator, **kwargs):
        super().__init__(site=True, **kwargs)
        self.generator = generator
        site = pywikibot.Site('uk', 'wikipedia')  # For Ukrainian Wikipedia
        main_category_title = 'Категорія:Шаблони:Нагороди України'
        main_category = pywikibot.Category(site, main_category_title)

        # Get all templates in the main category and its subcategories
        self.award_templates = set(
            page.title(with_ns=False)
            for page in pagegenerators.CategorizedPageGenerator(main_category, namespaces=10)
        )

        # Add templates from subcategories
        self.award_templates.update(
            page.title(with_ns=False)
            for cat in main_category.subcategories(recurse=True)
            for page in pagegenerators.CategorizedPageGenerator(cat, namespaces=10)
        )

        # Dictionary to store resolved redirects
        self.redirect_cache = {}

    def treat_page(self) -> None:
        """Load the given page, add 'nocat=true' to award templates, and save it."""
        print(f"Processing page: {self.current_page.title()}")

        if not self.has_relevant_category(self.current_page):
            print(f"Skipping page {self.current_page.title()}: no relevant categories found")
            return

        text = self.current_page.text
        parsed = wtp.parse(text)

        modified = False
        for template in parsed.templates:
            template_title = template.name.strip()
            print(f"Processing template: {template_title}")
            print(f"Template content: {str(template)}")

            # Skip templates with specific substrings or full names
            if any(substring in template_title.lower() for substring in ["dts", "cite", "youtube", "archive", "flag", "ref", "посилання"]) or template_title.lower() in ["д", "вік", "дтс", "дата", "прапор україни", "!", "якір", "red"]:
                print(f"Skipping template: {template_title} due to substring or full name match")
                continue

            # Check if 'nocat' parameter is already present
            if template.has_arg("nocat"):
                print(f"Template {template_title} already has 'nocat=true'")
                continue

            template_page = pywikibot.Page(self.site, template_title, ns=10)

            # Resolve redirects and cache the result
            if template_page.isRedirectPage():
                if template_title in self.redirect_cache:
                    template_title = self.redirect_cache[template_title]
                    print(f"Redirect cached: {template_title}")
                else:
                    print(f"Template {template_title} is a redirect. Resolving...")
                    try:
                        template_page = template_page.getRedirectTarget()
                        template_title = template_page.title(with_ns=False)
                        self.redirect_cache[template_title] = template_title
                        print(f"Resolved to: {template_title}")
                    except Exception as e:
                        print(f'Error checking redirect: {e}')
                        continue

            if template_title in self.award_templates:
                # Add 'nocat=true' parameter
                template.set_arg('nocat', 'true')
                print(f"Added 'nocat=true' to template {template_title} on page {self.current_page.title()}")
                modified = True
            else:
                print(f"Template {template_title} is not in the award templates list")

        # Convert the modified parsed object back to wikitext
        new_text = str(parsed)

        # Save changes if the text was modified
        if modified and new_text != text:
            self.put_current(new_text, summary=self.opt.summary)
            print(f"Saved changes to page: {self.current_page.title()}")
        else:
            print(f"No changes made to page: {self.current_page.title()}")

    def has_relevant_category(self, page):
        """Check if the page has any relevant categories."""
        keywords = ["нагороджені", "відзначені", "лицарі", "орден"]
        categories = set(cat.title(with_ns=False) for cat in page.categories())
        print(f"Page categories: {categories}")
        for category in categories:
            if any(keyword in category.lower() for keyword in keywords):
                print(f"Relevant category found: {category}")
                return True
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
        bot = AwardTemplateBot(generator=gen, **options)
        bot.run()

if __name__ == '__main__':
    main()

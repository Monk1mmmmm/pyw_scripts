from __future__ import annotations

import csv
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ConfigParserBot,
    ExistingPageBot,
    SingleSiteBot,
)
import wikitextparser as wtp

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

# List of template names and their redirects
TEMPLATE_NAMES = [
    "Обґрунтування добропорядного використання",
    "ОДВ",
    "Обґрунтування сумлінного використання",
    "Non-free use rationale",
    "Non-free image rationale",
    "ОСВ",
    "Non-free fair use rationale",
    "Non-free image data",
    "Non-free use rationale book cover"
]

# Aliases for the "Стаття" parameter
ARTICLE_PARAM_ALIASES = ["Стаття", "стаття", "Article"]

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
        'summary': "Додано параметр 'Стаття' до шаблону 'Обґрунтування добропорядного використання'.",
        'text': 'Test',
        'top': False,
    }

    def __init__(self, **options):
        super().__init__(**options)
        self.image_links = self.load_image_links('image_links.csv')
        #print(self.image_links)

    def load_image_links(self, csv_file):
        image_links = {}
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:
                    article_title, file_name = row
                    if file_name not in image_links:
                        image_links[file_name] = []
                    image_links[file_name].append(article_title)
        return image_links

    def treat_page(self) -> None:
        page = self.current_page
        print(f"Treating page: {page.title()}")
        text = page.text
        parsed = wtp.parse(text)

        templates = parsed.templates

        # Call check_image_usage and handle the result
        backlink_list = self.check_image_usage(page)
        article_title = ""
        if backlink_list:
            if len(backlink_list) == 1:
                article_title = backlink_list[0]
                print(f"Single page found: {article_title}. Updating image page.")
            elif len(backlink_list) > 1:
                
                print(f"Multiple pages link to the image '{page.title()}'. Please select one or skip:")
                for idx, title in enumerate(backlink_list, start=1):
                    print(f"{idx}. {title}")
                print(f"{len(backlink_list) + 1}. Skip this image")

                choice = int(input("Enter the number of your choice: ")) - 1
                if 0 <= choice < len(backlink_list):
                    article_title = backlink_list[choice]
                    print(f"Selected page: {article_title}. Updating image page.")
                elif choice == len(backlink_list):
                    print("Skipping this image.")
                else:
                    print("Invalid choice.")
                
                #return None

        if article_title == "":
            return None

        for template in templates:
            if template.name.strip() in TEMPLATE_NAMES:
                print(f"Found template: {template.name}")
                article_param_found = False
                for alias in ARTICLE_PARAM_ALIASES:
                    if alias in template.arguments:
                        if not template.get_arg(alias).value.strip():
                            print(f"Setting '{alias}' parameter to: {article_title}")
                            og_template = template.string
                            template.set_arg(alias, article_title)
                        article_param_found = True
                        break

                if not article_param_found:
                    print(f"Adding 'Стаття' parameter with value: {article_title}")
                    og_template = template.string
                    template.set_arg("Стаття", article_title)
                
                #print(f'{og_template}\n\n{template.string}')
                
                text = text.replace(og_template, template.string)

        print(f"Saving page: {page.title()}")
        self.current_page.put(text, summary=self.opt.summary)

    def check_image_usage(self, image_page):
        print(f"Checking image usage for: {image_page.title()}")
        # Get pages that link to the image page from the CSV data
        filename = str(image_page.title()[len("Файл:"):])
        if not filename in self.image_links: return []
        backlink_list = self.image_links[filename]

        print(f"Pages linking to '{image_page.title()}':")
        for title in backlink_list:
            print(f"{title}")

        return backlink_list

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

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ConfigParserBot,
    ExistingPageBot,
    SingleSiteBot,
)
import wikitextparser as wtp

# List of template names (without the "Шаблон:" prefix) that use the "Стаття" parameter.
TEMPLATE_NAMES = [
    "обґрунтування добропорядного використання",
    "одв",
    "обґрунтування сумлінного використання",
    "non-free use rationale",
    "non-free image rationale",
    "осв",
    "non-free fair use rationale",
    "non-free image data",
    "non-free use rationale book cover"
]

# Aliases for the "Стаття" parameter.
ARTICLE_PARAM_ALIASES = ["Стаття", "стаття", "Article"]

class UpdateRedirectBot(
    SingleSiteBot,
    ConfigParserBot,
    ExistingPageBot,
    AutomaticTWSummaryBot,
):
    
    summary_key = 'basic-changing'
    use_redirects = False
    
    update_options = {
        'replace': False,
        'summary': "Виправлення [[:Категорія:Невільні файли, у яких назва статті є перенаправленням]]",
        'text': 'Test',
        'top': False,
    }
    
    def treat_page(self) -> None:
        page = self.current_page
        print(f"Processing page: {page.title()}")
        text = page.text
        parsed = wtp.parse(text)
        templates = parsed.templates

        for template in templates:
            #print(template.name)
            if template.name.strip().lower() in TEMPLATE_NAMES:
                #print("Processing template")
                #print(template)
                for alias in ARTICLE_PARAM_ALIASES:
                    if alias in [argument.name.strip() for argument in template.arguments]:
                        current_val = template.get_arg(alias).value.strip()
                        #print(f"current_val: {current_val}")
                        if current_val:
                            # Create a page object from the parameter value.
                            article_page = pywikibot.Page(self.site, current_val)
                            #print(f"article_page.exists(): {article_page.exists()}, article_page.isRedirectPage(): {article_page.isRedirectPage()}")
                            if article_page.exists() and article_page.isRedirectPage():
                                old_template = template.string
                                target_page = article_page.getRedirectTarget()
                                new_title = target_page.title()+"\n"
                                #print(f"Updating parameter '{alias}': {current_val} -> {new_title}")
                                template.set_arg(alias, new_title)
                                print(f"Saving page: {page.title()}")
                                text = text.replace(old_template, template.string)
                                self.current_page.put(text, summary=self.opt.summary)
                                return None
                        break  # Stop after handling one of the aliases
        
        print(f"No changes needed for {page.title()}.")

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
        bot = UpdateRedirectBot(generator=gen, **options)
        bot.run()  # guess what it does


if __name__ == "__main__":
    main()

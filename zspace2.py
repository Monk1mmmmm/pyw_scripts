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

docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

# 1) stray-newline: newline not followed by |, {, or }
newline_re = re.compile(r'\n(?!\s*[\|{}<\n])')

# 2) spaces: various non-breaking or thin spaces + tabs
space_re = re.compile(r'[\u00A0\u202F\u200A\u0009]')

# 3) soft hyphen → literal hyphen
hyphen_re = re.compile(r'\u00AD')

# 4) other invisibles to just drop
drop_re = re.compile(r'[\u200B-\u200D\uFEFF\uFFFD\u007F]')

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
        'summary': "[[Вікіпедія:Завдання_для_ботів#Невидимі символи в шаблонах cite|Виправлення невидимих символів у шаблонах cite]]",
        'text': 'Test',
        'top': False,
    }

    def clean_ref_contents(self, text: str) -> str:
        # 1: turn any stray newline into a space
        text = newline_re.sub(' ', text)
        # 2: normalize various spaces/tabs → regular space
        text = space_re.sub(' ', text)
        # 3: soft hyphens → hyphen-minus
        text = hyphen_re.sub('-', text)
        # 4: drop zero-width & other invisibles
        text = drop_re.sub('', text)
        return text

    def treat_page(self) -> None:
        page_text = self.current_page.text
        parsed = mwparserfromhell.parse(page_text)
        changed = False

        for ref in parsed.filter_tags(matches=lambda t: t.tag.lower() == 'ref'):
            orig = str(ref.contents)
            cleaned = self.clean_ref_contents(orig)
            if cleaned != orig:
                ref.contents = cleaned
                changed = True

        if changed:
            self.put_current(str(parsed), summary=self.opt.summary)

def main(*args: str) -> None:
    options = {}
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)

    for arg in local_args:
        arg, _, val = arg.partition(':')
        opt = arg[1:]
        if opt in ('summary', 'text'):
            if not val:
                pywikibot.input(f'Please enter a value for {arg}')
            options[opt] = val
        else:
            options[opt] = True

    gen = gen_factory.getCombinedGenerator(preload=True)
    if not pywikibot.bot.suggest_help(missing_generator=not gen):
        BasicBot(generator=gen, **options).run()

if __name__ == '__main__':
    main()

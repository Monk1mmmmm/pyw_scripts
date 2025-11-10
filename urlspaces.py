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

# Help text for -help output
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

class RemoveLinkSpacesBot(
    SingleSiteBot,           # work on a single site only
    ConfigParserBot,         # read options from scripts.ini
    ExistingPageBot,         # skip non‐existing pages
    AutomaticTWSummaryBot,   # auto‐generate edit summaries
):

    summary_key = 'remove-link-spaces'
    update_options = {
        'summary': '[[Обговорення_користувача:MonAx#http:_//_->_http://|Прибирання зайвих пробілів у посиланнях]]',
        'always': False,
    }

    @staticmethod
    def _clean_url_preserve_ws(val_str: str) -> str:
        # Preserve leading/trailing whitespace, clean spaces inside core URL
        if len(val_str.strip()) == 0: return val_str
        leading = val_str[:len(val_str) - len(val_str.lstrip())]
        trailing = val_str[len(val_str.rstrip()):]
        core = val_str.strip()
        cleaned_core = core.replace(' ', '')
        return f"{leading}{cleaned_core}{trailing}"

    def treat_page(self) -> None:
        text = self.current_page.text
        parsed = mwparserfromhell.parse(text)
        changed = False

        # 1) Clean external link URLs across the page
        for ext in parsed.filter_external_links():
            url_str = str(ext.url)
            new_url = url_str.replace(' ', '')
            if new_url != url_str:
                ext.url = new_url
                changed = True

        # 2) Clean URL params in templates (preserve surrounding whitespace)
        for tmpl in parsed.filter_templates():
            for param in tmpl.params:
                name = str(param.name).strip().lower()
                if name in ['url', 'посилання', "ссылка", "archiveurl"]:
                    val_str = str(param.value)
                    new_val = self._clean_url_preserve_ws(val_str)
                    if new_val != val_str:
                        param.value = new_val
                        changed = True

        # 3) Within <ref> tags, also clean external link URLs and template URL params
        for tag in parsed.filter_tags(matches=lambda t: t.tag.lower() == 'ref'):
            inner = str(tag.contents)
            parsed_ref = mwparserfromhell.parse(inner)
            sub_changed = False

            # clean external links
            for ext in parsed_ref.filter_external_links():
                url_str = str(ext.url)
                new_url = url_str.replace(' ', '')
                if new_url != url_str:
                    ext.url = new_url
                    sub_changed = True

            # clean templates URL params inside refs
            for tmpl in parsed_ref.filter_templates():
                for param in tmpl.params:
                    if str(param.name).strip().lower() == 'url':
                        val_str = str(param.value)
                        new_val = self._clean_url_preserve_ws(val_str)
                        if new_val != val_str:
                            param.value = new_val
                            sub_changed = True

            if sub_changed:
                tag.contents = parsed_ref
                changed = True

        if changed or self.opt.always:
            self.put_current(str(parsed), summary=self.opt.summary)


def main(*args: str) -> None:
    options: dict[str, bool] = {}
    local_args = pywikibot.handle_args(args)

    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)

    for arg in local_args:
        if arg.startswith('-always'):
            options['always'] = True

    gen = gen_factory.getCombinedGenerator(preload=True)
    if not pywikibot.bot.suggest_help(missing_generator=not gen):
        bot = RemoveLinkSpacesBot(generator=gen, **options)
        bot.run()


if __name__ == '__main__':
    main()

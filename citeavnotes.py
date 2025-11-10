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

docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

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
        'summary': "[[ВП:ЗДБ#Заміна параметрів в Cite AV media notes|Заміна параметрів у шаблоні Cite AV media notes]]",
        'text': 'Test',
        'top': False,
    }

    def treat_page(self) -> None:
        text = self.current_page.text
        parsed = wtp.parse(text)
        changed = False

        for tpl in parsed.templates:
            tpl_name = tpl.name.strip().replace('_', ' ').lower()
            
            if tpl_name in ['cite av media notes', 'cite album-notes']:
                # Collect old values
                albumlink = tpl.get_arg('albumlink')
                artist = tpl.get_arg('artist')
                bandname = tpl.get_arg('bandname')
                notestitle = tpl.get_arg('notestitle')
                publisherid = tpl.get_arg('publisherid')
                
                old_tpl = tpl.string

                # Merge artist and bandname for 'others'
                others_vals = []
                if artist:
                    others_vals.append(artist.value)
                    tpl.del_arg('artist')
                if bandname:
                    others_vals.append(bandname.value)
                    tpl.del_arg('bandname')
                if others_vals:
                    tpl.set_arg('others', '; '.join(others_vals))

                if albumlink:
                    tpl.set_arg('title-link', albumlink.value)
                    tpl.del_arg('albumlink')
                if notestitle:
                    tpl.set_arg('chapter', notestitle.value)
                    tpl.del_arg('notestitle')
                if publisherid:
                    tpl.set_arg('id', publisherid.value)
                    tpl.del_arg('publisherid')

                changed = True
                #print(old_tpl)
                #print(tpl.string)
                #input()
                text.replace(old_tpl, tpl.string)
                

        if changed:
            self.put_current(str(parsed), summary=self.opt.summary)
        else:
            pywikibot.output(f"No changes needed on page: {self.current_page.title()}")

def main(*args: str) -> None:
    options = {}
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)
    for arg in local_args:
        arg, _, value = arg.partition(':')
        opt = arg[1:]
        if opt in ('summary', 'text'):
            if not value:
                options[opt] = pywikibot.input('Please enter a value for ' + arg)
            else:
                options[opt] = value
        else:
            options[opt] = True
    gen = gen_factory.getCombinedGenerator(preload=True)
    if not pywikibot.bot.suggest_help(missing_generator=not gen):
        BasicBot(generator=gen, **options).run()

if __name__ == '__main__':
    main()

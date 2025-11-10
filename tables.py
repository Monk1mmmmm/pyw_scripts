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
import re
from bs4 import BeautifulSoup
import mwparserfromhell as mwparser

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

def format_attrs(element):
    attributes = ""
    for attr in element.attrs:
        if attr == 'class':
            # Join class names with spaces
            attributes += f' {attr}="{" ".join(element.attrs[attr])}"'
        else:
            attributes += f' {attr}="{str(element.attrs[attr])}"'
    return attributes


def fix_html_table(html_table: str) -> str:
    """
    Attempt to auto-fix malformed HTML tables using BeautifulSoup (lxml parser).
    Returns a cleaned, valid HTML <table> string.
    """
    # Parse with a forgiving parser that auto-closes tags
    soup = BeautifulSoup(html_table, 'lxml')

    table = soup.find('table')
    if not table:
        return html_table  # No valid table found, return original

    # Normalize formatting (strip extra whitespace)
    fixed_html = str(table)
    fixed_html = re.sub(r'\s+', ' ', fixed_html)
    fixed_html = fixed_html.replace("> <", "><").strip()

    return fixed_html
    
def html_to_wikitext_table(html_table: str, inside_template: bool = False) -> str:
    """
    Convert an HTML table to MediaWiki table syntax, preserving attributes.
    If inside_template=True, use template-safe syntax ({{!}}, {{!-}}, etc.).
    """
    soup = BeautifulSoup(html_table, 'lxml')
    table = soup.find('table')
    if not table:
        return ""

    attributes = format_attrs(table)
    wikitext_table = f"\n{{|{attributes}"

    # Caption
    caption = table.find('caption')
    if caption:
        caption_attrs = format_attrs(caption)
        caption_content = ''.join(str(i) for i in caption.contents).strip()
        if caption_attrs:
            wikitext_table += f"\n|+ {caption_attrs} | {caption_content}"
        else:
            wikitext_table += f"\n|+ {caption_content}"

    # Rows
    for row in table.find_all('tr'):
        row_attrs = format_attrs(row)
        wikitext_table += f"\n|- {row_attrs}"

        for cell in row.find_all(['td', 'th']):
            cell_attrs = format_attrs(cell)
            marker = "!" if cell.name == 'th' else "|"
            cell_content = ''.join(str(i) for i in cell.contents).strip()

            if cell_attrs:
                wikitext_table += f"\n{marker}{cell_attrs} | {cell_content}"
            else:
                wikitext_table += f"\n{marker} {cell_content}"

    wikitext_table += "\n|}"

    if inside_template:
        # Escape wiki table syntax for use inside templates
        replacements = {
            "{|": "{{(!}}",
            "|}": "{{!)}}",
            "|-": "{{!-}}",
        }
        for k, v in replacements.items():
            wikitext_table = wikitext_table.replace(k, v)
        # Replace line-leading ! and | (only where they indicate cell markers)
        wikitext_table = re.sub(r'(?m)^\!', '{{!!}}', wikitext_table)
        wikitext_table = re.sub(r'(?m)^\|', '{{!}}', wikitext_table)
        wikitext_table = re.sub(r' \| ', ' {{!}} ', wikitext_table)

    return wikitext_table
    
class TableConverterBot(
    SingleSiteBot,
    ConfigParserBot,
    ExistingPageBot,
    AutomaticTWSummaryBot,
):

    use_redirects = False  # treats non-redirects only
    summary_key = 'table-conversion'

    update_options = {
        'summary': 'Заміна HTML-таблиць на MediaWiki-таблиці',  # your own bot summary
    }

    def treat_page(self) -> None:
        """Load the given page, fix and convert HTML tables to MediaWiki syntax."""
        text = self.current_page.text
        summary = self.opt.summary
        wikicode = mwparser.parse(text)

        table_pattern = re.compile(r'(<table.*?>.*?</table>)', re.DOTALL | re.IGNORECASE)

        for template in wikicode.filter_templates(recursive=True):
            for param in template.params:
                param_text = str(param.value)
                html_tables = table_pattern.findall(param_text)
                for html_table in html_tables:
                    fixed = fix_html_table(html_table)
                    wikitext_table = html_to_wikitext_table(fixed, inside_template=True)
                    param_text = param_text.replace(html_table, wikitext_table)
                param.value = mwparser.wikicode.Wikicode(param_text)

        plain_text = str(wikicode)
        html_tables = table_pattern.findall(plain_text)
        for html_table in html_tables:
            fixed = fix_html_table(html_table)
            wikitext_table = html_to_wikitext_table(fixed, inside_template=False)
            plain_text = plain_text.replace(html_table, wikitext_table)

        self.put_current(plain_text, summary=summary)
    
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
        bot = TableConverterBot(generator=gen, **options)
        bot.run()

if __name__ == '__main__':
    main()

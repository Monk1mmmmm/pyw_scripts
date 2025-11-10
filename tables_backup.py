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
    
def html_to_wikitext_table(html_table):
    """
    Convert an HTML table to MediaWiki table syntax, preserving attributes.
    """
    soup = BeautifulSoup(html_table, 'html.parser')
    table = soup.find('table')

    if not table:
        return ""
        
    attributes = format_attrs(table)
    
    wikitext_table = f"\n{{|{attributes}"

    # Process table caption if present
    caption = table.find('caption')
    if caption:
        caption_attributes = format_attrs(caption)
        if len(caption_attributes) != 0:
            wikitext_table += f"\n|+ {caption_attributes} | {''.join([str(i) for i in caption.contents])}\n"
        else:
            wikitext_table += f"\n|+ {''.join([str(i) for i in caption.contents])}\n"

    rows = table.find_all('tr')
    for i, row in enumerate(rows):
        attributes = format_attrs(row)
        cells = row.find_all(['td', 'th'])
        wikitext_table += f"\n|- {attributes}"
        for cell in cells:
            attributes = format_attrs(cell)
                
            is_header = "|" # not a header
            if cell.name == 'th' """or (i == 0 and cell.name == 'td')""":
                is_header = "!" # is a header
            
            if attributes:
                wikitext_table += f"\n{is_header}{attributes} | {''.join([str(i) for i in cell.contents])}"
            else:
                wikitext_table += f"\n{is_header} {''.join([str(i) for i in cell.contents])}"

    wikitext_table += "\n|}"
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
        'summary': 'Convert HTML tables to MediaWiki syntax tables',  # your own bot summary
    }

    def treat_page(self) -> None:
        """Load the given page, convert HTML tables to MediaWiki syntax, and save it."""
        text = self.current_page.text
        summary = self.opt.summary

        # Use regular expressions to find HTML table tags with lazy matching
        table_pattern = re.compile(r'(<table.*?>.*?</table>)', re.DOTALL)
        html_tables = table_pattern.findall(text)

        # Replace each HTML table with its MediaWiki equivalent
        for html_table in html_tables:
            fixed_table = fix_html_table(html_table)
            
            wikitext_table = html_to_wikitext_table(fixed_table)
            # Replace the table while preserving surrounding content
            text = text.replace(html_table, wikitext_table)

        self.put_current(text, summary=summary)

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

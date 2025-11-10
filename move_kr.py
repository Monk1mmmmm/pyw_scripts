from __future__ import annotations

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import ConfigParserBot
import wikitextparser as wtp
import re
from typing import Optional

# --- невеликі утиліти ---------------------------------------------------

def extract_param_value(text: str, key: str) -> Optional[str]:
    """
    Шукає в тексті рядок виду:
      |key = value
    (ігнорує пробіли навколо =, case-insensitive).
    Повертає value (без кінцевого пробілу) або None.
    """
    pattern = rf'^\s*\|\s*{re.escape(key)}\s*=\s*(.+)\s*$'
    m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    val = m.group(1).strip()
    # Якщо значення містить наступний рядок параметра, вирізати лише поточний рядок
    # (ми вже взяли до кінця рядка, тому це зайве; лишаємо на випадок інших форматів)
    return val

def unwrap_image(value: str) -> str:
    """
    Просте витягання імені файлу з форм:
      [[Файл:Name.png|...]] -> Name.png
      [[File:Name.svg]] -> Name.svg
      File:Name.png -> Name.png
      commons:File:Name -> Name
      або якщо вже plain 'Name.svg' -> Name.svg
    """
    if not value:
        return value
    v = value.strip()
    # [[...:Name|...]] або [[...:Name]]
    m = re.search(r'\[\[\s*(?:[Ff]ile|[Фф]айл|[Cc]ommons:File|[Cc]ommons:Файл)?\s*[:/]?\s*([^|\]]+)', v)
    if m:
        return m.group(1).strip()
    # префіксний варіант File:Name
    m2 = re.match(r'^(?:[Ff]ile|[Фф]айл|[Cc]ommons:File|[Cc]ommons:Файл)\s*:\s*(.+)$', v)
    if m2:
        return m2.group(1).strip()
    # якщо є pipe, беремо ліву частину
    if '|' in v:
        return v.split('|', 1)[0].strip()
    # знайти щось з розширенням
    m3 = re.search(r'([^/\\\|\n]+\.(?:svg|png|jpg|jpeg|gif|tif|tiff|webp))', v, flags=re.IGNORECASE)
    if m3:
        return m3.group(1).strip()
    return v

def format_lua_value(key: str, raw: Optional[str]) -> str:
    """
    Форматує значення для lua:
      - числа (ціле або з десятковою частиною) повертаються як число (без лапок),
        допускаються коми як десятковий розділювач (перетворюються в '.')
      - для ключів image/image1 витягуємо ім'я файлу і повертаємо 'Name.ext'
      - інші рядки — в одинарних лапках, апострофи екраніруємо
    """
    if raw is None:
        return "''"
    v = raw.strip()
    # видалити зовнішні лапки
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1].strip()
    # числа: допускаємо 51.6 або 51,6
    v_num = v.replace(',', '.')
    if re.fullmatch(r'-?\d+(\.\d+)?', v_num):
        return v_num
    # images
    if key.lower().startswith('image'):
        fname = unwrap_image(v)
        fname = fname.replace("'", "\\'")
        return f"'{fname}'"
    # рядкове значення
    s = v.replace("'", "\\'")
    return f"'{s}'"

# --- main (обробка сторінок і створення модулів) -----------------------

def main(*args: str) -> None:
    options = {}
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)

    # парсимо прості опції (summary, replace)
    for arg in local_args:
        arg, _, value = arg.partition(':')
        opt = arg[1:]
        if opt in ('summary',):
            options[opt] = value if value else pywikibot.input('Please enter a value for ' + arg)
        else:
            if opt:
                options[opt] = True

    gen = gen_factory.getCombinedGenerator(preload=True)
    if not gen:
        pywikibot.bot.suggest_help(missing_generator=True)
        return

    site = pywikibot.Site()
    replace_flag = bool(options.get('replace', False))
    summary = options.get('summary', 'Створення модуля Location map/data з шаблону')

    for page in gen:
        try:
            pywikibot.output(f'Обробка сторінки: {page.title()}')
            text = page.text or ''
            if not text.strip():
                pywikibot.output('  Порожня сторінка — пропускаю.')
                continue

            # Визначити суфікс для модуля: прибираємо "Шаблон:" і "Карта розташування"
            title = page.title()
            base = title
            if base.startswith('Шаблон:'):
                base = base[len('Шаблон:'):]
            suffix = base
            if base.startswith('Карта розташування'):
                suffix = base[len('Карта розташування'):].strip()
            suffix = suffix.strip()
            if not suffix:
                pywikibot.output('  Не вдалося визначити суфікс назви — пропускаю.')
                continue

            module_title = f'Модуль:Location map/data/{suffix}'
            module_page = pywikibot.Page(site, module_title)

            # Витягнути потрібні параметри (name, top, bottom, left, right, image, image1)
            # Використовуємо простий пошук по рядках |key = value
            keys = ['name', 'top', 'bottom', 'left', 'right', 'image', 'image1']
            found = {}
            # Для надійності спробуємо знайти у всьому тексті (не лише в тілі шаблона)
            for k in keys:
                v = extract_param_value(text, k)
                if v is None:
                    # спробуємо також варіант з можливими CAPS/пробілами навколо (ще один пошук)
                    # (extract_param_value вже ігнорує регістр, тому цього кроку зазвичай не треба)
                    v = extract_param_value(text, k)
                if v is not None:
                    found[k] = v

            # Якщо хоча б одне поле знайдено — продовжимо; інакше пропускаємо
            if not found:
                pywikibot.output('  Не знайдено жодного з полів (name/top/bottom/left/right/image/image1) — пропускаю.')
                continue

            # Побудова lua-тексту у бажаному порядку
            lines = []
            for k in keys:
                if k in found:
                    lua_val = format_lua_value(k, found[k])
                    lines.append(f'\t{k} = {lua_val},')

            lua_text = "-- Автоматично згенеровано скриптом\nreturn {\n" + "\n".join(lines) + "\n}\n"

            # Якщо модуль вже існує і не дозволено replace — пропускаємо
            if module_page.exists() and not replace_flag:
                pywikibot.output(f'  Модуль уже існує: {module_title} — пропускаю (використайте -replace щоб перезаписати).')
                continue

            # Записуємо модуль
            module_page.text = lua_text
            module_page.save(summary=summary)
            pywikibot.output(f'  Створено/оновлено модуль: {module_title}')

        except Exception as e:
            pywikibot.output(f'  Помилка при обробці {page.title()}: {e}')

if __name__ == '__main__':
    main()

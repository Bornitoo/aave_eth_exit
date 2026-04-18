from . import en, ru

_MODULES = {"en": en.STRINGS, "ru": ru.STRINGS}


def t(lang: str, key: str, **kwargs) -> str:
    strings = _MODULES.get(lang, ru.STRINGS)
    template = strings.get(key) or en.STRINGS.get(key, key)
    return template.format(**kwargs) if kwargs else template

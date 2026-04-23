"""Page types, defaults, and shared constants."""

PAGE_TYPES = ["summary", "entity", "concept", "comparison", "synthesis", "archive"]

DEFAULT_DATA_DIR = "D:\\AI\\llm-wiki"

SUPPORTED_LANGUAGES = ["zh", "en"]
DEFAULT_LANGUAGE = "zh"

DEFAULT_CONFIG = {
    "data_dir": DEFAULT_DATA_DIR,
    "active_domain": None,
    "active_provider": None,
    "language": DEFAULT_LANGUAGE,
    "providers": {},
}

LOGO = r"""
 ╦ ╦╦╦╔═╦
 ║║║║╠╩╗║
 ╚╩╝╩╩ ╩╩
"""

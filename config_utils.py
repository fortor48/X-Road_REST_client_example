import configparser

# функція для зчитування конфігураційного файлу
def load_config(file_path: str, defaults: dict = None) -> configparser.ConfigParser:
    config = configparser.ConfigParser(defaults=defaults, interpolation=None)
    config.read(file_path)
    return config


# функція для отримання значення параметрів з конфіг файлу за їх ім'ям
def get_config_param(config: configparser.ConfigParser, section: str, param: str) -> str:
    if config.has_option(section, param):
        return config.get(section, param)
    else:
        raise ValueError(f"Missing required config parameter: [{section}] {param}")

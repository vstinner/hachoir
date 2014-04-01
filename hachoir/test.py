from hachoir.core import config
from locale import setlocale, LC_ALL


def setup_tests():
    config.use_i18n = False  # Don't use i18n
    config.quiet = True      # Don't display warnings
    setlocale(LC_ALL, "C")

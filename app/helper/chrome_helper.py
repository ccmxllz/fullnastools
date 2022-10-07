import json
import os.path
import tempfile
from functools import reduce

from app.utils import SystemUtils
from app.utils.commons import singleton
import undetected_chromedriver as uc

from app.utils.types import OsType


@singleton
class ChromeHelper(object):

    _executable_path = "/usr/lib/chromium/chromedriver" if SystemUtils.is_docker() else None
    _chrome = None
    _display = None
    _ua = None

    def __init__(self, ua=None):
        self._ua = ua
        self.init_config()

    def init_config(self):
        if SystemUtils.get_system() == OsType.LINUX \
                and self._executable_path \
                and not os.path.exists(self._executable_path):
            return
        options = uc.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        if self._ua:
            options.add_argument("user-agent=%s" % self._ua)
        if not os.environ.get("NASTOOL_CHROME"):
            options.add_argument('--headless')
        prefs = {
            "profile.default_content_setting_values.images": 2,
            "useAutomationExtension": False,
            "excludeSwitches": ["enable-automation"]
        }
        options.add_experimental_option("prefs", prefs)
        self._chrome = ChromeWithPrefs(options=options, driver_executable_path=self._executable_path)
        self._chrome.set_page_load_timeout(30)

    def get_browser(self):
        return self._chrome

    def __del__(self):
        if self._chrome:
            self._chrome.quit()
        if self._display:
            self._display.stop()


class ChromeWithPrefs(uc.Chrome):
    def __init__(self, *args, options=None, **kwargs):
        if options:
            self._handle_prefs(options)
        super().__init__(*args, options=options, **kwargs)
        # remove the user_data_dir when quitting
        self.keep_user_data_dir = False

    @staticmethod
    def _handle_prefs(options):
        if prefs := options.experimental_options.get("prefs"):
            # turn a (dotted key, value) into a proper nested dict
            def undot_key(key, value):
                if "." in key:
                    key, rest = key.split(".", 1)
                    value = undot_key(rest, value)
                return {key: value}

            # undot prefs dict keys
            undot_prefs = reduce(
                lambda d1, d2: {**d1, **d2},  # merge dicts
                (undot_key(key, value) for key, value in prefs.items()),
            )

            # create an user_data_dir and add its path to the options
            user_data_dir = os.path.normpath(tempfile.mkdtemp())
            options.add_argument(f"--user-data-dir={user_data_dir}")

            # create the preferences json file in its default directory
            default_dir = os.path.join(user_data_dir, "Default")
            os.mkdir(default_dir)

            prefs_file = os.path.join(default_dir, "Preferences")
            with open(prefs_file, encoding="latin1", mode="w") as f:
                json.dump(undot_prefs, f)

            # pylint: disable=protected-access
            # remove the experimental_options to avoid an error
            del options._experimental_options["prefs"]

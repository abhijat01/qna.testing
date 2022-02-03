import configparser as cfg
import os
from utils import debug


class Configuration:
    _instance = None
    _app_name = "taiho.buddy"
    _config_dir = ".toi"

    @staticmethod
    def set_config_options(app_name: str, config_dir: str):
        """
        Must be invoked before an instance is created
        :param app_name:
        :param config_dir:
        :return:
        """
        if not (Configuration._instance is None):
            raise Exception("Instance already created. Cannot change options now")
        if not (app_name is None):
            Configuration._app_name = app_name
        if not (config_dir is None):
            Configuration._config_dir = config_dir
        return Configuration.get_instance()

    @staticmethod
    def get_instance():
        if Configuration._instance is None:
            Configuration._instance = Configuration(Configuration._app_name, Configuration._config_dir)
        return Configuration._instance

    def __init__(self, app_name: str , config_dir: str ):
        self.config_dir = config_dir
        self.config_dir = os.path.join(os.path.expanduser("~"), self.config_dir)
        self.app_name = app_name
        self.config_file = os.path.join(self.config_dir, self.app_name + ".ini")
        if not os.path.isfile(self.config_file):
            raise Exception("No configuration file [{}]".format(self.config_file))
        env_key = self.app_name + ".env"
        self.env_name = os.environ.get(self.app_name + ".env")
        if not self.env_name:
            debug("Environment variable [{}] not set. Using \"dev\"".format(env_key))
            self.env_name = "dev"
        self._read_config_file()

    def _read_config_file(self):
        self.config_all = cfg.ConfigParser()
        self.config_all.read(self.config_file)
        self.env_config = self.config_all[self.env_name]
        try:
            self.common_config = self.config_all['common']
        except KeyError as ke:
            debug("Could not locate common section in {}".format(self.config_file))
            self.common_config = {}

    def __getitem__(self, item):
        if item in self.env_config:
            return self.env_config[item]
        if item in self.common_config:
            return self.common_config[item]
        return None

    def __getattr__(self, item):
        return self.__getitem__(item)

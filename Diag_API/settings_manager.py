#***********************************************************************
# MODULE: settings_manager
# SCOPE:  Manages API settings, environment variables, and script execution
# REV: 1.0
#
# Created by: Codreanu Dan
# Imported from: https://github.com/CodreanuDan/Linked_API_RequestsApp/blob/master/settings_manager.py

#***********************************************************************

#***********************************************************************
# IMPORTS:
import os
import subprocess
from dotenv import load_dotenv
import tomllib


#***********************************************************************
# CONTENT: SettingsManager
# INFO: Manages API settings, environment variables, and script execution  
class SettingsManager:
    """ Manages API settings, environment variables, and script execution """

    _config = None  
    _env_loaded = False  

    @classmethod
    def _load_toml_file(cls):
        """ Loads configuration from settings.toml file """
        file_location = os.path.join(os.path.dirname(__file__), "api/settings.toml")
        if cls._config is None:  
            try:
                with open(file_location, "rb") as cfg_file:
                    cls._config = tomllib.load(cfg_file)
            except Exception as e:
                print(f"[❌] Error loading {file_location}: {e}")
                cls._config = {}
        return cls._config

    @classmethod
    def _load_env_data(cls):
        """ Loads environment variables from .env file """
        if not cls._env_loaded:
            env_file = os.path.join(os.path.dirname(__file__), "api/env_data.env")
            load_dotenv(env_file)
            cls._env_loaded = True  

    # @classmethod
    # def get_api_url(cls, identifier: str) -> str:
    #     """ Retrieves API URL from settings.toml """
    #     cls._load_toml_file()
    #     return cls._config.get("api", {}).get(identifier, {}).get("primary", "")

    @classmethod
    def get_api_key(cls, identifier: str) -> str:
        """ Retrieves API Key from environment variables """
        cls._load_env_data()
        return os.getenv(identifier, "")

    @classmethod
    def run_bat(cls):
        """ Runs .bat file to initialize environment variables """
        bat_file = os.path.join(os.path.dirname(__file__), "api/init.bat")
        try:
            subprocess.run(["cmd.exe", "/c", bat_file], check=True)
            # subprocess.run(bat_file, check=True, shell=True)
            print("[✔️] .bat file executed successfully.")
        except Exception as e:
            print(f"[❌] Error running {bat_file}: {e}")
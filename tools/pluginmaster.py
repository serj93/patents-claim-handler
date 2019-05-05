import pprint as pp
import os.path
from importlib.machinery import SourceFileLoader

# Прослойка доступа к плагину (семантическая проверка)
class PluginMaster(object):

    # Internal State
    __isModuleInit = False
    __module_path = "./plugins/semchecker.py"
    __module_name = "plugins.semchecker"
    schecker = None

    # Singleton
    __instance = None

    def __new__(cls):
        if PluginMaster.__instance is None:
            PluginMaster.__instance = object.__new__(cls)

        return PluginMaster.__instance

    def __init__(self):
        self.__initModule()

    def canUseModule(self):
        return self.__isModuleInit

    def __initModule(self):
        if not os.path.isfile(self.__module_path):
            return
        try:
            module = SourceFileLoader(self.__module_name, self.__module_path).load_module()
            self.schecker = module.SemanticChecker()
            self.__isModuleInit = self.schecker.canUseChecker()
        except:
            pass

        return

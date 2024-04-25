from typing import Any, Union

from app.utils.commons import singleton


@singleton
class SystemConfigOper():
    # 配置对象
    __SYSTEMCONF: dict = {}

    def __init__(self):
        super().__init__()

    def set(self, key: Union[str], value: Any):
        self.__SYSTEMCONF[key] = value

    def get(self, key: Union[str] = None) -> Any:
        return self.__SYSTEMCONF.get(key)

    def all(self):
        return self.__SYSTEMCONF or {}

    def delete(self, key: Union[str]):
        self.__SYSTEMCONF.pop(key, None)
        return True

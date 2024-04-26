import json
from typing import Any, Union

from app.db import MainDb, DbPersist
from app.db.models import SystemConfigModel
from app.utils.object import ObjectUtils
from app.utils.singleton import Singleton


class SystemConfigOper(metaclass=Singleton):
    # 配置对象
    __SYSTEMCONF: dict = {}
    _db = MainDb()

    def __init__(self):
        super().__init__()
        for item in self.list():
            if ObjectUtils.is_obj(item.value):
                self.__SYSTEMCONF[item.key] = json.loads(item.value)
            else:
                self.__SYSTEMCONF[item.key] = item.value



    def set(self, key: Union[str], value: Any):
        self.__SYSTEMCONF[key] = value

        # 写入数据库
        if ObjectUtils.is_obj(value):
            value = json.dumps(value)
        elif value is None:
            value = ''
        conf = self.get_by_key(key)
        if conf:
            if value:
                self.update(conf.id, value)
            else:
                self.delete(conf.id)
        else:
            self.save(key, value)

    def get(self, key: Union[str] = None) -> Any:
        return self.__SYSTEMCONF.get(key)

    def all(self):
        return self.__SYSTEMCONF or {}

    def delete(self, key: Union[str]):
        self.__SYSTEMCONF.pop(key, None)
        conf = self.get_by_key(key)
        if conf:
            conf.delete(conf.id)
        return True

    def get_by_key(self, key) -> SystemConfigModel:
        if not key:
            return self._db.query(SystemConfigModel).filter(SystemConfigModel.key == key).first()
        else:
            return None

    def list(self):
        return self._db.query(SystemConfigModel).all()

    @DbPersist(_db)
    def save(self, key, value):
        self._db.insert(
            SystemConfigModel(
                key=key,
                value=value,
            ))

    @DbPersist(_db)
    def delete(self, id):
        query = 'DELETE FROM system_config WHERE id=%s'
        self._db.execute(query, (id))

    @DbPersist(_db)
    def update(self, id, value):
        query = 'update system_config set value=%s where id=%s'
        self._db.execute(query, (value, id))
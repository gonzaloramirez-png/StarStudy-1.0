"""
Backend Django para MariaDB 10.4 (XAMPP).

Django 5.x exige MariaDB 10.5+, pero XAMPP incluye MariaDB 10.4.32.
Este backend reutiliza el backend mysql de Django y solo relaja el
chequeo de versión mínima: 10.4 en lugar de 10.5.
"""

from django.db.backends.mysql.base import DatabaseWrapper as MySQLDatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures as MySQLDatabaseFeatures

from django.utils.functional import cached_property


class MariaDB104DatabaseFeatures(MySQLDatabaseFeatures):
    @cached_property
    def minimum_database_version(self):
        if self.connection.mysql_is_mariadb:
            return (10, 4)
        return super().minimum_database_version

    @cached_property
    def can_return_columns_from_insert(self):
        # INSERT ... RETURNING está disponible solo desde MariaDB 10.5.
        return (
            self.connection.mysql_is_mariadb
            and self.connection.mysql_version >= (10, 5)
        )


class DatabaseWrapper(MySQLDatabaseWrapper):
    features_class = MariaDB104DatabaseFeatures

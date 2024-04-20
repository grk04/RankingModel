"""
Class to implement all coverage db related code
"""
import sys
try:
    import cx_Oracle
except ImportError as ie:
    raise Exception(f"Failed to import cx_Oracle {ie}")

import logging
import Logutil

logger = None


class CoverageDB:

    def __init__(self):
        """
        connect to coverage db
        """
        self.logger = Logutil.get_logger()
        self.__conn = None
        self.__user = '<user>'
        self.__pwd = '<pwd>'
        self.__tns = '<dsn_str>'

        self.__connect()

    def __connect(self):
        """
        connect to coverage db if not already done
        :return:
        """

        try:
            self.__conn = cx_Oracle.connect(
                user=self.__user,
                password=self.__pwd,
                dsn=self.__tns,
                threaded=True)
        except cx_Oracle.Error as dbe:
            raise Exception("Failed to connect to db")

    def commit(self):
        """

        :return:
        """

        if self.__conn is None:
            return

        try:
            self.__conn.commit()
        except cx_Oracle.Error as dbe:
            raise Exception("Failed to commit to db " + str(dbe))

    def rollback(self):
        """

        :return:
        """

        if self.__conn is None:
            return

        try:
            self.__conn.rollback()
        except cx_Oracle.Error as dbe:
            raise Exception ("Failed to rollback to db " + str(dbe))

    def is_alive(self):
        """
        check if connection is still alive
        :return:
        """
        if self.__conn is None:
            return False
        else:
            self.__conn.ping()

    def get_cursor(self):
        """
        get new  cursor object
        :return:
        """
        return self.__conn.cursor()

    def close(self):

        if self.__conn is None:
            return

        try:
            self.__conn.close()
        except cx_Oracle.Error as dbe:
            raise Exception("Failed to close db conn " + str(dbe))


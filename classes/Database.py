import json
import os
import sqlite3
from typing import Any
import cv2
import psycopg2
from psycopg2.extensions import AsIs
import tqdm
from .Card import OCRCard
from .Card import Card


class Database:
    config: dict
    db_connection: Any

    def __init__(self, config):
        self.config = config
        self.db_connection = psycopg2.connect(
            database="mysticocr",
            user="Chad",
            password="Dashwood",
            host="localhost",
            port="5432",
        )
        ocr_cursor = self.db_connection.cursor()

        if config["overwrite_db"] == True and config["command"] == "scan":
            ocr_cursor.execute("DROP TABLE IF EXISTS match_results;")
            ocr_cursor.execute("DROP TABLE IF EXISTS failed_results;")
            ocr_cursor.execute("DROP TABLE IF EXISTS cards;")
        ocr_cursor.execute(
            "CREATE TABLE IF NOT EXISTS cards ( "
            + "id SERIAL PRIMARY KEY,"
            + "file_name            TEXT     ,"
            + "location             TEXT     ,"
            + "type TEXT,"
            + "date TEXT, "
            + "showcase             TEXT     ,"
            + "ocr_result           TEXT     ,"
            + "image                bytea   ,"
            + "borderless TEXT "
            + ");"
        )

        if config["overwrite_db"] == True and config["command"] == "match":
            ocr_cursor.execute("DROP TABLE IF EXISTS failed_results;")
            ocr_cursor.execute("DROP TABLE IF EXISTS match_results;")
        ocr_cursor.execute(
            "CREATE TABLE IF NOT EXISTS match_results (  "
            + "ocr_id               INTEGER NOT NULL PRIMARY KEY  , "
            + "ratio                INTEGER     , "
            + "name                 TEXT     , "
            + "ocr_result TEXT,"
            + "price TEXT,"
            + "foil TEXT,"
            "FOREIGN KEY ( ocr_id ) REFERENCES cards( id ) " + ");"
        )

        ocr_cursor.execute(
            "CREATE TABLE IF NOT EXISTS failed_results (  "
            + "ocr_id               INTEGER NOT NULL PRIMARY KEY  , "
            + "ratio                INTEGER     , "
            + "name                 TEXT     , "
            + "ocr_result TEXT,"
            + "price TEXT,"
            + "foil TEXT,"
            "FOREIGN KEY ( ocr_id ) REFERENCES cards( id ) " + ");"
        )
        self.db_connection.commit()
        return None

    def insert_ocr_result(self, file_path, ocr_result, original_imagecv):
        split_path = os.path.dirname(file_path).split("\\")
        location = split_path[2]
        type = split_path[3]
        date = split_path[4]
        self.db_connection.cursor().execute(
            "INSERT INTO cards(file_name,location,type,date,showcase,ocr_result,image) VALUES (%s,%s,%s,%s,%s,%s,%s);",
            (
                file_path,
                location,
                type,
                date,
                self.config["scan"]["card"]["showcase"],
                f"{ocr_result}",
                sqlite3.Binary(cv2.imencode(".jpg", original_imagecv)[1].tobytes()),
            ),
        )
        self.db_connection.commit()

    def import_card_for_set(self, cursor, card):
        card = Card(card)
        insert_sql = """
        INSERT INTO card_set (card_id,name,prices,foil) VALUES (%s,%s,%s,%s)
        """
        values = (card.id, card.name, f"{card.prices}", card.foil)

        cursor.execute(insert_sql, values)
        self.db_connection.commit()

    def import_card_set(self, card_db):
        cursor = self.db_connection.cursor()
        ##TODO ADD OVERWRITE CONFIG SUPPORT
        cursor.execute("DROP TABLE IF EXISTS card_set;")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS card_set (
            id SERIAL PRIMARY KEY,
            card_id TEXT,
            name TEXT,
            prices TEXT,
            foil BOOLEAn);"""
        )
        self.db_connection.commit()
        cursor.execute("""SELECT * FROM card_set WHERE id=1;""")
        print("IMPORTING CARD SET JSON INTO DATABASE")
        if len(cursor.fetchall()) == 0:
            with tqdm.tqdm(card_db) as pbar:
                for card in card_db:
                    self.import_card_for_set(cursor, card)
                    pbar.update()

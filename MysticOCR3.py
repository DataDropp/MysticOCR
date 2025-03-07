from datetime import date
import glob
import json
import os
import yaml
from classes.Matcher import Matcher
from classes.Database import Database
from classes.OCR import MysticOCR
from MysticPricer import MysticPricer


def main():
    print("Loading configuration...")
    config = yaml.load(open("mysticocr.yml", "r"), Loader=yaml.FullLoader)["mystic"]
    print("Loading images...")
    files = glob.glob(
        os.path.join(config["scan"]["image_dir"], "**/*.jpg"), recursive=True
    )
    print("Loading Database...")
    db: Database = Database(config)

    if config.get("command") == "scan":
        ocr: MysticOCR = load_ocr(config)
        for file in files:
            print(f"Scanning file: " + file)
            ocr_result, imagecv = ocr.scan_file(file)
            if config["scan"]["show_image"]:
                ocr.show_image(imagecv, ocr_result)
            db.insert_ocr_result(file, ocr_result)
    elif config.get("command") == "match":
        card_set = json.loads(
            open(f"{date.today()}.json", "r", encoding="utf-8").read()
        )
        matcher: Matcher = Matcher(config, card_set, db)
        matcher.search_multi()
    elif config.get("command") == "scan_new":
        db_file_names = [file[0] for file in db.fetch_card_file_names()]
        ocr: MysticOCR = load_ocr(config)
        for file in files:
            if file not in db_file_names:
                print(f"Scanning file: " + file)
                ocr_result, imagecv = ocr.scan_file(file)
                if config["scan"]["show_image"]:
                    ocr.show_image(imagecv, ocr_result)
                db.insert_ocr_result(file, ocr_result)
    elif config.get("command") == "price":
        mysticPricer = MysticPricer(db)
        mysticPricer.download_db()
        mysticPricer.update_all_prices()


def load_ocr(config):
    print("Loading ocr...")
    return MysticOCR(config)

    # matcher.create_workers()


if __name__ == "__main__":
    main()

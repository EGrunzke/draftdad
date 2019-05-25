import time
import json
from lsv import load_from_disk

SLEEP_INTERVAL = 1.0


def readlines_then_tail(fin):
    "Iterate through lines and then tail for further lines."
    while True:
        line = fin.readline()
        if line:
            yield line
        else:
            tail(fin)


def tail(fin):
    "Listen for new lines added to file."
    while True:
        where = fin.tell()
        line = fin.readline()
        if not line:
            time.sleep(SLEEP_INTERVAL)
            fin.seek(where)
        else:
            yield line


def main():
    loc = 'C:\\Users\\Grunzkes\\AppData\\LocalLow\\Wizards Of The Coast\\MTGA\\output_log.txt'
    lw = LogWatch()
    with open(loc, 'r') as fin:
        for line in readlines_then_tail(fin):
            lw.scan_line(line.strip())


class LogWatch:
    buffer = []
    phase = 0

    def __init__(self):
        ratings = load_from_disk()
        self.ratings_by_id = {
            r['id']: r for r in ratings
        }

    def scan_line(self, line: str):
        if self.phase == 0 and (line.startswith('<== Draft.DraftStatus') or line.startswith('<== Draft.MakePick')):
            self.phase = 1
            return

        if self.phase > 0:
            self.buffer.append(line)
            if line.startswith('{'):
                self.phase = 2
            if self.phase == 2 and line.startswith('}'):
                self.phase = 0
                obj = json.loads(' '.join(self.buffer))
                self.buffer = []
                print()
                print()
                print(obj)
                print()
                pack = obj['draftPack']
                if pack:
                    self.print_ratings(pack)
                elif obj['draftStatus'] == "Draft.Complete":
                    status = obj['draftStatus']
                    deck = obj['pickedCards']
                    print('Draft Done! I should really print a summary')

    def print_ratings(self, pack):
        ratings = []
        for id_ in pack:
            card = self.ratings_by_id.get(id_, {"card": id_, "rating": "???", "reason": "UNKNOWN ID", "rarity": "?"})
            ratings.append(card)
        sorted_ = sorted(ratings, key=lambda rt: rt["rating"], reverse=True)
        for r in sorted_:
            card = r["card"]
            rating = r["rating"]
            reason = r["reason"]
            rarity = r["rarity"]
            print(f"{rarity:.1} {rating:<10} {card:<30} {reason}")

if __name__ == '__main__':
    main()

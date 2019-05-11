import json
from html.parser import HTMLParser
from mtga.set_data import all_mtga_cards
from lsv import load_from_disk

rating_by_name = {}


def create_ratings_from_json():
    with open("res/RNA.json", encoding="utf-8") as f:
        rna = json.load(f)
        for r in rna:
            name = r["card"]
            rating_by_name[name] = r


def rate_pack(pack):
    ratings = []
    for id_ in pack:
        card = all_mtga_cards.find_one(id_)
        r = rating_by_name.get(
            card.pretty_name,
            {"card": card.pretty_name, "rating": "???", "reason": "CARD NOT FOUND"},
        )
        r['rarity'] = card.rarity[:1]
        ratings.append(r)
    sorted_ = sorted(ratings, key=lambda rt: rt["rating"], reverse=True)
    for r in sorted_:
        card = r["card"]
        rating = r["rating"]
        reason = r["reason"]
        rarity = r["rarity"]
        print(f"{rarity} {rating:<10} {card:<30} {reason}")


class RnaParser(HTMLParser):
    ready_for_rating = False
    ready_for_name = False
    ready_for_reason = False
    context = {}
    cards = []

    def handle_starttag(self, tag, attrs):
        d = {entry[0]: entry[1] for entry in attrs}

        if tag == "div" and d.get("class") == "hidden_card":
            self.ready_for_rating = True

        if tag == "a":
            self.ready_for_name = True

        if tag == "p" and d.get("class") == "hidden_description":
            self.ready_for_reason = True

    def handle_data(self, data):
        if self.ready_for_rating:
            self.context["rating"] = data.strip()
            self.ready_for_rating = False

        if self.ready_for_name:
            self.context["card"] = data.strip()
            self.ready_for_name = False

        if self.ready_for_reason:
            self.context["reason"] = data.strip()
            self.ready_for_reason = False

    def handle_endtag(self, tag):
        if tag == "div" and len(self.context) == 3:
            self.cards.append(self.context)
            self.context = {}


def create_ratings_from_html():
    parser = RnaParser()
    with open("res/RNA.html", encoding="utf-8") as f:
        parser.feed(f.read())

    for r in parser.cards:
        name = r["card"]
        rating_by_name[name] = r


if __name__ == '__main__':
    create_ratings_from_html()
    main()

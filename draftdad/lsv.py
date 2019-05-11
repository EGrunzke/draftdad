import json
import requests
from html.parser import HTMLParser
from mtga.set_data.war import WarOfTheSpark
from mtga import all_mtga_cards
from fuzzywuzzy import process


def get_ratings_from_url(url):
    headers = {
        "accept-encoding": "gzip, deflate, br",
        "accept": "text/html",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36",
    }
    resp = requests.get(url, headers=headers)
    lp = LsvParser()
    print(len(lp.cards))
    lp.feed(resp.text)
    return lp.cards


def aggregate(urls):
    all_ratings = []
    by_name = {}
    for url in urls:
        color = get_ratings_from_url(url)
        for rating in color:
            all_ratings.append(rating)
            name = rating["card"]
            by_name[name] = rating
    infuse(all_ratings)
    write_to_disk(all_ratings)


def infuse(ratings):
    card_by_name = {
        card.pretty_name: card
        for card in all_mtga_cards.cards
    }
    mtg_names = [card.pretty_name for card in all_mtga_cards.cards]
    infused = []

    for r in ratings:
        name = r['card']
        try:
            card = card_by_name[name]
        except KeyError:
            best_match, ratio = process.extractOne(name, mtg_names)
            card = card_by_name[best_match]
            print(
                f"No card found for '{name}'. Best match is '{best_match}' with ratio '{ratio}'"
            )
        r["id"] = str(card.mtga_id)
        r["rarity"] = card.rarity
        infused.append(r)
    return infused


def write_to_disk(ratings):
    with open("res/WAR.json", "w") as outfile:
        json.dump(ratings, outfile, ensure_ascii=False, indent=2)


def load_from_disk():
    with open("res/WAR.json") as infile:
        return json.load(infile)


class LsvParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ready_for_rating = False
        self.ready_for_name = False
        self.ready_for_reason = False
        self.context = {}
        self.cards = []

    def handle_starttag(self, tag, attrs):
        d = {entry[0]: entry[1] for entry in attrs}

        if tag == "h3" or tag == "h4":
            self.ready_for_rating = True

        if tag == "h1" or tag == "h2":
            self.ready_for_name = True
            if len(self.context) == 3:
                self.cards.append(self.context)
            self.context = {}

        if tag == "p" and len(self.context) >= 2:
            self.ready_for_reason = True

    def handle_data(self, data):
        clean = data.strip()
        clean = clean.replace("\u00a0", " ")
        clean = clean.replace("\u2014", " -- ")
        clean = clean.replace("\u2019", "'")
        clean = clean.replace("\u201c", '"')
        clean = clean.replace("\u201d", '"')
        clean = clean.replace("\u2026", "...")
        if self.ready_for_rating and clean.startswith("Limited: "):
            self.context["rating"] = clean[9:]
            self.ready_for_rating = False

        if self.ready_for_name:
            self.context["card"] = clean
            self.ready_for_name = False

        if self.ready_for_reason:
            reason = self.context.get("reason", "")
            reason = reason + " " + clean
            self.context["reason"] = reason.strip()

    def handle_endtag(self, tag):
        if tag == "p" and self.ready_for_reason:
            self.ready_for_reason = False


if __name__ == "__main__":
    urls = [
        "https://www.channelfireball.com/articles/war-of-the-spark-limited-set-review-gold-artifacts-and-lands/",
        "https://www.channelfireball.com/articles/luis-scott-vargas/war-of-the-spark-limited-set-review-white/",
        "https://www.channelfireball.com/articles/war-of-the-spark-limited-set-review-blue/",
        "https://www.channelfireball.com/articles/war-of-the-spark-limited-set-review-green/",
        "https://www.channelfireball.com/articles/war-of-the-spark-limited-set-review-red/",
        "https://www.channelfireball.com/articles/war-of-the-spark-limited-set-review-black/",
        "https://www.channelfireball.com/articles/luis-scott-vargas/war-of-the-spark-limited-set-review-white/",
    ]
    # aggregate(urls)
    ratings = load_from_disk()
    infused = infuse(ratings)
    write_to_disk(ratings)
    # print(ratings)

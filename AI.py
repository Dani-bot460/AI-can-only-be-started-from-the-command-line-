#!/usr/bin/env python3
"""
JARVIS — Windows-safe verzió
- Duplakattintással is nyitva marad a konzol
- Hibák esetén is látod a hibaüzenetet
"""

import json, difflib, re, os, sys, traceback
from datetime import datetime
from pathlib import Path

KB_FILENAME = "chatbot_kb.json"



def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9áéíóöőúüűçß\s\?\!\.,]", "", text)
    return re.sub(r"\s+", " ", text)

class JARVIS:
    def __init__(self, kb_path: str = KB_FILENAME):
        self.kb_path = Path(kb_path)
        self.kb = {}
        if self.kb_path.exists():
            self.load()

    def add_pair(self, question: str, answer: str, save: bool = True):
        qn = normalize(question)
        self.kb[qn] = answer.strip()
        if save:
            self.save()
        return True

    def remove_pair(self, question: str, save: bool = True):
        qn = normalize(question)
        if qn in self.kb:
            del self.kb[qn]
            if save:
                self.save()
            return True
        return False

    def list_pairs(self):
        return [(q, self.kb[q]) for q in sorted(self.kb.keys())]

    def save(self):
        with open(self.kb_path, "w", encoding="utf-8") as f:
            json.dump({"meta": {"saved_at": datetime.utcnow().isoformat()}, "kb": self.kb}, f, ensure_ascii=False, indent=2)

    def load(self):
        try:
            with open(self.kb_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.kb = data.get("kb", {})
            return True
        except Exception as e:
            print("Hiba a betöltésnél:", e)
            return False

    def respond(self, text: str, cutoff: float = 0.6) -> str:
        q = normalize(text)
        if not q:
            return "Kérlek írj valamit."
        if q in self.kb:
            return self.kb[q]
        keys = list(self.kb.keys())
        if not keys:
            return "Még nem tanítottál semmit. Használd az 'add' parancsot."
        matches = difflib.get_close_matches(q, keys, n=3, cutoff=cutoff)
        if matches:
            best = matches[0]
            ratio = difflib.SequenceMatcher(None, q, best).ratio()
            return f"(talált hasonlóság: {ratio:.2f}) {self.kb[best]}"
        for key in keys:
            if key in q or q in key:
                return self.kb[key]
        closest = difflib.get_close_matches(q, keys, n=1, cutoff=0.0)
        if closest:
            return f"Nem vagyok benne biztos. Talán erre gondoltad: '{closest[0]}' -> {self.kb[closest[0]]}"
        return "Sajnálom, nem tudok erre válaszolni még. Taníts meg: add \"kérdés\" -> \"válasz\""

def repl(bot: JARVIS):
    print("JARVIS — írj be valamit. Parancsok: add, remove, list, save, load, exit")
    while True:
        try:
            inp = input("\nTe: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nKilépés...")
            break
        if not inp:
            continue
        cmd = inp.split(" ",1)[0].lower()
        try:
            if cmd == "add":
                rest = inp[len("add"):].strip()
                if "->" in rest:
                    q,a = rest.split("->",1)
                    bot.add_pair(q.strip(), a.strip())
                    print("Bot: Tanultam. ('%s' -> '%s')" % (q.strip(), a.strip()))
                else:
                    print("Használat: add kérdés -> válasz")
            elif cmd == "remove":
                rest = inp[len("remove"):].strip()
                if rest:
                    ok = bot.remove_pair(rest)
                    print("Bot: Törölve." if ok else "Bot: Nem találtam ilyen kérdést.")
                else:
                    print("Használat: remove <kérdés>")
            elif cmd == "list":
                pairs = bot.list_pairs()
                if not pairs:
                    print("Bot: Nincs tanult pár.")
                else:
                    print("Bot: Tanult párok:")
                    for q,a in pairs:
                        print(f" - '{q}' -> '{a}'")
            elif cmd == "save":
                bot.save()
                print("Bot: Mentve.")
            elif cmd == "load":
                bot.load()
                print("Bot: Betöltve.")
            elif cmd in ["exit","quit"]:
                print("Bot: Viszlát!")
                break
            else:
                ans = bot.respond(inp)
                print("Bot:", ans)
        except Exception:
            print("Hiba történt a parancs feldolgozása közben:")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        bot = JARVIS()
        if not bot.kb:
            bot.add_pair("szia", "Szia! Miben segíthetek?")
            bot.add_pair("hogy vagy", "Köszönöm, jól. Te hogy vagy?")
            bot.add_pair("mi a neved", "A nevem TrainableChatbot — te tanítasz.")
        print("=== Demo válaszok ===")
        for q in ["szia", "ki vagy te", "hogy vagyok ma", "mi a neved"]:
            print(f"\nTe: {q}\nBot: {bot.respond(q)}")
        print("\n=== REPL indítása ===")
        repl(bot)
    except Exception:
        print("Hiba történt a program indítása közben:")
        traceback.print_exc()
    input("\nNyomj Entert a kilépéshez...")


"""
CredStrike - Smart Wordlist Generator
Synthetic Password Auditing Lab

Features:
- Interactive input()
- Profile processing
- Casing mutations
- Word combinations
- Leetspeak transformations
- Suffix mutations
- Deduplication
- Length validation
- TXT export

Use synthetic profiles in authorized lab environments.
"""

from dataclasses import dataclass
from pathlib import Path
from itertools import combinations
from time import sleep
import re


@dataclass
class Profile:
    first_name: str
    last_name: str
    pet_name: str
    birth_year: str
    company: str


class WordlistGenerator:

    def __init__(self, min_length, max_length, max_words=50000):

        self.min_length = min_length
        self.max_length = max_length
        self.max_words = max_words

        self.words = set()

        self.stats = {
            "casing": 0,
            "combinations": 0,
            "suffixes": 0,
            "leetspeak": 0
        }

        self.leet_map = {
            "a": "4",
            "e": "3",
            "i": "1",
            "o": "0",
            "s": "5",
            "t": "7"
        }

        self.suffixes = [
            "123",
            "1234",
            "!",
            "@",            "01",
            "99"
        ]

    def validate(self, word):

        if not word:
            return False

        if not self.min_length <= len(word) <= self.max_length:
            return False

        return bool(re.fullmatch(pattern, word))

    def add_word(self, word):

        if len(self.words) >= self.max_words:
            return False

        if self.validate(word) and word not in self.words:

            self.words.add(word)
            return True

        return False

    def casing_mutations(self, word):

        return {
            word.lower(),
            word.upper(),
            word.capitalize(),
            word.title()
        }

    def leetspeak_mutations(self, word):

        variants = set()

        for character, replacement in self.leet_map.items():

            if character in word.lower():

                mutated = re.sub(
                    character,
                    replacement,
                    word,
                    count=1,
                    flags=re.IGNORECASE
                )

                variants.add(mutated)

        return variants

    def suffix_mutations(self, word):

        return {
            word + suffix
            for suffix in self.suffixes
        }

    def combine_words(self, base_words):

        results = set()

        for first, second in combinations(base_words, 2):

            results.add(first + second)
            results.add(first + "_" + second)
            results.add(first + "." + second)
            results.add(first + second.capitalize())

        return results

    def extract_profile_words(self, profile):

        values = [
            profile.first_name,
            profile.last_name,
            profile.pet_name,
            profile.birth_year,
            profile.company
        ]

        return [
            value.strip()
            for value in values
            if value and value.strip()
        ]

    def generate(self, profile):

        base_words = self.extract_profile_words(profile)

        print("\n[*] Starting generation...")

        print("[*] Applying casing mutations...")

        for word in base_words:

            for variant in self.casing_mutations(word):

                if self.add_word(variant):
                    self.stats["casing"] += 1

        print("[*] Generating combinations...")

        combined_words = self.combine_words(base_words)

        for word in combined_words:

            if self.add_word(word):
                self.stats["combinations"] += 1

        print("[*] Applying suffix mutations...")

        current_words = list(self.words)

        for word in current_words:

            for variant in self.suffix_mutations(word):

                if self.add_word(variant):
                    self.stats["suffixes"] += 1

        print("[*] Applying leetspeak mutations...")

        current_words = list(self.words)

        for word in current_words:

            for variant in self.leetspeak_mutations(word):

                if self.add_word(variant):
                    self.stats["leetspeak"] += 1

        print("[+] Generation completed!")

    def show_statistics(self):

        print("\n" + "=" * 45)
        print("          GENERATION STATISTICS")
        print("=" * 45)

        for mutation, count in self.stats.items():

            print(f"{mutation.capitalize():20}: {count}")

        print("-" * 45)

        print(f"{'Total unique entries':20}: {len(self.words)}")

        print("=" * 45)

    def export(self, filename):

        output_file = Path(filename)

        sorted_words = sorted(self.words)

        output_file.write_text(
            "\n".join(sorted_words) + "\n",
            encoding="utf-8"
        )

        print("\n[+] Export successful!")
        print(f"[+] File: {output_file.resolve()}")
        print(f"[+] Entries: {len(self.words)}")
        print(f"[+] Size: {output_file.stat().st_size} bytes")


def get_positive_integer(message):

    while True:

        try:

            value = int(input(message))

            if value > 0:
                return value

            print("[-] Enter a number greater than zero.")

        except ValueError:

            print("[-] Invalid input. Please enter an integer.")


def get_profile():

    print("\n" + "=" * 45)
    print("             PROFILE INPUT")
    print("=" * 45)

    print("Use synthetic test data.\n")

    first_name = input("[?] First name: ").strip()
    last_name = input("[?] Last name: ").strip()
    pet_name = input("[?] Pet name: ").strip()
    birth_year = input("[?] Birth year: ").strip()
    company = input("[?] Company name: ").strip()

    return Profile(
        first_name,
        last_name,
        pet_name,
        birth_year,
        company
    )


def main():

    print("\n")
    print("=" * 45)
    print("       CREDSTRIKE WORDLIST GENERATOR")
    print("=" * 45)

    print("\n[1] Enter synthetic profile")
    print("[2] Configure password length")
    print("[3] Generate wordlist")
    print("[4] Export wordlist")

    profile = get_profile()

    print("\n" + "=" * 45)
    print("        PASSWORD LENGTH SETTINGS")
    print("=" * 45)

    while True:

        min_length = get_positive_integer(
            "[?] Minimum password length: "
        )

        max_length = get_positive_integer(
            "[?] Maximum password length: "
        )

        if max_length >= min_length:
            break

        print("\n[-] Maximum length cannot be smaller than minimum length.")
        print("[-] Please enter the values again.\n")

    max_words = get_positive_integer(
        "\n[?] Maximum number of entries (default 50000): "
    )

    generator = WordlistGenerator(
        min_length=min_length,
        max_length=max_length,
        max_words=max_words
    )

    generator.generate(profile)

    generator.show_statistics()

    filename = input(
        "\n[?] Output filename (default credstrike.txt): "
    ).strip()

    if not filename:
        filename = "credstrike.txt"

    if not filename.lower().endswith(".txt"):
        filename += ".txt"

    generator.export(filename)

    print("\n[+] CredStrike finished successfully!")
    sleep(1)

if __name__ == "__main__":
    main()

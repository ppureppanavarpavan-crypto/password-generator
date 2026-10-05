import json
import os
import secrets
import string
from pathlib import Path
from typing import Optional


STORE_PATH = Path(__file__).with_name("passwords.json")


def generate_password(
    length: int,
    *,
    uppercase: bool = True,
    lowercase: bool = True,
    numbers: bool = True,
    symbols: bool = True,
) -> str:
    """Generate a password containing at least one character from each selected group."""
    if not isinstance(length, int) or isinstance(length, bool):
        raise ValueError("Length must be a whole number.")
    if length < 1:
        raise ValueError("Length must be at least 1.")

    groups = []
    if uppercase:
        groups.append(string.ascii_uppercase)
    if lowercase:
        groups.append(string.ascii_lowercase)
    if numbers:
        groups.append(string.digits)
    if symbols:
        groups.append(string.punctuation)

    if not groups:
        raise ValueError("Select at least one character type.")
    if length < len(groups):
        raise ValueError("Length must be at least the number of selected character types.")

    characters = [secrets.choice(group) for group in groups]
    alphabet = "".join(groups)
    characters.extend(secrets.choice(alphabet) for _ in range(length - len(characters)))

    for index in range(len(characters) - 1, 0, -1):
        swap_index = secrets.randbelow(index + 1)
        characters[index], characters[swap_index] = characters[swap_index], characters[index]

    return "".join(characters)


class PasswordStore:
    def __init__(self, path: Path = STORE_PATH) -> None:
        self.path = path

    def load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Could not read password store: {error}") from error

        if not isinstance(data, dict) or not all(
            isinstance(site, str) and isinstance(password, str)
            for site, password in data.items()
        ):
            raise ValueError("Password store has an invalid format; it was not changed.")
        return data

    def save(self, entries: dict[str, str]) -> None:
        try:
            self.path.write_text(
                json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            if os.name != "nt":
                self.path.chmod(0o600)
        except OSError as error:
            raise ValueError(f"Could not save password store: {error}") from error

    def add(self, site: str, password: str) -> None:
        entries = self.load()
        entries[site] = password
        self.save(entries)


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{prompt} ({hint}): ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter yes or no.")


def prompt_for_password() -> str:
    while True:
        try:
            length = int(input("Password length: ").strip())
        except ValueError:
            print("Enter a whole number.")
            continue
        if length < 1:
            print("Length must be at least 1.")
            continue

        selected = {
            "uppercase": ask_yes_no("Include uppercase letters?"),
            "lowercase": ask_yes_no("Include lowercase letters?"),
            "numbers": ask_yes_no("Include numbers?"),
            "symbols": ask_yes_no("Include symbols?"),
        }
        try:
            return generate_password(length, **selected)
        except ValueError as error:
            print(error)


def list_sites(store: PasswordStore) -> list[str]:
    entries = store.load()
    sites = sorted(entries, key=str.casefold)
    if not sites:
        print("No passwords are saved.")
        return []

    print("Saved websites:")
    for index, site in enumerate(sites, start=1):
        print(f"{index}. {site}")
    return sites


def choose_site(sites: list[str]) -> Optional[str]:
    if not sites:
        return None
    try:
        choice = int(input("Choose a website number: ").strip())
    except ValueError:
        print("Enter a valid number.")
        return None
    if not 1 <= choice <= len(sites):
        print("That number is not in the list.")
        return None
    return sites[choice - 1]


def run() -> None:
    store = PasswordStore()
    print("Password Generator and Manager")
    print(f"Local store: {store.path}")
    print("Warning: saved passwords are unencrypted on this device.")

    while True:
        print("\n1. Generate a password")
        print("2. Generate and save for a website")
        print("3. List saved websites")
        print("4. Show a saved password")
        print("5. Exit")
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                password = prompt_for_password()
                print(f"\nGenerated password: {password}")
            elif choice == "2":
                site = input("Website name: ").strip()
                if not site:
                    print("Website name cannot be empty.")
                    continue
                password = prompt_for_password()
                store.add(site, password)
                print(f"Password saved for {site}.")
                print(f"Generated password: {password}")
            elif choice == "3":
                list_sites(store)
            elif choice == "4":
                sites = list_sites(store)
                site = choose_site(sites)
                if site is not None:
                    print(f"Password for {site}: {store.load()[site]}")
            elif choice == "5":
                print("Goodbye.")
                return
            else:
                print("Choose an option from 1 to 5.")
        except ValueError as error:
            print(error)


if __name__ == "__main__":
    run()

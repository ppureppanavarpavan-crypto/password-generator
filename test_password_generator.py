import io
import string
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from password_generator import PasswordStore, generate_password, list_sites


class GeneratePasswordTests(unittest.TestCase):
    def test_password_has_requested_length_and_all_selected_groups(self) -> None:
        password = generate_password(
            20,
            uppercase=True,
            lowercase=True,
            numbers=True,
            symbols=True,
        )

        self.assertEqual(len(password), 20)
        self.assertTrue(any(char in string.ascii_uppercase for char in password))
        self.assertTrue(any(char in string.ascii_lowercase for char in password))
        self.assertTrue(any(char in string.digits for char in password))
        self.assertTrue(any(char in string.punctuation for char in password))

    def test_password_uses_only_selected_group(self) -> None:
        password = generate_password(
            16,
            uppercase=False,
            lowercase=False,
            numbers=True,
            symbols=False,
        )

        self.assertEqual(len(password), 16)
        self.assertTrue(password.isdigit())

    def test_rejects_no_groups_and_too_short_length(self) -> None:
        with self.assertRaises(ValueError):
            generate_password(12, uppercase=False, lowercase=False, numbers=False, symbols=False)
        with self.assertRaises(ValueError):
            generate_password(2, uppercase=True, lowercase=True, numbers=True, symbols=False)
        with self.assertRaises(ValueError):
            generate_password(0)


class PasswordStoreTests(unittest.TestCase):
    def test_load_add_and_reload_password(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = PasswordStore(Path(directory) / "passwords.json")

            self.assertEqual(store.load(), {})
            store.add("example.com", "not-printed-by-the-store")
            self.assertEqual(store.load(), {"example.com": "not-printed-by-the-store"})

    def test_listing_websites_does_not_print_saved_passwords(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = PasswordStore(Path(directory) / "passwords.json")
            store.add("example.com", "do-not-show-this")
            output = io.StringIO()

            with redirect_stdout(output):
                list_sites(store)

            self.assertIn("example.com", output.getvalue())
            self.assertNotIn("do-not-show-this", output.getvalue())


if __name__ == "__main__":
    unittest.main()

import os
import tkinter as tk
import tkinter.messagebox as mb
import tkinter.simpledialog as simpdial

USER_FILE = "./users.txt"

no_user_chars = ":[]{}"
password_must_include = "1234567890!£$%^&*()\\/\"'_-@#~,.?`¬¦;:"
password_has_chars = False
users = []
usernames = []
char_rec = ""

new_user = tk.StringVar(value="")
new_pass = tk.StringVar(value="")

def signup_main():
    users = {}

    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if ":" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        users[parts[0]] = parts[1]

    while True:
        username = ""
        while username == "":
            u = simpdial.askstring("Enter a username", "Please choose a username")
            if u is None:
                return

            if len(u) < 3:
                mb.showerror("Invalid username", "Username must be at least 4 characters.")
                continue

            bad_char_found = False
            for c in u:
                for bad in no_user_chars:
                    if c == bad:
                        bad_char_found = True
                        break
                if bad_char_found:
                    break

            if bad_char_found:
                mb.showerror("Invalid username", "Username contains invalid characters.")
                continue

            exists = False
            for existing in users:
                if existing == u:
                    exists = True
                    break

            if exists:
                mb.showerror("Invalid username", "This username is already taken.")
                continue

            username = u

        while True:
            password = simpdial.askstring("Enter a password", "Please choose a password", show="*")
            if password is None:
                return

            if len(password) < 7:
                mb.showerror("Invalid password", "Password must be at least 8 characters.")
                continue

            has_required = False
            for req in password_must_include:
                found = False
                for p in password:
                    if p == req:
                        found = True
                        break
                if found:
                    has_required = True
                    break

            if not has_required:
                mb.showerror("Invalid password", "Password must include at least one number or special character.")
                continue

            break

        with open(USER_FILE, "a", encoding="utf-8") as f:
            f.write(username + ":" + password + "\n")

        if len(username) >= 4 and len(password) >= 8:
            new_user.set(username)
            new_pass.set(password)
            return [username, password]
        else:
            exit()


if __name__ == "__main__":
    signup_main()

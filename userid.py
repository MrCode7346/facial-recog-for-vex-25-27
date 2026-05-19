import tkinter as tk
from tkinter import messagebox as mb
from tkinter import simpledialog as simpdial
from faceid import *


USER_FILE = "./users.txt"

user_inp = tk.StringVar(value="")
pass_inp = tk.StringVar(value="")

def userid_main():
    users = []
    usernames = []
    passwords = []
    chars = ""

    with open(USER_FILE, "r", encoding="utf-8") as f:
        for char in f.read():
            if char != "\n":
                chars += char
            elif char == "\n":
                users.append(chars)
                chars = ""
                continue
    
    for user in users:
        usernames.append(user.split(":")[0])
        passwords.append(user.split(":")[1])

    username_input = ""
    password_input = ""

    keep_going = True

    while keep_going: 
        if username_input == "":
            username = simpdial.askstring("Enter a username...", "Enter your username")

            if username == None:
                mb.showerror("Invalid input...", "Please input a username...")
                continue
            elif not username in usernames:
                mb.showerror("Invalid username...", "Please input a valid username...")
                continue
            elif username in usernames:
                username_input += username
        elif password_input == "":
            password = simpdial.askstring("Enter your password...", f"Enter the password for user: {username_input}", show="*")
            go_counter = 0

            if password == None and go_counter <= 1:
                mb.showerror("Invalid input...", f"Please input a password for user: {username_input}")
                go_counter += 1
                if go_counter == 2:
                    exit()
                continue
            elif not password in passwords:
                mb.showerror("Invalid password...", f"Incorrect password for {username_input}")
                sign_up = mb.askyesno("Sign up...", "Would you like to sign up?")
                if sign_up:
                    signup_face()
                else:
                    continue
            elif password in passwords:
                password_input += password
                keep_going = False

    if username_input == "" or password_input == "":
        exit()
    elif username_input != "" and password_input != "":
        user_inp.set(username_input)
        pass_inp.set(password_input)
        return [username_input, password_input]

if __name__ == "__main__":
    userid_main()
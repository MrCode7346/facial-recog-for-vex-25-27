import tkinter as tk
import os

root = tk.Tk()
root.title("FaceID app...")

APP_FONT = ("Comic Sans MS", 14)

from faceid import *
from userid import *

main_win = None

def logout():
    global main_win
    if main_win:
        main_win.destroy()
        main_win = None
    person_name.set("")
    user_inp.set("")
    root.deiconify()

def open_main_window():
    global main_win

    main_win = tk.Toplevel(root)
    main_win.title("Main window...")

    name = person_name.get() if person_name.get() != "" else user_inp.get()

    label = tk.Label(main_win, text=f"Welcome {name}!", font=APP_FONT)
    label.pack(pady=20)

    btn1 = tk.Button(main_win, text="Tic Tac Toe", font=APP_FONT, width=20, command=lambda: os.system("python ../tictactoe/main.py"))
    btn1.pack(pady=10)

    btn2 = tk.Button(main_win, text="Option 2", font=APP_FONT, width=20, command=lambda: os.system("cd ../llm-ai; python main.py"))
    btn2.pack(pady=10)

    logout_btn = tk.Button(main_win, text="Logout", font=APP_FONT, width=20, command=logout)
    logout_btn.pack(pady=10)

def signup_wrapper():
    signup_face()
    if person_name.get() != "":
        open_main_window()

def face_login_wrapper():
    faceid_main()
    if person_name.get() != "":
        open_main_window()

def user_login_wrapper():
    userid_main()
    if user_inp.get() != "":
        open_main_window()

signup_btn = tk.Button(root, text="Sign up", font=APP_FONT, width=30, command=signup_wrapper)
face_login = tk.Button(root, text="Login via FaceID", font=APP_FONT, width=30, command=face_login_wrapper)
user_login = tk.Button(root, text="Login via Username/Password", font=APP_FONT, width=30, command=user_login_wrapper)

signup_btn.pack(padx=10, pady=10)
face_login.pack(padx=10, pady=10)
user_login.pack(padx=10, pady=10)

root.mainloop()

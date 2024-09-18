from tkinter import *
from tkinter import filedialog
from tkinter import font

root = Tk()
root.title('Capitulador')
# root.iconbitmap('c:/gui/codemy.ico')
root.geometry('1200x800')

my_frame = Frame(root)
my_frame.pack(pady=5)

text_scroll = Scrollbar(my_frame)
text_scroll.pack(side=RIGHT, fill=Y)

my_text = Text(my_frame, 
               width=97, 
               height=25, 
               font=('Helvetica', 16),
               selectbackground='yellow',
               selectforeground='black',
               undo=True,
               yscrollcommand=text_scroll.set)

my_text.pack()

text_scroll.config(command=my_text.yview)

root.mainloop()
from OSUtil import OSutil
from tkinter import *

import threading, queue
from tkinter import filedialog 



#This queue lets us have the graphical interface and status window
q = queue.Queue()

#lets us search for directory
def browseFiles(): 
    folderSelected = filedialog.askdirectory()
    # Change label contents 
    directory.insert(0, str(folderSelected))


#Search the directory      
def searchDIR():
	username = userName.get()
	userpass = password.get()
	folder = directory.get()
	window.after(300, updateTextField)
	OSObject = OSutil(username, userpass, folder, q)

	threading.Thread(target=OSObject.backendProgram, args=(q,), daemon=True).start()

#Let us show what is happening. this program is dependant of opensubtitles servers at the moment. They arent the best
def updateTextField():
	try:
		if q.qsize() > 0:
			info = q.get()
			textWindow.delete(1.0, 'end')	
			textWindow.insert('end', info)
	except (NameError, queue.Empty) as e:
		pass
	window.after(300, updateTextField)


# Create the root window 
window = Tk()   
# Set window title 
window.title('Subbie')
try: 
	p1 = PhotoImage(file = 'files/subbie.png') 
	window.iconphoto(False, p1)
except TclError:
	pass	
# Set window size 
window.config(height=200, width=400) 
   
userLabel = Label(window, text="User Name")
userName = Entry(window)

passLabel = Label(window, text="Password")
password = Entry(window, show='*')
   
directory = Entry(window, width=30)      
buttonSearch = Button(window,  
                        text = "Browse for Directory", 
                        command = browseFiles)

textWindow = Text(window, height=2, width=39)
textWindow.insert('end', 'Status Window')

buttonRun = Button(window,  
                        text = "Scan Directory", 
                        command = searchDIR)    
   
buttonExit = Button(window,  
                     text = "Exit", 
                     command = window.destroy) 



userLabel.place(relx=0.2, rely=0.1)
userName.place(relx=0.45, rely=0.1)

passLabel.place(relx=0.2, rely=0.2)
password.place(relx=0.45, rely=0.2)

directory.place(relx=0.1, rely=0.35)
buttonSearch.place(relx=0.6, rely=0.34)

textWindow.place(relx=0.1, rely=0.5)

buttonRun.place(relx=0.42, rely= 0.8, anchor=CENTER)
buttonExit.place(relx=0.62, rely=0.8, anchor=CENTER)




if __name__ == "__main__":

	window.mainloop() 
import socket               # for network connections
import tkinter as tk        # gui 
from tkinter import ttk     # for dropdown
import threading            # for threading support
import time                 # for scan delays

scanning = False            # flag to stop scan
output_lines = []           # holds lines to write to file

# gets banner info if any
def grab_banner(ip, port):
    try:
        s = socket.socket()         # make socket
        s.settimeout(1)             # 1 sec timeout
        s.connect((ip, port))       # try to connect
        banner = s.recv(1024).decode(errors='ignore').strip()  # grab and decode
        s.close()                   # close it up
        return banner if banner else 'no banner'
    except:
        return 'no banner'

# thread runs this to scan a single port
def scan_port(ip, port, delay, show_closed, get_banners, lock, output_box):
    if not scanning: return         # quit if scan is off

    try:
        s = socket.socket()         # make socket
        s.settimeout(1)             # timeout for connect
        result = s.connect_ex((ip, port))  # returns 0 if open
        s.close()
        state = 'OPEN' if result == 0 else 'closed'
    except:
        state = 'error'             # connection failed

    banner = grab_banner(ip, port) if state == 'OPEN' and get_banners else ''  # get banner if wanted

    if state == 'OPEN' or show_closed:         # show if open or setting allows closed
        with lock:                             # thread-safe update
            line = f'Port {port:<5} → {state}'
            if banner:
                line += f' | {banner}'
            output_box.insert(tk.END, line + '\n')  # show in gui
            output_box.see(tk.END)                 # auto-scroll
            output_lines.append(line)              # store for file

    time.sleep(delay)       # delay between scans

# this runs when scan button clicked
def start_scan():
    global scanning, output_lines
    scanning = True
    output_lines = []           # clear last run

    ip = ip_entry.get()
    mode = mode_var.get()
    show_closed = show_closed_var.get()
    save = save_var.get()
    get_banners = banner_var.get()

    output_box.delete('1.0', tk.END)       # clear gui output

    try:
        host = socket.gethostbyaddr(ip)[0]          # reverse dns
        output_box.insert(tk.END, f'\n[+] Host resolved: {host}\n')
    except:
        output_box.insert(tk.END, f'\n[!] Could not resolve host\n')

    # define port range, delay, and thread count by mode
    if mode == 'Stealth':
        ports = range(10, 1024)
        delay = 0.5
        max_threads = 10
    elif mode == 'Aggressive':
        ports = range(1, 1025)
        delay = 0.01
        max_threads = 100
    elif mode == 'Script':
        ports = range(20, 100)
        delay = 0.2
        max_threads = 50
    else:
        output_box.insert(tk.END, "unknown mode selected\n")
        return

    output_box.insert(tk.END, f'\n[+] Scanning {ip} in {mode} mode...\n\n')

    lock = threading.Lock()     # to avoid output clashing
    threads = []

    for port in ports:
        if not scanning:
            output_box.insert(tk.END, '\n[!] Scan stopped by user\n')
            break

        t = threading.Thread(target=scan_port, args=(
            ip, port, delay, show_closed, get_banners, lock, output_box))
        threads.append(t)
        t.start()

        while threading.active_count() > max_threads:
            time.sleep(0.01)     # wait if too many threads

    for t in threads:
        t.join()     # wait for all to finish

    if scanning:
        output_box.insert(tk.END, '\n[✓] Scan complete\n')

    if save:
        with open('scan_output.txt', 'w') as f:
            f.write('\n'.join(output_lines))
        output_box.insert(tk.END, '\n[+] results saved to scan_output.txt\n')

# stop button hits this
def stop_scan():
    global scanning
    scanning = False

# === gui layout below ===

root = tk.Tk()
root.title('ransomw port scanner')               # window title
root.geometry('850x650')                         # window size
root.configure(bg='#1e1e1e')                     # dark background

tk.Label(root, text='target ip:', bg='#1e1e1e', fg='white', font=('Arial', 14)).pack(pady=5)
ip_entry = tk.Entry(root, font=('Consolas', 13), width=30)
ip_entry.pack()

tk.Label(root, text='scan mode:', bg='#1e1e1e', fg='white').pack()
mode_var = tk.StringVar()
mode_dropdown = ttk.Combobox(root, textvariable=mode_var, values=['Stealth', 'Aggressive', 'Script'])
mode_dropdown.current(0)
mode_dropdown.pack()

show_closed_var = tk.BooleanVar()
show_closed_var.set(True)
tk.Checkbutton(root, text='show closed ports', variable=show_closed_var,
               bg='#1e1e1e', fg='white', selectcolor='#1e1e1e').pack()

banner_var = tk.BooleanVar()
tk.Checkbutton(root, text='grab banners (slow)', variable=banner_var,
               bg='#1e1e1e', fg='white', selectcolor='#1e1e1e').pack()

save_var = tk.BooleanVar()
tk.Checkbutton(root, text='save results to file', variable=save_var,
               bg='#1e1e1e', fg='white', selectcolor='#1e1e1e').pack()

output_box = tk.Text(root, height=25, width=100, bg='black', fg='lime', font=('Consolas', 10))
output_box.pack(pady=10)

button_frame = tk.Frame(root, bg='#1e1e1e')
button_frame.pack()

tk.Button(button_frame, text='start scan', command=lambda: threading.Thread(target=start_scan).start(),
          width=15, bg='green', fg='white').grid(row=0, column=0, padx=10)
tk.Button(button_frame, text='stop scan', command=stop_scan,
          width=15, bg='red', fg='white').grid(row=0, column=1, padx=10)

root.mainloop()     # start the gui loop

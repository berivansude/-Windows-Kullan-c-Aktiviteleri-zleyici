import os
import psutil
import winreg
import tkinter as tk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import datetime
import win32com.client

# Başlangıçta kurulu olan programların listesi
previous_installed_programs = set()

# Çalışan programları listeleyen ve çalışma süresini hesaplayan fonksiyon
def get_running_processes():
    process_list = []
    for process in psutil.process_iter(['pid', 'name', 'create_time']):
        try:
            process_info = process.info
            start_time = datetime.datetime.fromtimestamp(process_info['create_time'])
            run_time = datetime.datetime.now() - start_time  # Çalışma süresi
            process_info['run_time'] = str(run_time).split(".")[0]  # Çalışma süresini saat, dakika, saniye olarak göster
            process_list.append(process_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return process_list

# Kurulu programları kontrol eden fonksiyon ve kurulan/kaldırılanları belirleyen
def check_installed_uninstalled_programs():
    global previous_installed_programs
    current_installed_programs = set()
    reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    registry_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
    
    try:
        i = 0
        while True:
            subkey_name = winreg.EnumKey(registry_key, i)
            subkey_path = reg_path + "\\" + subkey_name
            subkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path)
            program_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
            current_installed_programs.add(program_name)
            i += 1
    except WindowsError:
        pass

    # Kurulan ve kaldırılan programları belirle
    new_installed = current_installed_programs - previous_installed_programs
    removed = previous_installed_programs - current_installed_programs
    previous_installed_programs = current_installed_programs
    
    # Çıktı dosyasına yazma
    with open("program_list.txt", "w") as file:
        file.write("Yeni Kurulan Programlar:\n")
        for program in new_installed:
            file.write(f"{program}\n")
        file.write("Kaldırılan Programlar:\n")
        for program in removed:
            file.write(f"{program}\n")
    
    return list(new_installed), list(removed)

# Yüklü uygulamaları almak için fonksiyon
def get_installed_apps():
    apps = []
    try:
        # Kayıt defterini sorgulayarak yüklü uygulamaları al
        registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path) as reg_key:
            for i in range(winreg.QueryInfoKey(reg_key)[0]):
                try:
                    app_name = winreg.EnumKey(reg_key, i)
                    with winreg.OpenKey(reg_key, app_name) as sub_key:
                        display_name = winreg.QueryValueEx(sub_key, "DisplayName")[0]
                        apps.append(display_name)
                except WindowsError:
                    continue
    except Exception as e:
        print(f"Yüklü uygulamalar alınırken bir hata oluştu: {e}")
    return apps

# Silinmiş dosyaları almak için fonksiyon
def get_deleted_files():
    deleted_files = []
    try:
        recycle_bin = win32com.client.Dispatch("Shell.Application").Namespace(10)  # 10 numaralı klasör geri dönüşüm kutusu
        for item in recycle_bin.Items():
            deleted_files.append(item.Name)  # Dosya adını ekle
    except Exception as e:
        print(f"Silinmiş dosyalar alınırken bir hata oluştu: {e}")
    return deleted_files

# Belirtilen dizindeki dosyaların bilgilerini almak için fonksiyon
def get_file_info(directory):
    files_info = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            stats = os.stat(file_path)
            created_time = datetime.datetime.fromtimestamp(stats.st_ctime)
            modified_time = datetime.datetime.fromtimestamp(stats.st_mtime)
            files_info.append({
                'file_name': file,
                'file_path': file_path,
                'created_time': created_time,
                'modified_time': modified_time,
            })
    return files_info

# Açılan dosya ve klasörleri izleyen sınıf
class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, display_func):
        self.display_func = display_func

    def on_modified(self, event):
        self.display_func(f"Modified: {event.src_path}")

    def on_created(self, event):
        self.display_func(f"Created: {event.src_path}")

    def on_deleted(self, event):
        self.display_func(f"Deleted: {event.src_path}")

# Arayüz
root = tk.Tk()
root.title("Bilgisayar İzleme Aracı")
root.geometry("800x600")  # Başlangıç boyutu
root.configure(bg='black')  # Arka plan rengi siyah

# Buton üzerine gelindiğinde rengi değiştiren fonksiyon
def change_button_color(button, color):
    button.config(bg=color)

# Giriş ekranı
def show_start_screen():
    start_frame = tk.Frame(root, bg='black')
    start_frame.pack(fill=tk.BOTH, expand=True)

    title_label = tk.Label(start_frame, text="Berivan Sude Gün 215509033\nProgram Takip Aracı", bg='black', fg='white', font=("Arial", 20))
    title_label.pack(pady=50)

    start_button = tk.Button(start_frame, text="Başla", command=lambda: [start_frame.pack_forget(), show_main_menu()], bg='black', fg='white', bd=2, font=("Arial", 14))
    start_button.pack(pady=10)

    # Buton üzerine gelindiğinde animasyon
    start_button.bind("<Enter>", lambda e: change_button_color(start_button, 'green'))
    start_button.bind("<Leave>", lambda e: change_button_color(start_button, 'black'))

# Farklı ekranlar için çerçeveler
main_frame = tk.Frame(root, bg='black')
process_frame = tk.Frame(root, bg='black')
program_frame = tk.Frame(root, bg='black')
file_frame = tk.Frame(root, bg='black')

# Ana ekrana dönme fonksiyonu
def go_back():
    process_frame.pack_forget()
    program_frame.pack_forget()
    file_frame.pack_forget()
    main_frame.pack()

# Ana ekran oluşturma
def show_main_menu():
    main_frame.pack(fill=tk.BOTH, expand=True)

    process_button = tk.Button(main_frame, text="Çalışan Programları Göster", command=show_running_processes, bg='black', fg='white', bd=2, font=("Arial", 14))
    process_button.pack(pady=10)

    program_button = tk.Button(main_frame, text="Kurulan/Kaldırılan Programları Göster", command=show_installed_uninstalled_programs, bg='black', fg='white', bd=2, font=("Arial", 14))
    program_button.pack(pady=10)

    file_button = tk.Button(main_frame, text="Dosya Değişikliklerini Göster", command=show_file_events, bg='black', fg='white', bd=2, font=("Arial", 14))
    file_button.pack(pady=10)

    # Tüm butonlar için üzerine gelindiğinde renk değiştirme
    for button in main_frame.winfo_children():
        button.bind("<Enter>", lambda e: change_button_color(e.widget, 'green'))
        button.bind("<Leave>", lambda e: change_button_color(e.widget, 'black'))

# Çalışan programları gösteren fonksiyon
def show_running_processes():
    main_frame.pack_forget()
    for widget in process_frame.winfo_children()[1:]:
        widget.destroy()  # Önceki listeyi temizle
    tk.Button(process_frame, text="Geri", command=go_back, bg='black', fg='white', bd=2, font=("Arial", 14)).pack(pady=10)

    # Çalışan programları anlık olarak güncellemek için sürekli döngü
    def update_running_processes():
        for widget in process_frame.winfo_children()[1:]:
            widget.destroy()  # Önceki listeden çıkar
        processes = get_running_processes()
        for process in processes:
            tk.Label(process_frame, text=f"{process['name']} (PID: {process['pid']}, Çalışma Süresi: {process['run_time']})", bg='black', fg='white').pack()
        process_frame.pack(fill=tk.BOTH, expand=True)
        process_frame.after(1000, update_running_processes)  # Her 1 saniyede bir güncelle

    update_running_processes()

# Kurulu ve kaldırılan programları gösteren fonksiyon
def show_installed_uninstalled_programs():
    main_frame.pack_forget()
    for widget in program_frame.winfo_children()[1:]:
        widget.destroy()  # Önceki listeyi temizle
    tk.Button(program_frame, text="Geri", command=go_back, bg='black', fg='white', bd=2, font=("Arial", 14)).pack(pady=10)

    new_installed, removed = check_installed_uninstalled_programs()

    tk.Label(program_frame, text="Yeni Kurulan Programlar:", bg='black', fg='white').pack()
    for program in new_installed:
        tk.Label(program_frame, text=program, bg='black', fg='white').pack()

    tk.Label(program_frame, text="Kaldırılan Programlar:", bg='black', fg='white').pack()
    for program in removed:
        tk.Label(program_frame, text=program, bg='black', fg='white').pack()

    # Dosya bilgilerini göster
    tk.Label(program_frame, text="Dosya Bilgileri:", bg='black', fg='white').pack()
    directory = "C:/Users/Huawei/OneDrive/Masaüstü/sesler"  # İstediğiniz dizin yolunu belirtin
    file_info = get_file_info(directory)
    for file in file_info:
        tk.Label(program_frame, text=f"{file['file_name']} (Yolu: {file['file_path']}, Oluşturulma: {file['created_time']}, Değiştirilme: {file['modified_time']})", bg='black', fg='white').pack()

    program_frame.pack(fill=tk.BOTH, expand=True)

# Dosya değişikliklerini gösteren fonksiyon
def show_file_events():
    main_frame.pack_forget()
    for widget in file_frame.winfo_children()[1:]:
        widget.destroy()  # Önceki listeyi temizle
    tk.Button(file_frame, text="Geri", command=go_back, bg='black', fg='white', bd=2, font=("Arial", 14)).pack(pady=10)

    file_events_label = tk.Label(file_frame, text="Dosya Değişiklikleri:", bg='black', fg='white')
    file_events_label.pack()

    event_handler = FileChangeHandler(lambda message: file_events_label.config(text=file_events_label.cget("text") + "\n" + message))
    observer = Observer()
    observer.schedule(event_handler, path="C:/Users/Huawei/OneDrive/Masaüstü/sesler", recursive=True)
    observer.start()

    file_frame.pack(fill=tk.BOTH, expand=True)

# Uygulamayı başlatma
show_start_screen()
root.mainloop()

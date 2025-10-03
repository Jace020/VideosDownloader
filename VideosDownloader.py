import yt_dlp
import os
import threading
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter import ttk

# ------------------- Variables globales -------------------
is_downloading = False

# ------------------- Mise à jour automatique de yt-dlp -------------------
def update_yt_dlp():
    #Vérifie et met à jour yt-dlp au lancement
    try:
        #messagebox.showinfo("Mise à jour", "Vérification et mise à jour de yt-dlp...")
        yt_dlp.main(['-U'])
        #messagebox.showinfo("Mise à jour", "yt-dlp est à jour ✅")
    except Exception as e:
        messagebox.showwarning("Mise à jour", f"Impossible de mettre à jour yt-dlp :\n{e}")

# ------------------- Fonctions de téléchargement -------------------
def dl_with_ydl(url, format_choice, folder, progress_callback=None):
    """Télécharge en utilisant yt_dlp avec callback de progression"""
    # Chemin vers ffmpeg embarqué (dossier ffmpeg/bin à côté du script/exe)
    ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg", "bin")

    options = {
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_callback] if progress_callback else None,
        'quiet': True,
        'ffmpeg_location': ffmpeg_path
    }

    if format_choice == 'mp4':
        options['format'] = 'bestvideo+bestaudio/best'
        options['merge_output_format'] = 'mp4'
    else:  # mp3
        options['format'] = 'bestaudio/best'
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    os.makedirs(folder, exist_ok=True)

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

    os.startfile(folder)

# ------------------- Interface Tkinter -------------------
def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        entry_folder.delete(0, END)
        entry_folder.insert(0, folder_selected)

def telecharger_thread():
    global is_downloading
    url = entry_url.get().strip()
    choix = format_choice.get()
    folder = entry_folder.get().strip()

    if not url:
        messagebox.showwarning("Erreur", "Veuillez entrer une URL.")
        return

    if choix not in ("mp3", "mp4"):
        messagebox.showwarning("Erreur", "Veuillez sélectionner MP3 ou MP4.")
        return

    if not folder:
        folder = "videos" if choix == "mp4" else "audios"

    # Bloquer l'UI
    btn_dl.config(state=DISABLED)
    entry_url.config(state=DISABLED)
    entry_folder.config(state=DISABLED)
    btn_folder.config(state=DISABLED)
    rb_mp3.config(state=DISABLED)
    rb_mp4.config(state=DISABLED)
    progress_bar['value'] = 0
    progress_bar.pack(pady=10)
    is_downloading = True

    def progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = downloaded / total * 100
                progress_bar['value'] = percent
                app.update_idletasks()
        elif d['status'] == 'finished':
            progress_bar['value'] = 100
            app.update_idletasks()

    def worker():
        global is_downloading
        try:
            dl_with_ydl(url, choix, folder, progress_callback=progress_hook)
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue :\n{e}")
        finally:
            is_downloading = False
            # Débloquer l'UI
            btn_dl.config(state=NORMAL)
            entry_url.config(state=NORMAL)
            entry_folder.config(state=NORMAL)
            btn_folder.config(state=NORMAL)
            rb_mp3.config(state=NORMAL)
            rb_mp4.config(state=NORMAL)
            progress_bar.pack_forget()

    threading.Thread(target=worker, daemon=True).start()

def on_closing():
    if is_downloading:
        if messagebox.askokcancel("Téléchargement en cours",
                                  "Un téléchargement est en cours.\nVoulez-vous vraiment quitter ?"):
            app.destroy()
    else:
        app.destroy()

# ------------------- Création de l'UI -------------------
app = Tk()
app.title("Téléchargeur YouTube")

screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()

win_width = 400   # largeur en pixels
win_height = 275  # hauteur en pixels
x_pos = (screen_width - win_width) // 2
y_pos = (screen_height - win_height) // 2
app.geometry(f"{win_width}x{win_height}+{x_pos}+{y_pos}")

# Label et Entry URL
Label(app, text="Entrez une URL YouTube :").pack(pady=5)
entry_url = Entry(app, width=50)
entry_url.pack(pady=5)

# Sélecteur de dossier
Label(app, text="Dossier de sortie :").pack(pady=5)
frame_folder = Frame(app)
frame_folder.pack()
entry_folder = Entry(frame_folder, width=40)
entry_folder.pack(side=LEFT, padx=(0,5))
btn_folder = Button(frame_folder, text="Parcourir...", command=select_folder)
btn_folder.pack(side=LEFT)

# Radiobuttons MP3 / MP4
format_choice = StringVar(value="")
rb_mp3 = Radiobutton(app, text="Télécharger en MP3", variable=format_choice, value="mp3")
rb_mp3.pack()
rb_mp4 = Radiobutton(app, text="Télécharger en MP4", variable=format_choice, value="mp4")
rb_mp4.pack()

# Bouton télécharger
btn_dl = Button(app, text="Lancer le téléchargement", command=telecharger_thread)
btn_dl.pack(pady=10)

# Barre de progression
progress_bar = ttk.Progressbar(app, orient=HORIZONTAL, length=int(win_width*0.9), mode='determinate')
progress_bar.pack(pady=10)
progress_bar.pack_forget()

# ------------------- Vérification maj yt-dlp -------------------
threading.Thread(target=update_yt_dlp, daemon=True).start()

app.mainloop()

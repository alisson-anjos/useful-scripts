# import tkinter as tk
# from tkinter import filedialog, messagebox
# import cv2
# from PIL import Image, ImageTk, ImageSequence, ImageDraw
# import os
# import shutil
# from moviepy.editor import VideoFileClip  # For conversion

# # Minimal Tooltip class for Tkinter widgets
# class ToolTip:
    # def __init__(self, widget, text='widget info'):
        # self.waittime = 500  # milliseconds
        # self.wraplength = 180  # pixels
        # self.widget = widget
        # self.text = text
        # self.widget.bind("<Enter>", self.enter)
        # self.widget.bind("<Leave>", self.leave)
        # self.widget.bind("<ButtonPress>", self.leave)
        # self.id = None
        # self.tw = None
    # def enter(self, event=None):
        # self.schedule()
    # def leave(self, event=None):
        # self.unschedule()
        # self.hidetip()
    # def schedule(self):
        # self.unschedule()
        # self.id = self.widget.after(self.waittime, self.showtip)
    # def unschedule(self):
        # id = self.id
        # self.id = None
        # if id:
            # self.widget.after_cancel(id)
    # def showtip(self, event=None):
        # x, y, cx, cy = self.widget.bbox("insert")
        # x += self.widget.winfo_rootx() + 25
        # y += self.widget.winfo_rooty() + 20
        # self.tw = tk.Toplevel(self.widget)
        # self.tw.wm_overrideredirect(True)
        # self.tw.wm_geometry("+%d+%d" % (x, y))
        # label = tk.Label(self.tw, text=self.text, justify='left',
                         # background='lightyellow', relief='solid', borderwidth=1,
                         # wraplength=self.wraplength)
        # label.pack(ipadx=1)
    # def hidetip(self):
        # tw = self.tw
        # self.tw = None
        # if tw:
            # tw.destroy()

# class VideoGridApp(tk.Tk):
    # def __init__(self):
        # super().__init__()
        # self.title("Video Preview & Copier")
        # self.geometry("1400x900")
        
        # # Lists and sets for video data and selection
        # self.video_files = []
        # self.thumbnails = []
        # self.thumbnail_widgets = []
        # self.marked_labels = []   # "MARKED" overlay labels
        # self.current_labels = []  # "CURRENT" overlay labels
        # self.video_info = {}      # Video details keyed by file path
        # self.marked_indices = set()  # Set of indices marked for copying
        # self.current_index = None
        
        # # Variables for preview playback
        # self.cap = None          # For regular videos
        # self.preview_job = None  # For scheduling preview updates
        
        # # Variables for GIF preview
        # self.is_current_gif = False
        # self.gif_frames = []
        # self.gif_durations = []
        # self.gif_index = 0
        
        # self.create_widgets()
        # self.bind_keys()

    # def create_widgets(self):
        # # Top frame with buttons and instructions
        # top_frame = tk.Frame(self)
        # top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        # self.select_folder_btn = tk.Button(top_frame, text="Select Folder", command=self.select_folder)
        # self.select_folder_btn.pack(side=tk.LEFT, padx=5)
        # ToolTip(self.select_folder_btn, "Click to select a folder containing video files (mp4, avi, mov, mkv, gif).")
        
        # self.copy_btn = tk.Button(top_frame, text="Copy Selected Videos", command=self.copy_selected_videos)
        # self.copy_btn.pack(side=tk.LEFT, padx=5)
        # ToolTip(self.copy_btn, "Click to copy marked videos. You can choose to convert GIFs to MP4 and set a target FPS.")
        
        # instructions = tk.Label(top_frame, text="Instructions: Use arrow keys to navigate. Press Space to mark/unmark. Click a thumbnail to preview.")
        # instructions.pack(side=tk.LEFT, padx=20)
        
        # # Main frame: grid on left, preview/details on right
        # main_frame = tk.Frame(self)
        # main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # # Left: Thumbnail grid inside a scrollable canvas
        # grid_container = tk.Frame(main_frame)
        # grid_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # self.canvas = tk.Canvas(grid_container)
        # self.scrollbar = tk.Scrollbar(grid_container, orient="vertical", command=self.canvas.yview)
        # self.scrollable_frame = tk.Frame(self.canvas)
        # self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        # self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        # self.canvas.configure(yscrollcommand=self.scrollbar.set)
        # self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # # Right: Preview and info panel
        # preview_frame = tk.Frame(main_frame, bd=2, relief=tk.SUNKEN)
        # preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # self.preview_label = tk.Label(preview_frame)
        # self.preview_label.pack(fill=tk.BOTH, expand=True)
        # ToolTip(self.preview_label, "Video preview area. For GIFs, an animated preview is shown.")
        
        # self.info_label = tk.Label(preview_frame, text="", anchor="w", justify=tk.LEFT)
        # self.info_label.pack(fill=tk.X, padx=5, pady=5)
        # ToolTip(self.info_label, "Video information: file name, resolution, FPS, frame count, duration, type (GIF/Video).")

    # def bind_keys(self):
        # self.bind("<Left>", self.navigate_left)
        # self.bind("<Right>", self.navigate_right)
        # self.bind("<Up>", self.navigate_up)
        # self.bind("<Down>", self.navigate_down)
        # self.bind("<space>", self.toggle_mark_current_video)
        # self.focus_set()
        
    # def select_folder(self):
        # folder = filedialog.askdirectory(title="Select Folder with Videos")
        # if folder:
            # self.load_videos(folder)
    
    # def load_videos(self, folder):
        # # Reset previous data and stop any running preview
        # self.video_files = []
        # self.thumbnails = []
        # self.thumbnail_widgets = []
        # self.marked_labels = []
        # self.current_labels = []
        # self.video_info = {}
        # self.marked_indices.clear()
        # self.current_index = None
        # self.is_current_gif = False
        # self.gif_frames = []
        # self.gif_durations = []
        # self.gif_index = 0
        
        # if self.preview_job:
            # self.after_cancel(self.preview_job)
            # self.preview_job = None
        # if self.cap:
            # self.cap.release()
            # self.cap = None
        
        # # Clear grid
        # for widget in self.scrollable_frame.winfo_children():
            # widget.destroy()
        
        # # Accept common video extensions plus GIF
        # video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.gif', 'webm')
        # for file in os.listdir(folder):
            # if file.lower().endswith(video_extensions):
                # full_path = os.path.join(folder, file)
                # self.video_files.append(full_path)
                # thumb = self.generate_thumbnail(full_path)
                # self.thumbnails.append(thumb)
                # info = self.get_video_info(full_path)
                # self.video_info[full_path] = info
        
        # # Display thumbnails in grid (4 columns)
        # columns = 4
        # for i, thumb in enumerate(self.thumbnails):
            # frame = tk.Frame(self.scrollable_frame, bd=2, relief=tk.RAISED)
            # label = tk.Label(frame, image=thumb)
            # label.image = thumb  # keep reference
            # label.pack()
            
            # # "CURRENT" overlay (hidden initially)
            # current_label = tk.Label(frame, text="CURRENT", bg="lightgreen", fg="blue")
            # current_label.pack(side=tk.TOP, fill=tk.X)
            # current_label.pack_forget()
            # self.current_labels.append(current_label)
            
            # # "MARKED" overlay (hidden initially)
            # mark_label = tk.Label(frame, text="MARKED", bg="yellow", fg="red")
            # mark_label.pack(side=tk.BOTTOM, fill=tk.X)
            # mark_label.pack_forget()
            # self.marked_labels.append(mark_label)
            
            # frame.grid(row=i // columns, column=i % columns, padx=5, pady=5)
            # frame.bind("<Button-1>", lambda e, idx=i: self.on_thumbnail_click(idx))
            # label.bind("<Button-1>", lambda e, idx=i: self.on_thumbnail_click(idx))
            # self.thumbnail_widgets.append(frame)
            
        # if self.video_files:
            # self.select_video(0)
    
    # def generate_thumbnail(self, video_path):
        # if video_path.lower().endswith('.gif'):
            # try:
                # im = Image.open(video_path)
                # im.seek(0)
                # im = im.convert("RGB")
                # im.thumbnail((160, 120))
                # return ImageTk.PhotoImage(im)
            # except Exception:
                # im = Image.new("RGB", (160, 120), color=(128, 128, 128))
                # return ImageTk.PhotoImage(im)
        # else:
            # cap = cv2.VideoCapture(video_path)
            # ret, frame = cap.read()
            # cap.release()
            # if ret:
                # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # image = Image.fromarray(frame)
                # image.thumbnail((160, 120))
                # return ImageTk.PhotoImage(image)
            # else:
                # image = Image.new("RGB", (160, 120), color=(128, 128, 128))
                # return ImageTk.PhotoImage(image)
    
    # def get_video_info(self, video_path):
        # if video_path.lower().endswith('.gif'):
            # try:
                # im = Image.open(video_path)
                # frame_count = getattr(im, "n_frames", 1)
                # duration = im.info.get('duration', 100) * frame_count / 1000.0
                # width, height = im.size
                # fps = 1000 / im.info['duration'] if ('duration' in im.info and im.info['duration'] > 0) else 0
                # return {
                    # "File": os.path.basename(video_path),
                    # "Resolution": f"{width}x{height}",
                    # "FPS": f"{fps:.2f}" if fps else "N/A",
                    # "Frame Count": f"{frame_count}",
                    # "Duration (s)": f"{duration:.2f}",
                    # "Type": "GIF"
                # }
            # except Exception:
                # return {
                    # "File": os.path.basename(video_path),
                    # "Resolution": "Unknown",
                    # "FPS": "N/A",
                    # "Frame Count": "N/A",
                    # "Duration (s)": "N/A",
                    # "Type": "GIF"
                # }
        # else:
            # cap = cv2.VideoCapture(video_path)
            # if not cap.isOpened():
                # return {
                    # "File": os.path.basename(video_path),
                    # "Resolution": "Unknown",
                    # "FPS": "N/A",
                    # "Frame Count": "N/A",
                    # "Duration (s)": "N/A",
                    # "Type": "Video"
                # }
            # width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            # height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            # fps = cap.get(cv2.CAP_PROP_FPS)
            # frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            # duration = frame_count / fps if fps > 0 else 0
            # cap.release()
            # return {
                # "File": os.path.basename(video_path),
                # "Resolution": f"{int(width)}x{int(height)}",
                # "FPS": f"{fps:.2f}" if fps else "N/A",
                # "Frame Count": f"{int(frame_count)}",
                # "Duration (s)": f"{duration:.2f}",
                # "Type": "Video"
            # }
    
    # def on_thumbnail_click(self, index):
        # self.select_video(index)
    
    # def select_video(self, index):
        # # Remove "CURRENT" overlay from previous selection
        # if self.current_index is not None and self.current_index < len(self.thumbnail_widgets):
            # self.thumbnail_widgets[self.current_index].config(relief=tk.RAISED)
            # self.current_labels[self.current_index].pack_forget()
        # self.current_index = index
        # self.thumbnail_widgets[self.current_index].config(relief=tk.SUNKEN)
        # self.current_labels[self.current_index].pack(side=tk.TOP, fill=tk.X)
        
        # # Stop any current preview
        # if self.preview_job:
            # self.after_cancel(self.preview_job)
            # self.preview_job = None
        # if self.cap:
            # self.cap.release()
            # self.cap = None
        
        # video_path = self.video_files[self.current_index]
        # # If GIF, load frames for animated preview; otherwise use cv2
        # if video_path.lower().endswith('.gif'):
            # self.is_current_gif = True
            # self.load_gif(video_path)
        # else:
            # self.is_current_gif = False
            # self.cap = cv2.VideoCapture(video_path)
        
        # self.play_video()
        # self.update_info_label()
    
    # def load_gif(self, video_path):
        # try:
            # im = Image.open(video_path)
            # self.gif_frames = []
            # self.gif_durations = []
            # self.gif_index = 0
            # for frame in ImageSequence.Iterator(im):
                # frame_image = frame.convert("RGB")
                # self.gif_frames.append(frame_image)
                # duration = frame.info.get('duration', 100)  # in ms
                # self.gif_durations.append(duration)
        # except Exception:
            # self.gif_frames = []
            # self.gif_durations = []
            # self.gif_index = 0
    
    # def play_video(self):
        # if self.is_current_gif:
            # if not self.gif_frames:
                # return
            # frame_image = self.gif_frames[self.gif_index]
            # imgtk = ImageTk.PhotoImage(frame_image)
            # self.preview_label.imgtk = imgtk
            # self.preview_label.config(image=imgtk)
            # delay = self.gif_durations[self.gif_index]
            # self.gif_index = (self.gif_index + 1) % len(self.gif_frames)
            # self.preview_job = self.after(delay, self.play_video)
        # else:
            # if self.cap is None:
                # return
            # ret, frame = self.cap.read()
            # if ret:
                # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # img = Image.fromarray(frame)
                # imgtk = ImageTk.PhotoImage(image=img)
                # self.preview_label.imgtk = imgtk
                # self.preview_label.config(image=imgtk)
                # fps = self.cap.get(cv2.CAP_PROP_FPS)
                # delay = int(1000 / fps) if fps > 0 else 33
                # self.preview_job = self.after(delay, self.play_video)
            # else:
                # self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                # self.play_video()
    
    # def update_info_label(self):
        # video_path = self.video_files[self.current_index]
        # info = self.video_info.get(video_path)
        # if info:
            # info_text = "\n".join(f"{k}: {v}" for k, v in info.items())
            # self.info_label.config(text=info_text)
        # else:
            # self.info_label.config(text="No video info available.")
    
    # def toggle_mark_current_video(self, event):
        # if self.current_index is None:
            # return
        # idx = self.current_index
        # if idx in self.marked_indices:
            # self.marked_indices.remove(idx)
            # self.marked_labels[idx].pack_forget()
        # else:
            # self.marked_indices.add(idx)
            # self.marked_labels[idx].pack(side=tk.BOTTOM, fill=tk.X)
    
    # def copy_selected_videos(self):
        # if not self.marked_indices:
            # messagebox.showinfo("Info", "No videos marked for copying.")
            # return
        # # Open a dialog for conversion options
        # self.open_conversion_options()
    
    # def open_conversion_options(self):
        # self.conv_win = tk.Toplevel(self)
        # self.conv_win.title("Conversion Options")
        
        # # Option to convert GIF to MP4
        # self.convert_gif_var = tk.BooleanVar()
        # self.convert_gif_var.set(False)
        # chk = tk.Checkbutton(self.conv_win, text="Convert GIF to MP4", variable=self.convert_gif_var)
        # chk.pack(padx=10, pady=5)
        # ToolTip(chk, "Check if you want to convert GIF files to MP4 format during copying.")
        
        # # Option for target FPS
        # tk.Label(self.conv_win, text="Target FPS (leave empty to use original):").pack(padx=10, pady=5)
        # self.target_fps_var = tk.StringVar()
        # fps_entry = tk.Entry(self.conv_win, textvariable=self.target_fps_var)
        # fps_entry.pack(padx=10, pady=5)
        # ToolTip(fps_entry, "Enter desired FPS for output videos. Leave empty to keep the original FPS.")
        
        # btn_frame = tk.Frame(self.conv_win)
        # btn_frame.pack(pady=10)
        # ok_btn = tk.Button(btn_frame, text="OK", command=self.on_conversion_options_ok)
        # ok_btn.pack(side=tk.LEFT, padx=5)
        # cancel_btn = tk.Button(btn_frame, text="Cancel", command=self.conv_win.destroy)
        # cancel_btn.pack(side=tk.LEFT, padx=5)
    
    # def on_conversion_options_ok(self):
        # try:
            # target_fps = float(self.target_fps_var.get()) if self.target_fps_var.get().strip() != "" else None
        # except ValueError:
            # messagebox.showerror("Error", "Invalid FPS value.")
            # return
        # convert_gif = self.convert_gif_var.get()
        # self.conv_win.destroy()
        # self.do_copy_videos(convert_gif, target_fps)
    
    # def do_copy_videos(self, convert_gif, target_fps):
        # dest_folder = filedialog.askdirectory(title="Select Destination Folder")
        # if not dest_folder:
            # return
        # for idx in self.marked_indices:
            # src = self.video_files[idx]
            # base, ext = os.path.splitext(os.path.basename(src))
            # file_type = self.video_info[src].get("Type", "Video")
            # dest_path = os.path.join(dest_folder, os.path.basename(src))
            # # For GIF files: if conversion is requested, convert to MP4
            # if file_type == "GIF" and convert_gif:
                # dest_path = os.path.join(dest_folder, base + ".mp4")
                # try:
                    # clip = VideoFileClip(src)
                    # clip.write_videofile(dest_path, fps=target_fps if target_fps is not None else clip.fps, logger=None)
                # except Exception as e:
                    # messagebox.showerror("Error", f"Error converting {base}: {str(e)}")
            # # For non-GIF videos: if target_fps is set, convert; otherwise, copy as-is
            # elif file_type != "GIF" and target_fps is not None:
                # dest_path = os.path.join(dest_folder, base + "_converted.mp4")
                # try:
                    # clip = VideoFileClip(src)
                    # clip.write_videofile(dest_path, fps=target_fps, logger=None)
                # except Exception as e:
                    # messagebox.showerror("Error", f"Error converting {base}: {str(e)}")
            # else:
                # try:
                    # shutil.copy(src, dest_folder)
                # except Exception as e:
                    # messagebox.showerror("Error", f"Error copying {base}: {str(e)}")
        # messagebox.showinfo("Info", "Selected videos processed successfully.")
    
    # # Navigation using arrow keys
    # def navigate_left(self, event):
        # if self.current_index is not None and self.current_index > 0:
            # self.select_video(self.current_index - 1)
    
    # def navigate_right(self, event):
        # if self.current_index is not None and self.current_index < len(self.video_files) - 1:
            # self.select_video(self.current_index + 1)
    
    # def navigate_up(self, event):
        # if self.current_index is not None and self.current_index - 4 >= 0:
            # self.select_video(self.current_index - 4)
    
    # def navigate_down(self, event):
        # if self.current_index is not None and self.current_index + 4 < len(self.video_files):
            # self.select_video(self.current_index + 4)

# if __name__ == '__main__':
    # app = VideoGridApp()
    # app.mainloop()
import tkinter as tk
from tkinter import ttk # Using themed widgets for better look
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk, ImageSequence, ImageDraw, ImageFont # Added ImageFont
import os
import shutil
import platform
import math # For ceiling function

# --- Configuration ---
DEFAULT_ITEMS_PER_PAGE = 40 # Default value
THUMBNAIL_WIDTH = 160
THUMBNAIL_HEIGHT = 120
THUMBNAIL_SIZE = (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)
MAX_PREVIEW_WIDTH = 800
MAX_PREVIEW_HEIGHT = 600
MAX_PREVIEW_SIZE = (MAX_PREVIEW_WIDTH, MAX_PREVIEW_HEIGHT)


# Minimal Tooltip class
class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None
        self.waittime = 500  # milliseconds
        self.wraplength = 180  # pixels

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id_val = self.id
        self.id = None
        if id_val:
            self.widget.after_cancel(id_val)

    def showtip(self, event=None):
        # Get coordinates of the mouse pointer
        x = self.widget.winfo_pointerx() + 15
        y = self.widget.winfo_pointery() + 10

        # Creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window decorations
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         wraplength=self.wraplength, font=("sans-serif", 8)) # Smaller font
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()

class MediaGridApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Media Preview, Classifier & Organizer (Paginated/Configurable)")
        self.geometry("1600x950") # Wider window

        self.style = ttk.Style(self)
        # Configure a style for the selected thumbnail frame if needed
        # self.style.configure('SelectedCard.TFrame', background='lightblue', relief=tk.SUNKEN, borderwidth=2)
        # self.style.configure('Card.TFrame', background='white', relief=tk.RAISED, borderwidth=1)

        # --- Data Storage ---
        self.all_media_files = []
        self.total_items = 0
        self.current_folder = None

        # Pagination State
        self.config_items_per_page = tk.IntVar(value=DEFAULT_ITEMS_PER_PAGE) # User configurable setting
        self.items_per_page = DEFAULT_ITEMS_PER_PAGE # Actual value used for calculations
        self.current_page = 1
        self.total_pages = 0
        self.view_all_mode = tk.BooleanVar(value=False)
        self._original_items_per_page = DEFAULT_ITEMS_PER_PAGE # To restore after view all

        # Data for CURRENT page only
        self.current_page_indices = []
        self.current_page_thumbnails = {}
        self.current_page_info = {}

        # Global State (using GLOBAL indices)
        self.marked_indices = set()
        self.media_classifications = {}

        # Selection State
        self.current_selection_page_index = None # Index WITHIN the current page

        # UI Elements
        self.thumbnail_widgets = []
        self.marked_labels = {}
        self.current_labels = {}
        self.classification_labels = {}

        # Preview Handling
        self.cap = None; self.preview_job = None; self.is_current_gif = False
        self.gif_frames = []; self.gif_photoimages = []; self.gif_durations = []; self.gif_index = 0

        # Classification Mapping
        self.classification_map = {1: "Low", 2: "Medium", 3: "High"}

        # Load default font for placeholder thumbnails
        try: self.placeholder_font = ImageFont.load_default()
        except IOError: self.placeholder_font = None # Handle case where font fails

        self.create_widgets()
        self.bind_keys()
        self._update_ui_controls_state() # Initial state

    def create_widgets(self):
        # --- Top Frame ---
        top_frame = ttk.Frame(self, padding="5 5 5 5")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self.select_folder_btn = ttk.Button(top_frame, text="Select Folder", command=self.select_folder)
        self.select_folder_btn.pack(side=tk.LEFT, padx=(0,5))
        ToolTip(self.select_folder_btn, "Select folder containing images and videos.")

        self.organize_btn = ttk.Button(top_frame, text="Organize Marked", command=self.organize_marked_items)
        self.organize_btn.pack(side=tk.LEFT, padx=5)
        ToolTip(self.organize_btn, "Copy or move marked items into subfolders.")

        # Separator
        ttk.Separator(top_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # --- Pagination Controls ---
        self.prev_page_btn = ttk.Button(top_frame, text="<< Prev", command=self.go_to_previous_page)
        self.prev_page_btn.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.prev_page_btn, "Go to Previous Page (PgUp)")

        self.page_label = ttk.Label(top_frame, text="Page - of -", width=15, anchor=tk.CENTER) # Wider label
        self.page_label.pack(side=tk.LEFT, padx=0)

        self.next_page_btn = ttk.Button(top_frame, text="Next >>", command=self.go_to_next_page)
        self.next_page_btn.pack(side=tk.LEFT, padx=(5, 0))
        ToolTip(self.next_page_btn, "Go to Next Page (PgDn)")

        # --- Items Per Page Config ---
        ttk.Label(top_frame, text="Items/Page:").pack(side=tk.LEFT, padx=(15, 2))
        self.items_per_page_entry = ttk.Entry(top_frame, textvariable=self.config_items_per_page, width=5, justify=tk.RIGHT)
        self.items_per_page_entry.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.items_per_page_entry, "Set number of items per page (requires folder reload or 'Apply')")
        self.apply_items_btn = ttk.Button(top_frame, text="Apply", command=self.apply_items_per_page, width=6)
        self.apply_items_btn.pack(side=tk.LEFT, padx=0)
        ToolTip(self.apply_items_btn, "Apply new items per page setting and reload.")

        # --- View All Option ---
        self.view_all_checkbox = ttk.Checkbutton(top_frame, text="View All", variable=self.view_all_mode, command=self.toggle_view_all)
        self.view_all_checkbox.pack(side=tk.LEFT, padx=(15, 5))
        ToolTip(self.view_all_checkbox, "Attempt to load all items (Warning: performance/memory issues likely!)")

        # --- Main Frame ---
        main_frame = ttk.Frame(self, padding="5 0 5 5")
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left: Grid
        grid_container = ttk.Frame(main_frame)
        grid_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.scrollbar = ttk.Scrollbar(grid_container, orient="vertical")
        self.canvas = tk.Canvas(grid_container, bd=0, highlightthickness=0, yscrollcommand=self.scrollbar.set, bg='lightgrey')
        self.scrollbar.config(command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.configure(style='TFrame') # Ensure default ttk style
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        if platform.system() == "Linux":
            self.canvas.bind_all("<Button-4>", self._on_mousewheel)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Right: Preview & Info Pane
        preview_container = ttk.Frame(main_frame, padding=5)
        preview_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.pane = ttk.PanedWindow(preview_container, orient=tk.VERTICAL)
        self.pane.pack(fill=tk.BOTH, expand=True)
        preview_frame = ttk.Frame(self.pane, relief=tk.SUNKEN, width=MAX_PREVIEW_WIDTH + 10, height=MAX_PREVIEW_HEIGHT + 10)
        preview_frame.pack(fill=tk.BOTH, expand=True); preview_frame.pack_propagate(False)
        self.pane.add(preview_frame, weight=4)
        self.preview_label = tk.Label(preview_frame, bg='black')
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        ToolTip(self.preview_label, "Preview area.")
        info_frame = ttk.Frame(self.pane, padding=5)
        info_frame.pack(fill=tk.BOTH, expand=True)
        self.pane.add(info_frame, weight=1)
        self.info_label = ttk.Label(info_frame, text="", anchor="nw", justify=tk.LEFT, wraplength=MAX_PREVIEW_WIDTH)
        self.info_label.pack(fill=tk.BOTH, expand=True)
        ToolTip(self.info_label, "File information.")

        # --- Status Bar ---
        status_frame = ttk.Frame(self, relief=tk.SUNKEN, padding="2 2 2 2")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(status_frame, text="Select a folder to begin.", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        instr_label = ttk.Label(status_frame, text=" | Space: Mark | Ctrl+1/2/3: Classify", anchor=tk.E)
        instr_label.pack(side=tk.RIGHT)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for the canvas."""
        if platform.system() == 'Linux': delta = -1 if event.num == 4 else 1 if event.num == 5 else 0
        else: delta = int(-1*(event.delta/120)) if hasattr(event, 'delta') and event.delta else 0
        # Only scroll canvas if mouse is over it or its direct children
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget == self.canvas or str(widget.master) == str(self.canvas):
            self.canvas.yview_scroll(delta, "units")

    def on_canvas_configure(self, event=None):
        """Adjust grid columns based on canvas width."""
        if not self.all_media_files: return
        canvas_width = self.canvas.winfo_width()
        thumb_width_estimate = THUMBNAIL_WIDTH + 10
        new_columns = max(1, canvas_width // thumb_width_estimate) if canvas_width > 0 else 1
        # Only redraw grid if number of columns changes *and* page is loaded
        if not hasattr(self, 'current_columns') or self.current_columns != new_columns:
             if self.current_page_indices: # Only redraw if page is loaded
                 print(f"Canvas resized/columns change ({getattr(self, 'current_columns', '?')}->{new_columns}). Redrawing grid.")
                 self.update_grid(new_columns) # Redraw with new column count
        # Adjust scrollable frame width to match canvas
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def bind_keys(self):
        """Bind keyboard shortcuts."""
        self.bind("<Left>", self.navigate_left)
        self.bind("<Right>", self.navigate_right)
        self.bind("<Up>", self.navigate_up)
        self.bind("<Down>", self.navigate_down)
        self.bind("<space>", self.toggle_mark_current)
        self.bind("<Prior>", lambda e: self.go_to_previous_page()) # Page Up
        self.bind("<Next>", lambda e: self.go_to_next_page())   # Page Down
        for i in range(4): # 0, 1, 2, 3 for classify
            self.bind(f"<Control-KeyPress-{i}>", lambda e, num=i: self.classify_current_item(e, num))
        # Bind Enter key in items per page entry to apply
        self.items_per_page_entry.bind("<Return>", lambda e: self.apply_items_per_page())
        self.focus_set() # Set focus to the main window initially

    def set_status(self, text):
        """Updates the status bar text."""
        self.status_label.config(text=text)
        self.update_idletasks() # Make status update immediately visible

    def select_folder(self):
        """Open folder selection dialog and load media."""
        folder = filedialog.askdirectory(title="Select Folder with Media Files")
        if folder and os.path.isdir(folder):
            self.current_folder = folder
            # Apply the value from the entry widget *before* loading
            if self.apply_items_per_page(show_confirmation=False): # Apply silently
                self.load_media(folder)
        elif folder:
            messagebox.showerror("Error", f"Invalid folder selected:\n{folder}")

    def load_media(self, folder):
        """Scans the folder for media files and prepares for pagination."""
        self.set_status(f"Scanning folder: {folder}...")
        # --- Reset State ---
        self.all_media_files = []
        # Keep marked_indices and media_classifications - they are global!
        self.current_page_thumbnails.clear()
        self.current_page_info.clear()
        self.current_page_indices = []
        self.total_items = 0
        self.current_page = 1 # Reset to page 1
        self.total_pages = 0
        self.current_selection_page_index = None

        self._stop_preview()
        self.preview_label.config(image=None); self.preview_label.imgtk = None
        self.info_label.config(text="")
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.thumbnail_widgets = []; self.marked_labels.clear(); self.current_labels.clear(); self.classification_labels.clear()
        self.update()

        # --- Scan Folder ---
        supported_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',
                                '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', 'webm')
        try:
            count = 0
            # Use scandir for potentially better performance on large directories
            for entry in os.scandir(folder):
                 if entry.is_file() and not entry.name.startswith('.') and entry.name.lower().endswith(supported_extensions):
                     self.all_media_files.append(entry.path)
                     count += 1
            # Sort AFTER collecting all paths
            self.all_media_files.sort()
            self.total_items = len(self.all_media_files)
            self.set_status(f"Found {self.total_items} supported media files in {os.path.basename(folder)}.")
        except OSError as e:
            messagebox.showerror("Error", f"Cannot access folder content:\n{folder}\n{e}")
            self._reset_ui_state(); return

        if self.total_items == 0:
            messagebox.showinfo("Info", "No supported image or video files found.")
            self._reset_ui_state(); return

        # --- Calculate Pagination (using self.items_per_page) ---
        self._recalculate_pagination()

        # --- Load First Page ---
        if self.total_pages > 0:
            self.load_page(1)
        else: # Handle edge case where items_per_page > total_items
             self._reset_ui_state()
             self.set_status(f"Found {self.total_items} items. Select a folder.")

    def load_page(self, page_number):
        """Loads data (thumbnails, info) for the specified page number."""
        if not (1 <= page_number <= self.total_pages):
            print(f"Invalid page number requested: {page_number}")
            return

        self.set_status(f"Loading page {page_number}/{self.total_pages}...")
        self.current_page = page_number
        self._stop_preview() # Stop preview from previous page

        # --- Calculate Indices for this Page ---
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = min(start_index + self.items_per_page, self.total_items)
        self.current_page_indices = list(range(start_index, end_index)) # Global indices

        # --- Clear previous page's cached data (Important for memory) ---
        self.current_page_thumbnails.clear()
        self.current_page_info.clear()
        print(f"Cleared caches for page {page_number}. Loading {len(self.current_page_indices)} items.")

        # --- Load Data for Current Page Items ---
        items_loaded = 0
        for global_idx in self.current_page_indices:
            if global_idx >= len(self.all_media_files): continue # Safety check
            file_path = self.all_media_files[global_idx]
            # Only load info/thumb if needed (cache was just cleared)
            if global_idx not in self.current_page_info:
                 info = self.get_item_info(file_path)
                 self.current_page_info[global_idx] = info
            else: info = self.current_page_info[global_idx]

            if global_idx not in self.current_page_thumbnails:
                 thumb = self.generate_thumbnail(file_path, info.get("Type", "Unknown"))
                 self.current_page_thumbnails[global_idx] = thumb
            items_loaded += 1

        print(f"Loaded data for {items_loaded} items.")

        # --- Update Grid Display ---
        # Recalculate columns based on current canvas size *before* updating grid
        canvas_width = self.canvas.winfo_width()
        thumb_width_estimate = THUMBNAIL_WIDTH + 10
        columns = max(1, canvas_width // thumb_width_estimate) if canvas_width > 0 else 1
        self.update_grid(columns) # Build grid with loaded data

        # --- Reset selection ---
        self.current_selection_page_index = None # Reset selection index for the new page
        self.info_label.config(text="")
        self.preview_label.config(image=None); self.preview_label.imgtk = None

        # Optionally select the first item on the new page
        if self.current_page_indices:
             self.select_item(0)

        self._update_ui_controls_state() # Update buttons, labels
        self.canvas.yview_moveto(0.0) # Scroll grid to top
        self.canvas.focus_set() # Set focus for key navigation
        self.set_status(f"Page {self.current_page}/{self.total_pages} loaded ({len(self.current_page_indices)} items).")

    def update_grid(self, columns):
        """Populates the grid with widgets for the CURRENTLY loaded page."""
        self.current_columns = columns
        # Clear previous grid widgets
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.thumbnail_widgets = []; self.marked_labels.clear(); self.current_labels.clear(); self.classification_labels.clear()

        if not self.current_page_indices:
            ttk.Label(self.scrollable_frame, text="No items on this page.").pack(padx=20, pady=20)
            # Update scrollregion even if empty
            self.scrollable_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            return

        for page_idx, global_idx in enumerate(self.current_page_indices):
            thumb = self.current_page_thumbnails.get(global_idx)

            # Use default relief, manage highlight via select_item
            frame = ttk.Frame(self.scrollable_frame, relief=tk.RAISED, borderwidth=1)

            label = tk.Label(frame, bg='white', width=THUMBNAIL_WIDTH, height=THUMBNAIL_HEIGHT)
            if thumb: label.config(image=thumb); label.image = thumb # Keep reference
            else: label.config(text="No Thumb", bg="grey", fg="white")
            label.pack(padx=1, pady=1)

            # Overlays
            current_label = tk.Label(frame, text="▶", bg="lightgreen", fg="blue", font=("Arial", 8, "bold"))
            mark_label = tk.Label(frame, text="✓", bg="yellow", fg="red", font=("Arial", 8, "bold"))
            class_label = tk.Label(frame, text="", width=7, anchor='e', bg="lightblue", fg="black", font=("Arial", 7))

            self.current_labels[page_idx] = current_label
            self.marked_labels[page_idx] = mark_label
            self.classification_labels[page_idx] = class_label

            current_label.place(in_=label, relx=0, rely=0, anchor='nw'); current_label.place_forget()
            mark_label.place(in_=label, relx=0, rely=1.0, anchor='sw'); mark_label.place_forget()
            class_label.place(in_=label, relx=1.0, rely=1.0, anchor='se'); class_label.place_forget()

            # Restore state based on GLOBAL index (these are persistent)
            if global_idx in self.marked_indices:
                mark_label.place(in_=label, relx=0, rely=1.0, anchor='sw')
            if global_idx in self.media_classifications:
                class_value = self.media_classifications[global_idx]
                class_label.config(text=f"{class_value}")
                class_label.place(in_=label, relx=1.0, rely=1.0, anchor='se')

            # Grid Placement
            row = page_idx // columns; col = page_idx % columns
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")

            # Bind clicks to pass the PAGE index
            frame.bind("<Button-1>", lambda e, p_idx=page_idx: self.on_thumbnail_click(p_idx))
            label.bind("<Button-1>", lambda e, p_idx=page_idx: self.on_thumbnail_click(p_idx))
            self.thumbnail_widgets.append(frame) # Store the frame widget

        # Highlight selection if it exists on this page
        if self.current_selection_page_index is not None and self.current_selection_page_index < len(self.thumbnail_widgets):
             self._highlight_selection(self.current_selection_page_index)

        # Update scrollregion after adding all widgets
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def generate_thumbnail(self, media_path, media_type):
        """Generates a thumbnail for images, GIFs, or videos."""
        try:
            img = None
            if media_type == "Video":
                cap = cv2.VideoCapture(media_path)
                ret, frame = cap.read(); cap.release()
                if ret: img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                else: raise ValueError("Vid frame read fail")
            elif media_type in ["Image", "GIF"]:
                # Use 'with' to ensure file is closed
                with Image.open(media_path) as temp_img:
                    img = temp_img.copy() # Work with a copy
                if media_type == "GIF": img.seek(0)
                if img.mode == 'RGBA' or 'transparency' in img.info:
                    img = img.convert('RGBA'); bg = Image.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3]); img = bg
                else: img = img.convert('RGB')
            else: raise ValueError(f"Unsup type {media_type}")

            if img: img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            else: raise ValueError("Img is None")
            return ImageTk.PhotoImage(img)
        except Exception as e:
            # print(f"Thumb Err {os.path.basename(media_path)}: {e}") # Reduce console noise
            ph = Image.new("RGB", THUMBNAIL_SIZE, color=(150, 150, 150))
            draw = ImageDraw.Draw(ph)
            font_to_use = self.placeholder_font if self.placeholder_font else None
            # Draw centered text
            text = "Thumb\nError"
            try: # Use textbbox for centering if possible (Pillow >= 8.0.0)
                bbox = draw.textbbox((0, 0), text, font=font_to_use, align="center")
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (THUMBNAIL_WIDTH - text_width) / 2
                y = (THUMBNAIL_HEIGHT - text_height) / 2
                draw.text((x, y), text, fill=(255,0,0), font=font_to_use, align="center")
            except AttributeError: # Fallback for older Pillow
                 draw.text((5, 5), text, fill=(255,0,0), font=font_to_use)
            return ImageTk.PhotoImage(ph)

    def get_item_info(self, media_path):
        """Gets information about an image or video file."""
        base_name = os.path.basename(media_path)
        info = {"File": base_name, "Type": "Unknown"}
        ext = os.path.splitext(media_path)[1].lower()
        try: info["Size (KB)"] = f"{os.path.getsize(media_path) / 1024:.1f}"
        except OSError: info["Size (KB)"] = "N/A"
        image_exts = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
        video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        if ext in image_exts:
            try:
                with Image.open(media_path) as im:
                    width, height = im.size; info["Dimensions"] = f"{width}x{height}"
                    info["Type"] = "GIF" if im.format == "GIF" else "Image"
                    if info["Type"] == "GIF":
                        try:
                            frame_count = getattr(im, "n_frames", 1); duration_info = im.info.get('duration', 0)
                            if isinstance(duration_info, list): duration_info = duration_info[0] # Some gifs have list duration
                            if isinstance(duration_info, int) and duration_info > 0 and frame_count > 1:
                                total_duration = (duration_info * frame_count) / 1000.0
                                info["Frames"] = f"{frame_count}"; info["Duration (s)"] = f"{total_duration:.2f}"
                        except Exception: pass # Ignore errors getting GIF details
            except Exception as e: info["Dimensions"] = "Error"; info["Type"] = "Image (Err)"
        elif ext in video_exts:
            info["Type"] = "Video"; cap = None
            try:
                cap = cv2.VideoCapture(media_path)
                if cap.isOpened():
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH); height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fps = cap.get(cv2.CAP_PROP_FPS); frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    duration = frame_count / fps if fps and fps > 0 else 0
                    info["Resolution"] = f"{int(width)}x{int(height)}"; info["FPS"] = f"{fps:.2f}" if fps else "N/A"
                    info["Duration (s)"] = f"{duration:.2f}"
                else: raise IOError("Open failed")
            except Exception as e: info["Resolution"] = "Error"; info["Type"] = "Video (Err)"
            finally:
                 if cap: cap.release()
        info["Classification"] = "None" # Placeholder, updated later
        return info

    def on_thumbnail_click(self, page_index):
        """Handle thumbnail click."""
        self.select_item(page_index)

    def select_item(self, page_index):
        """Selects an item based on its index within the current page."""
        if page_index is None or not (0 <= page_index < len(self.current_page_indices)):
            print(f"Selection failed: Invalid page index {page_index}")
            return

        global_index = self.current_page_indices[page_index]
        if global_index >= len(self.all_media_files):
             print(f"Selection failed: Global index {global_index} out of bounds")
             return

        file_path = self.all_media_files[global_index]
        info = self.current_page_info.get(global_index, {}) # Should be preloaded
        media_type = info.get("Type", "Unknown")

        self.set_status(f"Selected: {os.path.basename(file_path)} (Index {global_index})")

        # --- Update Selection Highlight ---
        self._deselect_previous()
        self._highlight_selection(page_index) # Highlight new
        self.current_selection_page_index = page_index # Update state *after* visuals

        # --- Start Preview ---
        self._stop_preview()
        if media_type == "GIF":
            self.is_current_gif = True
            if self.load_gif_frames(file_path): self.animate_gif()
            else: self.show_placeholder_preview("Error Loading GIF")
        elif media_type == "Image":
            self.display_static_image(file_path)
        elif media_type == "Video":
            self.cap = cv2.VideoCapture(file_path)
            if self.cap.isOpened(): self.play_video_frame()
            else: self.show_placeholder_preview("Error Loading Video"); self._ensure_cap_released()
        else:
             self.show_placeholder_preview(f"Cannot preview\nType: {media_type}")

        self.update_info_label()
        self.canvas.focus_set() # Ensure canvas keeps focus for key navigation

    def _deselect_previous(self):
        """Removes highlight from the previously selected item on the current page."""
        if self.current_selection_page_index is not None and self.current_selection_page_index < len(self.thumbnail_widgets):
            try:
                 prev_widget = self.thumbnail_widgets[self.current_selection_page_index]
                 prev_widget.config(relief=tk.RAISED) # Reset relief
                 # prev_widget.configure(style='TFrame') # Reset style if using ttk styles
                 if self.current_selection_page_index in self.current_labels:
                     self.current_labels[self.current_selection_page_index].place_forget()
            except (IndexError, tk.TclError): pass # Widget might be gone

    def _highlight_selection(self, page_index):
        """Highlights the selected item and scrolls it into view."""
        if page_index < len(self.thumbnail_widgets):
            try:
                 widget = self.thumbnail_widgets[page_index]
                 widget.config(relief=tk.SUNKEN) # Highlight relief
                 # widget.configure(style='SelectedCard.TFrame') # Highlight style if defined
                 label_widget = widget.winfo_children()[0] # Inner label for overlay positioning
                 if page_index in self.current_labels:
                     self.current_labels[page_index].place(in_=label_widget, relx=0, rely=0, anchor='nw')
                 self._scroll_widget_into_view(widget) # Schedule scroll
            except (IndexError, tk.TclError) as e:
                 print(f"Error highlighting widget {page_index}: {e}")

    def _scroll_widget_into_view(self, widget):
        """Scrolls the canvas to make the given widget visible."""
        # Schedule the scroll slightly later to allow layout calculations
        self.after(20, lambda: self._do_scroll(widget))

    def _do_scroll(self, widget):
        """Performs the actual scrolling."""
        try:
            self.canvas.update_idletasks() # Ensure bbox is accurate
            bbox = self.canvas.bbox(widget)
            if not bbox: return # Widget might not be mapped yet

            item_top, item_bottom = bbox[1], bbox[3]
            canvas_height = self.canvas.winfo_height()
            scroll_region_str = self.canvas.cget("scrollregion");
            scroll_region_height = float(scroll_region_str.split()[3]) if scroll_region_str else canvas_height
            if scroll_region_height <= 0: scroll_region_height = 1.0 # Avoid division by zero

            view_top, view_bottom = self.canvas.yview() # Current view fractions

            item_top_frac = item_top / scroll_region_height
            item_bottom_frac = item_bottom / scroll_region_height

            # Check if already fully visible
            if item_top_frac >= view_top and item_bottom_frac <= view_bottom:
                return

            # Scroll up if item top is above view
            if item_top_frac < view_top:
                self.canvas.yview_moveto(max(0.0, item_top_frac - 0.01)) # Move slightly above item top
            # Scroll down if item bottom is below view
            elif item_bottom_frac > view_bottom:
                # Calculate fraction needed to place bottom of item at bottom of view
                scroll_frac = (item_bottom - canvas_height) / scroll_region_height
                self.canvas.yview_moveto(max(0.0, scroll_frac))

        except (tk.TclError, ValueError, IndexError, AttributeError) as e:
            # Ignore errors during scroll calculation, might happen if things change quickly
            # print(f"Scroll error: {e}")
            pass

    def _stop_preview(self):
        """Safely stops any ongoing preview (video or GIF)."""
        if self.preview_job: self.after_cancel(self.preview_job); self.preview_job = None
        self._ensure_cap_released()
        self.is_current_gif = False; self.gif_frames = []; self.gif_photoimages = []; self.gif_durations = []; self.gif_index = 0

    def _ensure_cap_released(self):
        """Releases the OpenCV capture object if it exists."""
        if self.cap:
            try: self.cap.release()
            except Exception: pass
            self.cap = None

    # --- Preview Methods ---
    def load_gif_frames(self, image_path):
        """Loads and pre-renders PhotoImage objects for GIF frames."""
        try:
             with Image.open(image_path) as im:
                 self.gif_frames = []; self.gif_photoimages = []; self.gif_durations = []; self.gif_index = 0
                 for frame in ImageSequence.Iterator(im):
                     frame_image = frame.convert("RGBA"); frame_image.thumbnail(MAX_PREVIEW_SIZE, Image.Resampling.LANCZOS)
                     self.gif_frames.append(frame_image); self.gif_photoimages.append(ImageTk.PhotoImage(frame_image))
                     duration = frame.info.get('duration', 100); self.gif_durations.append(max(20, duration))
             return bool(self.gif_photoimages)
        except Exception as e: print(f"GIF Load Err: {e}"); self._stop_preview(); return False

    def animate_gif(self):
        """Callback for animating GIF frames."""
        if not self.is_current_gif or not self.gif_photoimages or self.current_selection_page_index is None: self._stop_preview(); return
        try:
            imgtk = self.gif_photoimages[self.gif_index]; self.preview_label.imgtk = imgtk; self.preview_label.config(image=imgtk)
            delay = self.gif_durations[self.gif_index]; self.gif_index = (self.gif_index + 1) % len(self.gif_photoimages)
            self.preview_job = self.after(delay, self.animate_gif)
        except (IndexError, tk.TclError) as e: print(f"GIF Anim Err: {e}"); self._stop_preview()

    def display_static_image(self, image_path):
        """Displays a static image in the preview pane."""
        try:
            with Image.open(image_path) as img:
                img_copy = img.copy() # Work with a copy
            # Handle transparency by pasting on white background
            if img_copy.mode == 'RGBA' or 'transparency' in img_copy.info:
                img_copy = img_copy.convert('RGBA'); bg = Image.new('RGB', img_copy.size, (255, 255, 255)); bg.paste(img_copy, mask=img_copy.split()[-1]); img_copy = bg
            else: img_copy = img_copy.convert('RGB')
            img_copy.thumbnail(MAX_PREVIEW_SIZE, Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(img_copy)
            self.preview_label.imgtk = imgtk; self.preview_label.config(image=imgtk)
        except Exception as e: print(f"Img Disp Err: {e}"); self.show_placeholder_preview("Error Displaying Image")

    def play_video_frame(self):
        """Reads and displays one frame of the video."""
        if self.cap is None or not self.cap.isOpened() or self.current_selection_page_index is None: self._stop_preview(); return
        ret, frame = self.cap.read()
        if ret:
            try:
                h, w, _ = frame.shape; scale = min(MAX_PREVIEW_WIDTH/w, MAX_PREVIEW_HEIGHT/h) if w > 0 and h > 0 else 1
                if scale < 1: new_w, new_h = int(w * scale), int(h * scale); frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB); img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img); self.preview_label.imgtk = imgtk; self.preview_label.config(image=imgtk)
                fps = self.cap.get(cv2.CAP_PROP_FPS); delay = int(1000 / fps) if fps and fps > 0 else 33 # ms per frame
                self.preview_job = self.after(delay, self.play_video_frame)
            except (cv2.error, tk.TclError, ValueError) as e: print(f"Video Frame Err: {e}"); self._stop_preview() # Stop on error
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
            self.preview_job = self.after(10, self.play_video_frame) # Small delay before restart

    def show_placeholder_preview(self, text="No Preview"):
         """Displays a placeholder in the preview area."""
         try:
            placeholder = Image.new("RGB", (MAX_PREVIEW_WIDTH//2, MAX_PREVIEW_HEIGHT//2), color='grey')
            draw = ImageDraw.Draw(placeholder); lines = text.split('\n'); y_text = 10
            font_to_use = self.placeholder_font if self.placeholder_font else None
            for line in lines: draw.text((10, y_text), line, fill='white', font=font_to_use); y_text += 15
            imgtk = ImageTk.PhotoImage(placeholder); self.preview_label.imgtk = imgtk; self.preview_label.config(image=imgtk)
         except Exception as e: print(f"Placeholder Err: {e}"); self.preview_label.imgtk=None; self.preview_label.config(image=None, text=text, fg="white")

    # --- Info Label ---
    def update_info_label(self):
        """Updates the information display panel based on current selection."""
        if self.current_selection_page_index is None: self.info_label.config(text="No item selected."); return
        try:
            global_idx = self.current_page_indices[self.current_selection_page_index]
            info = self.current_page_info.get(global_idx)
            if info:
                display_info = info.copy()
                # Get current classification using GLOBAL index
                classification = self.media_classifications.get(global_idx, "None")
                display_info["Classification"] = classification
                key_order = ["File", "Type", "Classification", "Dimensions", "Resolution", "FPS", "Duration (s)", "Frames", "Size (KB)"]
                info_text = f"Index: {global_idx} (Page: {self.current_page}, Item: {self.current_selection_page_index+1})\n" # Context info
                info_text += "\n".join(f"{k}: {display_info[k]}" for k in key_order if k in display_info and display_info[k] not in [None, "N/A", "Unknown", "Error"]) # Filter less useful info
                self.info_label.config(text=info_text)
            else: self.info_label.config(text="No media info available.")
        except IndexError: self.info_label.config(text="Error retrieving info.")

    # --- Marking and Classification ---
    def toggle_mark_current(self, event=None):
        """Toggles the 'marked' state for the currently selected item."""
        if self.current_selection_page_index is None: return
        page_idx = self.current_selection_page_index
        try:
            global_idx = self.current_page_indices[page_idx]
            mark_label_widget = self.marked_labels.get(page_idx)
            if not mark_label_widget: return # Label not found

            # Get inner label for positioning overlay
            label_widget_for_pos = self.thumbnail_widgets[page_idx].winfo_children()[0]

            if global_idx in self.marked_indices:
                self.marked_indices.remove(global_idx)
                mark_label_widget.place_forget()
                # print(f"Unmarked Global Index: {global_idx}")
            else:
                self.marked_indices.add(global_idx)
                mark_label_widget.place(in_=label_widget_for_pos, relx=0, rely=1.0, anchor='sw')
                # print(f"Marked Global Index: {global_idx}")
        except (IndexError, KeyError, tk.TclError) as e:
            print(f"Error toggling mark for page index {page_idx}: {e}")

    def classify_current_item(self, event, classification_num):
        """Assigns or removes classification (Low/Medium/High)."""
        if self.current_selection_page_index is None: return
        page_idx = self.current_selection_page_index
        try:
            global_idx = self.current_page_indices[page_idx]
            class_label_widget = self.classification_labels.get(page_idx)
            if not class_label_widget: return

            label_widget_for_pos = self.thumbnail_widgets[page_idx].winfo_children()[0]

            if classification_num == 0: # Remove classification
                if global_idx in self.media_classifications:
                    del self.media_classifications[global_idx]
                    class_label_widget.place_forget()
                    # print(f"Removed classification for Global Index: {global_idx}")
            elif classification_num in self.classification_map: # Assign 1, 2, or 3
                class_value = self.classification_map[classification_num]
                self.media_classifications[global_idx] = class_value
                class_label_widget.config(text=f"{class_value}")
                class_label_widget.place(in_=label_widget_for_pos, relx=1.0, rely=1.0, anchor='se')
                # print(f"Assigned '{class_value}' to Global Index: {global_idx}")
            else: return # Ignore invalid numbers

            self.update_info_label() # Update info panel display

        except (IndexError, KeyError, tk.TclError) as e:
             print(f"Error classifying page index {page_idx}: {e}")

    # --- Configurable Items/Page & View All ---
    def apply_items_per_page(self, show_confirmation=True):
        """Applies the items per page setting from the entry."""
        if self.view_all_mode.get():
             messagebox.showwarning("View All Active", "Cannot change items per page while 'View All' is active.")
             return False # Indicate failure
        try:
            new_val = int(self.config_items_per_page.get()) # Use get() on IntVar
            if new_val <= 0:
                raise ValueError("Items per page must be positive.")
            # Optional: Add a reasonable upper limit?
            if new_val > 5000: # Example limit
                 if not messagebox.askyesno("High Value Warning", f"Setting items per page to {new_val} might be very slow. Continue?"):
                     raise ValueError("Value considered too high by user.")

        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Invalid items per page value: {e}\nPlease enter a positive integer.")
            self.config_items_per_page.set(self.items_per_page) # Reset entry to current value
            return False # Indicate failure

        if new_val != self.items_per_page:
            if not self.all_media_files: # No files loaded yet, just set it
                self.items_per_page = new_val
                self._original_items_per_page = new_val
                print(f"Items per page set to {new_val} (before loading).")
                return True

            # Files are loaded, confirm reload
            if show_confirmation:
                confirm = messagebox.askyesno("Apply Setting",
                                            f"Set items per page to {new_val} and reload the current folder?\n"
                                            f"(Marks and classifications will be preserved)")
                if not confirm:
                    self.config_items_per_page.set(self.items_per_page) # Revert entry
                    return False

            self.set_status(f"Applying items per page: {new_val}...")
            self.items_per_page = new_val
            self._original_items_per_page = new_val # Keep track if user toggles view all later

            self._recalculate_pagination() # Update total pages

            # Determine which page to load - try to keep current items visible
            new_target_page = 1
            current_global_idx = None
            if self.current_selection_page_index is not None:
                 try: # Find global index of currently selected item
                     current_global_idx = self.current_page_indices[self.current_selection_page_index]
                 except IndexError: pass # Ignore if selection index is bad

            if current_global_idx is not None:
                 # Calculate which page this index falls on with the new setting
                 new_target_page = math.floor(current_global_idx / self.items_per_page) + 1
                 new_target_page = max(1, min(new_target_page, self.total_pages)) # Clamp

            # Make sure target page is valid if calculation failed or no selection
            if not (1 <= new_target_page <= self.total_pages): new_target_page = 1

            self.load_page(new_target_page) # Reload data for the calculated page
        return True # Indicate success

    def _recalculate_pagination(self):
        """Recalculates total pages based on total items and items_per_page."""
        if self.total_items > 0 and self.items_per_page > 0:
            self.total_pages = math.ceil(self.total_items / self.items_per_page)
        else:
            self.total_pages = 0
        # Clamp current page if it becomes invalid due to change in total pages
        if self.current_page > self.total_pages and self.total_pages > 0:
            self.current_page = self.total_pages
        elif self.total_pages == 0:
            self.current_page = 1 # Or 0? Let's use 1 as standard.
        print(f"Recalculated: Total Pages = {self.total_pages}, Current Page = {self.current_page}, Items/Page = {self.items_per_page}")

    def toggle_view_all(self):
        """Handles the View All checkbox state change."""
        if not self.all_media_files:
            messagebox.showinfo("No Folder Loaded", "Please load a folder first.")
            self.view_all_mode.set(False); return

        is_activating_view_all = self.view_all_mode.get()

        if is_activating_view_all:
            warning_msg = (f"WARNING: Viewing all items ({self.total_items}) at once may cause severe performance "
                           f"issues or high memory usage.\n\nDo you want to proceed?")
            if messagebox.askyesno("Performance Warning", warning_msg, icon='warning'):
                self.set_status("Attempting to load all items...")
                self._original_items_per_page = self.items_per_page
                self.items_per_page = max(1, self.total_items)
                self._recalculate_pagination() # Should result in 1 page
                self.load_page(1)
                self.set_status(f"View All Mode: Displaying {self.total_items} items.")
            else:
                self.view_all_mode.set(False); return # User cancelled
        else: # Deactivating view all
            self.set_status("Restoring paginated view...")
            self.items_per_page = self._original_items_per_page
            self.config_items_per_page.set(self.items_per_page)
            self._recalculate_pagination()

            target_page = 1 # Default page to return to
            current_global_idx = None
            if self.current_selection_page_index is not None:
                 try: # Find global index of currently selected item from the 'view all' page
                     current_global_idx = self.current_page_indices[self.current_selection_page_index]
                 except IndexError: pass

            if current_global_idx is not None: # Calculate target page based on selection
                 target_page = math.floor(current_global_idx / self.items_per_page) + 1
                 target_page = max(1, min(target_page, self.total_pages))

            if not (1 <= target_page <= self.total_pages): target_page = 1 # Safety clamp
            self.load_page(target_page)
            self.set_status(f"Restored paginated view. Items/Page: {self.items_per_page}.")

        self._update_ui_controls_state() # Update button states etc.

    def _update_ui_controls_state(self):
        """Enables/disables pagination and config controls based on mode."""
        is_view_all = self.view_all_mode.get()
        has_multiple_pages = self.total_pages > 1

        state_pagination = tk.NORMAL if has_multiple_pages and not is_view_all else tk.DISABLED
        state_config = tk.NORMAL if not is_view_all else tk.DISABLED
        # View all checkbox only makes sense if there are items
        state_view_all_cb = tk.NORMAL if self.total_items > 0 else tk.DISABLED

        # Update Pagination Buttons
        state_prev = state_pagination if self.current_page > 1 else tk.DISABLED
        state_next = state_pagination if self.current_page < self.total_pages else tk.DISABLED
        try:
            if hasattr(self, 'prev_page_btn'): self.prev_page_btn.config(state=state_prev)
            if hasattr(self, 'next_page_btn'): self.next_page_btn.config(state=state_next)
            if hasattr(self, 'page_label'):
                if self.total_items > 0:
                     page_info = f"Page {self.current_page} of {self.total_pages}"
                     if is_view_all: page_info = f"View All ({self.total_items} items)"
                     self.page_label.config(text=page_info)
                else:
                     self.page_label.config(text="Page - of -")

            # Update Config Controls
            if hasattr(self, 'items_per_page_entry'): self.items_per_page_entry.config(state=state_config)
            if hasattr(self, 'apply_items_btn'): self.apply_items_btn.config(state=state_config)
            # Update View All Checkbox itself
            if hasattr(self, 'view_all_checkbox'): self.view_all_checkbox.config(state=state_view_all_cb)

        except tk.TclError: pass # Ignore if widgets destroyed during update

    # --- Navigation ---
    def navigate_left(self, event=None):
        if self.current_selection_page_index is None:
            if self.current_page_indices: self.select_item(0); return
            else: return
        current_page_idx = self.current_selection_page_index
        if current_page_idx > 0: self.select_item(current_page_idx - 1)
        elif self.current_page > 1 and not self.view_all_mode.get(): self.go_to_previous_page(select_last=True)

    def navigate_right(self, event=None):
        if self.current_selection_page_index is None:
            if self.current_page_indices: self.select_item(0); return
            else: return
        current_page_idx = self.current_selection_page_index
        if current_page_idx < len(self.current_page_indices) - 1: self.select_item(current_page_idx + 1)
        elif self.current_page < self.total_pages and not self.view_all_mode.get(): self.go_to_next_page(select_first=True)

    def navigate_up(self, event=None):
        if self.current_selection_page_index is None:
            if self.current_page_indices: self.select_item(0); return
            else: return
        cols = getattr(self, 'current_columns', 1)
        if cols <= 0: cols = 1 # Safety
        target_page_idx = self.current_selection_page_index - cols
        if target_page_idx >= 0: self.select_item(target_page_idx)
        elif self.current_page > 1 and not self.view_all_mode.get():
             items_on_prev_page = self.items_per_page # Assume full page
             target_idx_on_prev = items_on_prev_page + target_page_idx # target_page_idx < 0
             self.go_to_previous_page(select_index=target_idx_on_prev)
        elif target_page_idx < 0: self.select_item(0) # Go to first item

    def navigate_down(self, event=None):
        if self.current_selection_page_index is None:
            if self.current_page_indices: self.select_item(0); return
            else: return
        cols = getattr(self, 'current_columns', 1)
        if cols <= 0: cols = 1 # Safety
        target_page_idx = self.current_selection_page_index + cols
        if target_page_idx < len(self.current_page_indices): self.select_item(target_page_idx)
        elif self.current_page < self.total_pages and not self.view_all_mode.get():
             current_col = self.current_selection_page_index % cols
             self.go_to_next_page(select_index=current_col) # Try same column, first row of next
        elif target_page_idx >= len(self.current_page_indices): self.select_item(len(self.current_page_indices) - 1) # Go to last item

    def go_to_previous_page(self, event=None, select_last=False, select_index=None):
        """Navigate to the previous page."""
        if self.current_page > 1 and not self.view_all_mode.get():
            target_page = self.current_page - 1
            self.load_page(target_page)
            # Selection logic *after* page load
            if self.current_page_indices: # Ensure page loaded successfully
                if select_last: self.select_item(len(self.current_page_indices) - 1)
                elif select_index is not None: self.select_item(min(max(0, select_index), len(self.current_page_indices) - 1))
                # Default: select_item(0) might be called within load_page

    def go_to_next_page(self, event=None, select_first=False, select_index=None):
        """Navigate to the next page."""
        if self.current_page < self.total_pages and not self.view_all_mode.get():
            target_page = self.current_page + 1
            self.load_page(target_page)
            if self.current_page_indices:
                if select_first: self.select_item(0)
                elif select_index is not None: self.select_item(min(max(0, select_index), len(self.current_page_indices) - 1))

    def _reset_ui_state(self):
        """Clears UI elements when no folder is loaded or folder is empty."""
        self.set_status("Resetting UI...")
        self.all_media_files = []; self.total_items = 0; self.current_page = 1; self.total_pages = 0
        self.current_page_indices = []; self.current_page_thumbnails.clear(); self.current_page_info.clear()
        self.current_selection_page_index = None
        self._stop_preview()
        self.preview_label.config(image=None); self.preview_label.imgtk = None
        self.info_label.config(text="Select a folder to begin.")
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.thumbnail_widgets = []; self.marked_labels.clear(); self.current_labels.clear(); self.classification_labels.clear()
        self.set_status("Select a folder to begin.")
        self.view_all_mode.set(False) # Ensure view all is off
        self._update_ui_controls_state() # Update button states

    # --- Organizing ---
    def organize_marked_items(self):
        """Organizes marked items into subfolders."""
        if not self.marked_indices: messagebox.showinfo("Info", "No items marked."); return

        dest_base_folder = filedialog.askdirectory(title="Select Base Destination Folder")
        if not dest_base_folder: return

        action_choice = messagebox.askquestion("Copy or Move?", "MOVE files? ('No' will COPY)", icon='warning', default='no')
        move_files = (action_choice == 'yes'); action_func = shutil.move if move_files else shutil.copy2
        action_gerund = "Moving" if move_files else "Copying"; action_past = "moved" if move_files else "copied"
        processed_count = 0; error_count = 0; errors = []; processed_global_indices = set()
        indices_to_process = sorted(list(self.marked_indices)) # Process in order

        self.set_status(f"{action_gerund} {len(indices_to_process)} marked items...")
        self.update_idletasks()

        for global_idx in indices_to_process:
             if global_idx >= len(self.all_media_files): continue # Safety check
             src_path = self.all_media_files[global_idx]
             if not os.path.exists(src_path): errors.append(f"Skip (Missing): {os.path.basename(src_path)}"); error_count += 1; continue

             base_name = os.path.basename(src_path)
             classification = self.media_classifications.get(global_idx)
             # Fetch info - needed for type classification
             item_info = self.current_page_info.get(global_idx) or self.get_item_info(src_path)
             item_type = item_info.get("Type", "Unknown")

             # --- Determine Destination ---
             type_subfolder = "Images" if item_type in ["Image", "GIF"] else "Videos" if item_type == "Video" else "Others"
             class_subfolder = classification if classification else "Unclassified"
             dest_folder = os.path.join(dest_base_folder, type_subfolder, class_subfolder)
             dest_path = os.path.join(dest_folder, base_name)

             try:
                 os.makedirs(dest_folder, exist_ok=True)
                 # Prevent self-move/copy
                 if os.path.abspath(src_path) == os.path.abspath(dest_path):
                     errors.append(f"Skip (Src=Dest): {base_name}"); error_count += 1; continue

                 # Handle existing file: rename with suffix
                 counter = 1; name, ext = os.path.splitext(base_name); final_dest_path = dest_path
                 while os.path.exists(final_dest_path):
                      final_dest_path = os.path.join(dest_folder, f"{name}_{counter}{ext}"); counter += 1
                 if final_dest_path != dest_path: print(f"Dest exists, renaming to: {os.path.basename(final_dest_path)}")

                 # print(f"{action_gerund} '{base_name}' to '{type_subfolder}/{class_subfolder}/{os.path.basename(final_dest_path)}'")
                 action_func(src_path, final_dest_path); processed_count += 1; processed_global_indices.add(global_idx)

             except Exception as e:
                 error_count += 1; errors.append(f"FAIL {action_gerund[:3]} {base_name}: {e}"); print(f"ERROR {action_gerund} {base_name}: {e}")

        # --- Reporting ---
        summary = f"{action_past.capitalize()} {processed_count} items.\n"
        if error_count > 0: summary += f"{error_count} errors/skips.\n";
        if errors: summary += "\nDetails:\n" + "\n".join(errors[:15]); # Show first 15 errors
        if len(errors) > 15: summary += "\n..."
        msg_func = messagebox.showwarning if error_count > 0 else messagebox.showinfo
        msg_func(f"Organizing Complete ({'with issues' if error_count > 0 else 'OK'})", summary)
        final_status = f"Organizing complete. {action_past.capitalize()} {processed_count} items, {error_count} errors."
        self.set_status(final_status)

        # --- Post-Action ---
        # Remove marks ONLY for successfully processed items
        self.marked_indices -= processed_global_indices

        # Refresh current page display to remove marks visually
        if hasattr(self, 'current_columns'): # Check if grid was ever built
            self.update_grid(self.current_columns)

        # If files were MOVED, the `all_media_files` list is now stale. Reload.
        if move_files and processed_count > 0:
            print("Files moved. Reloading folder content..."); self.set_status("Files moved. Reloading...")
            current_folder_path = self.current_folder # Store before potentially clearing
            if current_folder_path and os.path.isdir(current_folder_path):
                 self.load_media(current_folder_path) # Reload
            else:
                 self._reset_ui_state() # Clear if folder vanished


# --- Main Execution ---
if __name__ == '__main__':
    app = MediaGridApp()
    app.mainloop()
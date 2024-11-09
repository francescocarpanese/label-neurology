import tkinter as tk
from PIL import Image, ImageTk

# Initialize the main application window
root = tk.Tk()
root.title("Zoom and Pan Example")

# Load an example image and display it on a canvas
image_path = "/Users/nc-mbp-4564/Documents/neurology/example_img/test_1.png"  # Replace with your image path
img = Image.open(image_path)
img_width, img_height = img.size

# Canvas setup
canvas = tk.Canvas(root, width=800, height=600, bg="gray")
canvas.grid(row=0, column=0, sticky="nsew")

# Add scrollbars to the canvas
scroll_x = tk.Scrollbar(root, orient="horizontal", command=canvas.xview)
scroll_x.grid(row=1, column=0, sticky="ew")
scroll_y = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scroll_y.grid(row=0, column=1, sticky="ns")
canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

# Add the image to the canvas
img_tk = ImageTk.PhotoImage(img)
image_id = canvas.create_image(0, 0, anchor="nw", image=img_tk)
canvas.config(scrollregion=canvas.bbox(tk.ALL))

# Initial zoom factor and position variables
zoom_factor = 1.0
global start_x, start_y
start_x, start_y = 0, 0

# Zoom function using mouse wheel
def zoom(event):
    global zoom_factor, img_tk, image_id
    # Zoom online if control is pressed 
    if event.state == 8:
        # Determine the zoom direction (in or out)
        scale = 1.1 if event.delta > 0 else 0.9
        zoom_factor *= scale
        
        # Resize the image
        new_width = int(img_width * zoom_factor)
        new_height = int(img_height * zoom_factor)
        resized_img = img.resize((new_width, new_height))
        img_tk = ImageTk.PhotoImage(resized_img)
        
        # Update the image on the canvas
        canvas.itemconfig(image_id, image=img_tk)
        canvas.config(scrollregion=canvas.bbox(tk.ALL))

# Pan function using mouse drag
def start_pan(event):
    global start_x, start_y
    start_x, start_y = event.x, event.y

def pan(event):
    global start_x, start_y
    # Calculate the movement delta
    delta_x = event.x - start_x
    delta_y = event.y - start_y

    # Move the canvas
    canvas.scan_dragto(event.x, event.y, gain=1)
    
    # Update start positions
    start_x, start_y = event.x, event.y

# Function to perform 10x zoom
def zoom_10x():
    global zoom_factor, img_tk, image_id
    scale = 10
    zoom_factor *= scale
    
    # Resize the image
    new_width = int(img_width * zoom_factor)
    new_height = int(img_height * zoom_factor)
    resized_img = img.resize((new_width, new_height), Image.LANCZOS)
    img_tk = ImageTk.PhotoImage(resized_img)
    
    # Update the image on the canvas
    canvas.itemconfig(image_id, image=img_tk)
    canvas.config(scrollregion=canvas.bbox(tk.ALL))

# Bind zoom and pan events
canvas.bind("<MouseWheel>", zoom)      # For Windows and MacOS
canvas.bind("<ButtonPress-1>", start_pan)
canvas.bind("<B1-Motion>", pan)

# Add a button to perform 10x zoom
zoom_button = tk.Button(root, text="Zoom 10x", command=zoom_10x)
zoom_button.grid(row=2, column=0, sticky="ew")

# Run the application
root.mainloop()
import os
import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backend_bases import MouseButton
import pandas as pd
from pydicom import dcmread
import numpy as np

# Initialize the DataFrame to store the coordinates and selection status
coordinates_df = pd.DataFrame(columns=['x', 'y', 'size', 'selected'])

# Initialize variables to store the image list and current image index
image_names = []
current_image_index = 0
patient_folder_path = ""

# Variables for drag-and-drop
dragging = False
selected_square_index = None
default_square_size = 20  # Default size for the squares

# Function to get the current square size from the entry
def get_square_size():
    try:
        return int(square_size_entry.get())
    except ValueError:
        return default_square_size  # Return default size if input is invalid

# Function to select a folder
def select_folder():
    global image_names, current_image_index, patient_folder_path
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        patient_folder_path = folder_selected
        image_names = sorted(os.listdir(folder_selected))
        current_image_index = 0
        load_image(patient_folder_path, image_names[current_image_index])
        slider.config(to=len(image_names) - 1)
        slider.set(current_image_index)

# Function to load and display an image
def load_image(folder_path, image_name):
    global ax, canvas, coordinates_df
    ds = dcmread(os.path.join(folder_path, image_name))
    image_array = ds.pixel_array
    ax.clear()
    ax.imshow(image_array, cmap='gray')
    ax.set_title(f"Image: {image_name}")
    
    # Draw all squares, highlighting if selected
    for _, row in coordinates_df.iterrows():
        color = 'yellow' if row['selected'] else 'red'
        square = Rectangle((row['x'] - row['size'] / 2, row['y'] - row['size'] / 2), row['size'], row['size'],
                           linewidth=2, edgecolor=color, facecolor='none')
        ax.add_patch(square)
    canvas.draw()

# Function to handle mouse clicks, adding or selecting squares
def on_click(event):
    global coordinates_df, dragging, selected_square_index
    if event.button == MouseButton.LEFT and event.inaxes:
        x, y = event.xdata, event.ydata
        square_size = get_square_size()
        
        # Check if the click is near an existing square
        threshold_distance = square_size / 2  # Distance to consider a square selected
        for i, row in coordinates_df.iterrows():
            dist = np.sqrt((row['x'] - x) ** 2 + (row['y'] - y) ** 2)
            if dist < threshold_distance:
                # Toggle selection if not dragging, else start dragging
                coordinates_df.at[i, 'selected'] = not row['selected']
                selected_square_index = i
                dragging = coordinates_df.at[i, 'selected']
                load_image(patient_folder_path, image_names[current_image_index])
                return

        # Add a new square if no existing square was selected
        new_row = pd.DataFrame({'x': [x], 'y': [y], 'size': [square_size], 'selected': [False]})
        coordinates_df = pd.concat([coordinates_df, new_row], ignore_index=True)
        load_image(patient_folder_path, image_names[current_image_index])
        counter_label.config(text=f"Number of squares: {len(coordinates_df)}")

# Function to handle mouse motion for dragging
def on_motion(event):
    global coordinates_df, dragging, selected_square_index
    if dragging and event.inaxes and selected_square_index is not None:
        x, y = event.xdata, event.ydata
        # Update the selected square’s center coordinates
        coordinates_df.at[selected_square_index, 'x'] = x
        coordinates_df.at[selected_square_index, 'y'] = y
        load_image(patient_folder_path, image_names[current_image_index])

# Function to handle mouse release and stop dragging
def on_release(event):
    global dragging, selected_square_index
    dragging = False
    selected_square_index = None

# Function to move to the previous image
def previous_image():
    global current_image_index
    if current_image_index > 0:
        current_image_index -= 1
        load_image(patient_folder_path, image_names[current_image_index])
        slider.set(current_image_index)

# Function to move to the next image
def next_image():
    global current_image_index
    if current_image_index < len(image_names) - 1:
        current_image_index += 1
        load_image(patient_folder_path, image_names[current_image_index])
        slider.set(current_image_index)

# Function to update the image based on the slider value
def update_image(val):
    global current_image_index
    current_image_index = int(val)
    load_image(patient_folder_path, image_names[current_image_index])

# Function to delete selected squares
def delete_selected():
    global coordinates_df
    coordinates_df = coordinates_df[coordinates_df['selected'] == False].reset_index(drop=True)
    load_image(patient_folder_path, image_names[current_image_index])
    counter_label.config(text=f"Number of squares: {len(coordinates_df)}")

# Create the main application window
root = tk.Tk()
root.title("Interactive Plot with Square Marker")

# Create a frame for the buttons at the top
button_frame = tk.Frame(root)
button_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

# Add an entry for setting square size
tk.Label(button_frame, text="Square Size:").grid(row=0, column=0, padx=5, pady=5)
square_size_entry = tk.Entry(button_frame, width=5)
square_size_entry.insert(0, str(default_square_size))  # Set default square size
square_size_entry.grid(row=0, column=1, padx=5, pady=5)

# Create a button to select a folder
select_folder_button = tk.Button(button_frame, text="Select Folder", command=select_folder)
select_folder_button.grid(row=0, column=2, padx=5, pady=5)

# Create buttons to navigate images
previous_image_button = tk.Button(button_frame, text="Previous Image", command=previous_image)
previous_image_button.grid(row=0, column=3, padx=5, pady=5)
next_image_button = tk.Button(button_frame, text="Next Image", command=next_image)
next_image_button.grid(row=0, column=4, padx=5, pady=5)

# Create a button to delete selected squares
delete_button = tk.Button(button_frame, text="Delete Selected Squares", command=delete_selected)
delete_button.grid(row=0, column=5, padx=5, pady=5)

# Create a frame for the counter at the bottom
counter_frame = tk.Frame(root)
counter_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

# Create a label to display the counter
counter_label = tk.Label(counter_frame, text="Number of squares: 0")
counter_label.grid(row=0, column=0, padx=5, pady=5)

# Create a slider to move between images
slider = tk.Scale(root, from_=0, to=0, orient=tk.HORIZONTAL, command=update_image)
slider.grid(row=2, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

# Create a Matplotlib figure and axis
fig, ax = plt.subplots()
ax.set_title("Click on the plot to place a square")

# Embed the Matplotlib figure in the Tkinter window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=1, column=0, columnspan=2, sticky='nsew')

# Configure the grid to expand properly
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Connect the click, motion, and release events for drawing and moving squares
canvas.mpl_connect('button_press_event', on_click)
canvas.mpl_connect('motion_notify_event', on_motion)
canvas.mpl_connect('button_release_event', on_release)

# Start the Tkinter event loop
root.mainloop()
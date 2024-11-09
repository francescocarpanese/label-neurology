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
from tkinter import ttk
from datetime import datetime

CODE_VERSION = "0.0.1"

def init_dataframe():
    coordinates_df = pd.DataFrame(columns=['x', 'y', 'size', 'selected', 'type', 'active_indices',
                                           'patient_folder', 'creation_timestamp', 'file_name', 'code_version', 'series_type',
                                           'instance_number',
                                           ])
    return coordinates_df

# Initialize the DataFrame to store the coordinates and selection status
global coordinates_df
coordinates_df = init_dataframe()

series_type_df = pd.DataFrame({'file_name': [], 'series_type': [], 'instance_number': []})

# Initialize variables to store the image list and current image index
image_names = []
current_image_index = 0
patient_folder_path = ""
current_series_type = ""
current_image_name = ""
current_instance_number = ""

# Variables for drag-and-drop
dragging = False
selected_square_index = None
default_square_size = 20  # Default size for the squares


# Function to retrieve the different series types and acquisition times of images in the dataset
def get_series_description(folder_path):
    file_list = []
    series_list = []
    instance_list = []
    
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            try:
                ds = dcmread(file_path)
                if not hasattr(ds, 'pixel_array'):
                    continue
                # Retrieve SeriesDescription and AcquisitionTime
                series_description = ds.SeriesDescription if 'SeriesDescription' in ds else 'Unknown'
                instance_number = ds.InstanceNumber if 'InstanceNumber' in ds else 'Unknown'
                
                # Append information to lists
                file_list.append(file_name)
                series_list.append(series_description)
                instance_list.append(instance_number)
                    
            except Exception as e:
                print(f"Error reading {file_name}: {e}")
    
    # Create the DataFrame with datetime-compatible acquisition time
    df = pd.DataFrame({
        'file_name': file_list,
        'series_type': series_list,
        'instance_number': instance_list,
    })
    return df


# Function to get the current square size from the entry
def get_square_size():
    try:
        return int(square_size_entry.get())
    except ValueError:
        return default_square_size  # Return default size if input is invalid
    

# Function to select a folder
def select_folder():
    global image_names, current_image_index, patient_folder_path, coordinates_df, series_type_df, current_series_type, current_image_name, current_instance_number
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        patient_folder_path = folder_selected
        current_image_index = 0
        coordinates_df = init_dataframe()
        series_type_df = get_series_description(folder_selected)
        current_series_type = series_type_df['series_type'].iloc[0]
        image_names = series_type_df[series_type_df['series_type'] == current_series_type].sort_values('instance_number')['file_name'].tolist()
        current_image_name = image_names[current_image_index]        
        load_image(patient_folder_path, image_names[current_image_index])
        slider.config(to=len(image_names) - 1)
        slider.set(current_image_index)
        series_type_combo.config(text=current_series_type, values=list(series_type_df['series_type'].unique()))
        series_type_combo.set(current_series_type)

# Function to handle series type selection
def on_series_type_selected(event):
    global image_names, current_image_index, current_series_type, series_type_df, current_image_name
    selected_series_type = series_type_combo.get()
    if selected_series_type:
        current_series_type = selected_series_type
        image_names = series_type_df[series_type_df['series_type'] == current_series_type].sort_values('instance_number')['file_name'].tolist()
        current_image_index = 0
        current_image_name = image_names[current_image_index]
        load_image(patient_folder_path, image_names[current_image_index])
        slider.config(to=len(image_names) - 1)
        slider.set(current_image_index)

# Get color depending on type
def get_color(row):
    if row['selected']:
        return 'yellow'
    else:
        return row['type']
        
# Get linestyle depending is_saved
def get_linestyle(row):
    if len(row['active_indices']) >1:
        # In this case the corrent square is part of more than one slice
        return ':'
    return '-'

# Plot all the squares on the image of a given active index
def plot_squares():
    global ax, canvas, coordinates_df, current_image_index, current_image_name, series_type_df
    # Draw all squares, highlighting if selected and if the current index is part of active indices
    for _, row in coordinates_df.iterrows():
        current_instance_number = series_type_df[series_type_df['file_name'] == current_image_name]['instance_number'].values[0]
        if current_instance_number in row['active_indices']:
            color = get_color(row)
            linestyle = get_linestyle(row)
            square = Rectangle((row['x'] - row['size'] / 2, row['y'] - row['size'] / 2), row['size'], row['size'],
                               linewidth=2, edgecolor=color, facecolor='none', linestyle=linestyle)
            ax.add_patch(square)

# Function to load and display an image
def load_image(folder_path, image_name):
    global ax, canvas, coordinates_df, current_image_index
    ds = dcmread(os.path.join(folder_path, image_name))
    
    # Plot the image 
    image_array = ds.pixel_array
    ax.clear()
    ax.imshow(image_array, cmap='gray')
    ax.set_title(f"Image: {image_name}")
    
    # Plot all annotation    
    plot_squares()
    
    # Draw the canvas
    canvas.draw()

# Function to handle mouse clicks, adding or selecting squares
def on_click(event):
    global coordinates_df, dragging, selected_square_index
    if event.button == MouseButton.LEFT and event.inaxes:
        x, y = event.xdata, event.ydata
        square_size = get_square_size()
        

        # Get current instance number to add to the active indices
        current_instance_number = series_type_df[series_type_df['file_name'] == current_image_name]['instance_number'].values[0]        
        
        # Check if the click is near an existing square
        #threshold_distance = square_size / 2  # Distance to consider a square selected
        for i, row in coordinates_df.iterrows():
            if abs((row['x'] - x))< square_size/2 and abs((row['y'] - y)) <  square_size/2  and current_instance_number in row['active_indices']:
                # Toggle selection if not dragging, else start dragging
                coordinates_df.at[i, 'selected'] = not row['selected']
                selected_square_index = i
                dragging = coordinates_df.at[i, 'selected']
                load_image(patient_folder_path, image_names[current_image_index])
                update_label_counts()
                return
            

        # Add a new square if no existing square was selected
        new_row = pd.DataFrame(
            {
                'x': [x],
                'y': [y],
                'size': [square_size],
                'selected': [False],
                'type': [label_type.get()],
                'active_indices': [[current_instance_number]],
                'patient_folder': [patient_folder_path],
                'creation_timestamp': [pd.Timestamp.now()],
                'file_name': [image_names[current_image_index]],
                'code_version': [CODE_VERSION]
                },
            )
        coordinates_df = pd.concat([coordinates_df, new_row], ignore_index=True)
        load_image(patient_folder_path, image_names[current_image_index])
        update_label_counts()


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
        unselect_all()
        load_image(patient_folder_path, image_names[current_image_index])
        slider.set(current_image_index)
        update_label_counts()

# Function to move to the next image
def next_image():
    global current_image_index
    if current_image_index < len(image_names) - 1:
        current_image_index += 1
        unselect_all()
        load_image(patient_folder_path, image_names[current_image_index])
        slider.set(current_image_index)
        update_label_counts()

# Function to update the image based on the slider value
def update_image(val):
    global current_image_index
    current_image_index = int(val)
    unselect_all()
    load_image(patient_folder_path, image_names[current_image_index])

# Function to delete selected squares
def delete_selected():
    global coordinates_df, current_image_index
    
    # Remove the current instance number from active_indices of all selected squares
    current_instance_number = series_type_df[series_type_df['file_name'] == current_image_name]['instance_number'].values[0]
    coordinates_df.loc[coordinates_df['selected'], 'active_indices'] = coordinates_df.loc[coordinates_df['selected'], 'active_indices'].apply(lambda x: [i for i in x if i != current_instance_number])
    
    # Remove rows where active_indices is empty
    coordinates_df = coordinates_df[coordinates_df['active_indices'].map(len) > 0].reset_index(drop=True)
    
    # Reload the image to reflect changes
    unselect_all()
    load_image(patient_folder_path, image_names[current_image_index])
    update_label_counts()


# Function to save labels to a CSV file
def save_labels_to_file():
    global coordinates_df
    # Open a file dialog to select the folder and specify the file name
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        # Save the DataFrame to the specified CSV file
        coordinates_df.to_csv(file_path, index=False)
        tk.messagebox.showinfo("Save Labels", f"Labels saved to {file_path}")
        
# Function to load labels from a CSV file
def load_labels_from_file():
    global coordinates_df
    # Open a file dialog to select the CSV file
    file_path = filedialog.askopenfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        # Load the DataFrame from the specified CSV file
        coordinates_df = pd.read_csv(file_path)
        # Convert 'active_indices' from string representation of list to actual list
        coordinates_df['active_indices'] = coordinates_df['active_indices'].apply(eval)
        load_image(patient_folder_path, image_names[current_image_index])
        update_label_counts()
        
# Function to delete all labels in the current slice
def delete_all_labels_slides():
    if tk.messagebox.askyesno("Confirm Delete", "Are you sure you want to delete all labels in the current slice?"):
        global coordinates_df, current_image_index, current_image_name
        current_instance_number = series_type_df[series_type_df['file_name'] == current_image_name]['instance_number'].values[0]
        
        # Remove the current image index from active_indices of all squares
        coordinates_df['active_indices'] = coordinates_df['active_indices'].apply(lambda x: [i for i in x if i != current_instance_number])
        
        # Remove rows where active_indices is empty
        coordinates_df = coordinates_df[coordinates_df['active_indices'].map(len) > 0].reset_index(drop=True)
        
        # Reload the image to reflect changes
        load_image(patient_folder_path, image_names[current_image_index])
        update_label_counts()
        # Function to show a confirmation dialog before deleting all labels

# Function to load labels from the previous slice
def load_labels_from_previous_slice():
    global coordinates_df, current_image_index, current_image_name, series_type_df
    if current_image_index > 0:
        previous_index = current_image_index - 1
        
#        previous_instance_number = series_type_df[series_type_df['file_name'] == image_names[previous_index]]['instance_number'].values[0]
        # Update the active indices of the existing rows that contain the previous index
        coordinates_df.loc[coordinates_df['active_indices'].apply(lambda x: previous_index in x), 'active_indices'] = coordinates_df.loc[coordinates_df['active_indices'].apply(lambda x: previous_index in x), 'active_indices'].apply(lambda x: x + [current_image_index])
        unselect_all()
        load_image(patient_folder_path, image_names[current_image_index])
        update_label_counts()

# Create function to unselect all squares
def unselect_all():
    global coordinates_df
    coordinates_df['selected'] = False
    load_image(patient_folder_path, image_names[current_image_index])


# --------------------- Layout ---------------------------------

# Create the main application window
root = tk.Tk()
root.title("Interactive Plot with Square Marker")


## ---  Menu Frame
# Create a frame for the custom menu bar
menu_frame = tk.Frame(root, bg="lightgrey")
menu_frame.grid(row=0, column=0, columnspan=2, sticky='ew')

# Create "File" menu button
file_menu_button = tk.Menubutton(menu_frame, text="File", bg="lightgrey", relief="raised")
file_menu_button.pack(side="left")

# Create "File" menu
file_menu = tk.Menu(file_menu_button, tearoff=0)
file_menu.add_command(label="Open Images from Folder", command=select_folder)
file_menu.add_command(label="Save Labels to File", command=save_labels_to_file)
file_menu.add_command(label="Load Labels from File", command=load_labels_from_file)
file_menu.add_command(label="Export images with Labels to File", state="disabled")
file_menu.add_command(label="Save Report to File", command=root.quit, state="disabled")
file_menu_button.config(menu=file_menu)

## -- Image frame
# Create a Matplotlib figure and axis
fig, ax = plt.subplots()
ax.set_title("Click on the plot to place a square")

# Create a Tkinter canvas to embed the Matplotlib figure
tk_canvas = tk.Canvas(root, width=1200, height=800, bg="gray")
tk_canvas.grid(row=1, column=0, columnspan=2, sticky="nsew")

# Embed the Matplotlib figure in the Tkinter canvas
canvas = FigureCanvasTkAgg(fig, master=tk_canvas)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill=tk.BOTH, expand=True)

# Add scrollbars to the Tkinter canvas
scroll_x = tk.Scrollbar(root, orient="horizontal", command=tk_canvas.xview)
scroll_x.grid(row=2, column=0, sticky="ew")
scroll_y = tk.Scrollbar(root, orient="vertical", command=tk_canvas.yview)
scroll_y.grid(row=1, column=2, sticky="ns")
tk_canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

# Configure the scroll region of the Tkinter canvas
tk_canvas.create_window((0, 0), window=canvas_widget, anchor="nw")
tk_canvas.config(scrollregion=tk_canvas.bbox(tk.ALL))


## -- Interaction frame

# Create a frame for the buttons at the top
button_frame = tk.Frame(root)
button_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

# Create buttons to navigate images
previous_image_button = tk.Button(button_frame, text="Previous Image", command=previous_image)
previous_image_button.grid(row=0, column=0, padx=5, pady=5)

# Create a slider to move between images
slider = tk.Scale(button_frame, from_=0, to=0, orient=tk.HORIZONTAL, command=update_image)
slider.grid(row=0, column=1, columnspan=2, sticky='ew', padx=5, pady=5)

next_image_button = tk.Button(button_frame, text="Next Image", command=next_image)
next_image_button.grid(row=0, column=3, padx=5, pady=5)

# Create dropdown to select the series type
series_type_combo = ttk.Combobox(button_frame, values=[], state='readonly', width=20)
series_type_combo.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

# Create a vertical separator spanning multiple rows
ttk.Separator(button_frame, orient='vertical').grid(row=0, column=4, rowspan=2, sticky='ns', padx=5, pady=5)

# Add an entry for setting square size
tk.Label(button_frame, text="Square Size:").grid(row=0, column=5, padx=0, pady=0)
square_size_entry = tk.Entry(button_frame, width=5)
square_size_entry.insert(0, str(default_square_size))  # Set default square size
square_size_entry.grid(row=0, column=6, padx=0, pady=0)

# Create dropdown to select the type of label
label_type = ttk.Combobox(button_frame, values=['green', 'red', 'blue'], state='readonly', width=5)
label_type.set('green')
label_type.grid(row=1, column=5)

# Create buttons to navigate images
previous_image_button = tk.Button(button_frame, text="Delete selected Labels", command=delete_selected)
previous_image_button.grid(row=0, column=7, padx=0, pady=0)

# Create buttons to navigate images
clear_slice_button = tk.Button(button_frame, text="Clear current slice", command=delete_all_labels_slides)
clear_slice_button.grid(row=1, column=7, padx=0, pady=0)

# Create buttons to navigate images
load_previous_slice_button = tk.Button(button_frame, text="Load Labels from previous slice", command=load_labels_from_previous_slice)
load_previous_slice_button.grid(row=0, column=8, padx=0, pady=0)

## -- Create a horizontal separator
ttk.Separator(root, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

## -- Create a frame for information on the slide

## -- Bottom frame for information
# Create a frame for the counter at the bottom
counter_frame = tk.Frame(root)
counter_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

# Create a label to display the counter
green_label_count = tk.Label(counter_frame, text="Green Labels in slice: 0")
green_label_count.grid(row=0, column=1, padx=5, pady=5)

red_label_count = tk.Label(counter_frame, text="Red Total Labels in slice: 0")
red_label_count.grid(row=0, column=2, padx=5, pady=5)

blue_label_count = tk.Label(counter_frame, text="Blue Total Labels in slice: 0")
blue_label_count.grid(row=0, column=3, padx=5, pady=5)

## -- Create a horizontal separator
ttk.Separator(root, orient='horizontal').grid(row=6, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

## -- Bottom frame for information on the total number of squares
# Create a frame for the total counter at the bottom
total_counter_frame = tk.Frame(root)
total_counter_frame.grid(row=7, column=0, columnspan=2, padx=5, pady=5)

# Create labels to display the total counter
total_green_label_count = tk.Label(total_counter_frame, text="Total Green Labels: 0")
total_green_label_count.grid(row=0, column=1, padx=5, pady=5)

total_red_label_count = tk.Label(total_counter_frame, text="Total Red Labels: 0")
total_red_label_count.grid(row=0, column=2, padx=5, pady=5)

total_blue_label_count = tk.Label(total_counter_frame, text="Total Blue Labels: 0")
total_blue_label_count.grid(row=0, column=3, padx=5, pady=5)

# Function to update the total label counts
def update_label_counts():
    tot_green_count = len(coordinates_df[coordinates_df['type'] == 'green'])
    tot_red_count = len(coordinates_df[coordinates_df['type'] == 'red'])
    tot_blue_count = len(coordinates_df[coordinates_df['type'] == 'blue'])
    
    total_green_label_count.config(text=f"Total Green Labels: {tot_green_count}")
    total_red_label_count.config(text=f"Total Red Labels: {tot_red_count}")
    total_blue_label_count.config(text=f"Total Blue Labels: {tot_blue_count}")

    green_count = len(coordinates_df[(coordinates_df['type'] == 'green') & (coordinates_df['active_indices'].apply(lambda x: current_image_index in x))])
    red_count = len(coordinates_df[(coordinates_df['type'] == 'red') & (coordinates_df['active_indices'].apply(lambda x: current_image_index in x))])
    blue_count = len(coordinates_df[(coordinates_df['type'] == 'blue') & (coordinates_df['active_indices'].apply(lambda x: current_image_index in x))])
    
    green_label_count.config(text=f"Green Labels in slice: {green_count}")
    red_label_count.config(text=f"Red Total Labels in slice: {red_count}")
    blue_label_count.config(text=f"Blue Total Labels in slice: {blue_count}")


# Configure the grid to expand properly
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Connect the click, motion, and release events for drawing and moving squares
canvas.mpl_connect('button_press_event', on_click)
canvas.mpl_connect('motion_notify_event', on_motion)
canvas.mpl_connect('button_release_event', on_release)
# Bind the series type combo box to the selection function
series_type_combo.bind("<<ComboboxSelected>>", on_series_type_selected)

# Start the Tkinter event loop
root.mainloop()
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
from tkinter import simpledialog
import threading
import time


CODE_VERSION = "0.0.1"

def init_dataframe():
    coordinates_df = pd.DataFrame(columns=['x', 'y', 'size', 'selected', 'label_type', 'active_instance_numbers',
                                           'patient_folder', 'creation_timestamp', 'code_version', 'series_type',
                                           'user_name'])
    return coordinates_df

state = {
    'current_image_idx': 0,
    'patient_folder_path': "",
    'current_series_type': "",
    'current_image_name': "",
    'coordinates_df': init_dataframe(),
    'series_type_df': pd.DataFrame({'file_name': [], 'series_type': [], 'instance_number': []}),
    "current_series_type_df": pd.DataFrame({'file_name': [], 'series_type': [], 'instance_number': []}),
}


# Variables for drag-and-drop
dragging = False
selected_square_index = None
default_square_size = 20  # Default size for the squares
scale_factor = 1  # Factor to scale the image by
user_name = ""
last_save_time = datetime.now()

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
                instance_number = int(ds.InstanceNumber) if 'InstanceNumber' in ds else 'Unknown'
                
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

def get_instance_number(file_name):
    return state['series_type_df'][state['series_type_df']['file_name'] == file_name]['instance_number'].values[0]


def set_state_from_series_type(series_type):
    state['current_series_type'] = series_type
    state['current_series_type_df'] = state['series_type_df'][state['series_type_df']['series_type'] == series_type].sort_values(by='instance_number')
    state['current_image_name'] = state['current_series_type_df']['file_name'].iloc[0]
    state['current_image_idx'] = 0

# Function to select a folder
def select_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        # Set state
        state['patient_folder_path'] = folder_selected
        state['coordinates_df'] = init_dataframe()
        state['series_type_df'] = get_series_description(folder_selected)
        set_state_from_series_type(state['series_type_df']['series_type'].iloc[0])
        # Update the GUI
        load_image()
        slider.config(to=state['current_series_type_df'].shape[0] - 1)
        slider.set(state['current_image_idx'])
        series_type_combo.config(text=state['current_series_type'], values=list(state['series_type_df']['series_type'].unique()))
        series_type_combo.set(state['current_series_type'])

# Function to handle series label_type selection
def on_series_type_selected(event):
    selected_series_type = series_type_combo.get()
    if selected_series_type:
        set_state_from_series_type(selected_series_type)
        load_image()
        slider.config(to=state['current_series_type_df'].shape[0] - 1)
        slider.set(state['current_image_idx'])

# Get color depending on label_type
def get_color(row):
    if row['selected']:
        return 'yellow'
    else:
        return row['label_type']
        
# Get linestyle depending is_saved
def get_linestyle(row):
    if len(row['active_instance_numbers']) >1:
        # In this case the corrent square is part of more than one slice
        return ':'
    return '-'

# Plot all the squares on the image of a given active index
def plot_squares():
    global ax, canvas
    for _, row in state['coordinates_df'].iterrows():
        current_instance_number = get_instance_number(state['current_image_name'])
        if current_instance_number in row['active_instance_numbers'] and row['series_type'] == state['current_series_type']:
            color = get_color(row)
            linestyle = get_linestyle(row)
            square = Rectangle((row['x'] - row['size'] / 2, row['y'] - row['size'] / 2), row['size'], row['size'],
                               linewidth=2, edgecolor=color, facecolor='none', linestyle=linestyle)
            ax.add_patch(square)

# Function to load and display an image
def load_image():
    image_file_path = os.path.join(state['patient_folder_path'], state['current_image_name'])

    # Get image
    ds = dcmread(image_file_path)
    
    # Plot the image 
    image_array = ds.pixel_array
    ax.clear()
    ax.imshow(image_array, cmap='gray')
    ax.set_title(f"Image: {state['current_image_name']}")

    # Plot all annotation    
    plot_squares()
    update_label_counts()

    # Draw the canvas
    canvas.draw()


# Function to handle mouse clicks, adding or selecting squares
def on_click(event):
    global dragging, selected_square_index
    if event.button == MouseButton.LEFT and event.inaxes:
        x, y = event.xdata, event.ydata
        square_size = get_square_size()
        current_instance_number = get_instance_number(state['current_image_name'])
        
        # Check if the click is near an existing square
        #threshold_distance = square_size / 2  # Distance to consider a square selected
        for i, row in state['coordinates_df'].iterrows():
            if abs((row['x'] - x))< square_size/2 and abs((row['y'] - y)) <  square_size/2  and current_instance_number in row['active_instance_numbers']:
                # Toggle selection if not dragging, else start dragging
                state['coordinates_df'].at[i, 'selected'] = not row['selected']
                selected_square_index = i
                dragging = state['coordinates_df'].at[i, 'selected']
                load_image()
                update_label_counts()
                return
            

        # Add a new square if no existing square was selected
        new_row = pd.DataFrame(
            {
                'x': [x],
                'y': [y],
                'size': [square_size],
                'selected': [False],
                'label_type': [label_type.get()],
                'active_instance_numbers': [[current_instance_number]],
                'patient_folder': [state['patient_folder_path']],
                'creation_timestamp': [pd.Timestamp.now()],
                'code_version': [CODE_VERSION],
                'series_type': [state['current_series_type']],
                'user_name': [user_name],
                },
            )
        state['coordinates_df'] = pd.concat([state['coordinates_df'], new_row], ignore_index=True)
        load_image()
        update_label_counts()


# Function to handle mouse motion for dragging
def on_motion(event):
    global coordinates_df, dragging, selected_square_index
    if dragging and event.inaxes and selected_square_index is not None:
        x, y = event.xdata, event.ydata
        # Update the selected square’s center coordinates
        state['coordinates_df'].at[selected_square_index, 'x'] = x
        state['coordinates_df'].at[selected_square_index, 'y'] = y
        load_image() 

# Function to handle mouse release and stop dragging
def on_release(event):
    global dragging, selected_square_index
    dragging = False
    selected_square_index = None

# Function to move to the previous image
def previous_image():
    min_value = slider.cget('from')
    if state['current_image_idx'] > min_value:
        state['current_image_idx'] -= 1
        state['current_image_name'] = state['current_series_type_df']['file_name'].iloc[state['current_image_idx']]
        unselect_all()
        load_image()
        slider.set(state['current_image_idx'])
        update_label_counts()

# Function to move to the next image
def next_image():
    # Get the length of the slider
    max_value = slider.cget('to')
    
    if state['current_image_idx'] < max_value:
        state['current_image_idx'] += 1
        state['current_image_name'] = state['current_series_type_df']['file_name'].iloc[state['current_image_idx']]
        unselect_all()
        load_image()
        slider.set(state['current_image_idx'])
        update_label_counts()

# Function to update the image based on the slider value
def update_image_slider(val):
    state['current_image_idx'] = int(val)
    state['current_image_name'] = state['current_series_type_df']['file_name'].iloc[state['current_image_idx']]
    unselect_all()
    load_image()
    update_label_counts()

# Function to delete selected squares
def delete_selected():
    # Remove the current instance number from active_instance_numbers of all selected squares
    current_instance_number = get_instance_number(state['current_image_name'])
    state['coordinates_df'].loc[state['coordinates_df']['selected'], 'active_instance_numbers'] = state['coordinates_df'].loc[state['coordinates_df']['selected'], 'active_instance_numbers'].apply(lambda x: [i for i in x if i != current_instance_number])
    # Remove rows where active_instance_numbers is empty
    state['coordinates_df'] = state['coordinates_df'][state['coordinates_df']['active_instance_numbers'].map(len) > 0].reset_index(drop=True)
    # Reload the image to reflect changes
    unselect_all()
    load_image()
    update_label_counts()
    



# Function to save labels to a CSV file
def save_labels_to_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        # Convert 'active_instance_numbers' into list of integers
        state['coordinates_df']['active_instance_numbers'] = state['coordinates_df']['active_instance_numbers'].apply(lambda x: [int(i) for i in x])
        
        # Save the DataFrame to the specified CSV file
        state['coordinates_df'].to_csv(file_path, index=False)
        tk.messagebox.showinfo("Save Labels", f"Labels saved to {file_path}")
        last_save_time = datetime.now()
        
# Function to load labels from a CSV file
def load_labels_from_file():
    # Open a file dialog to select the CSV file
    file_path = filedialog.askopenfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        # Load the DataFrame from the specified CSV file
        state['coordinates_df'] = pd.read_csv(file_path)
        # Convert 'active_instance_numbers' from string representation of list to actual list
        state['coordinates_df']['active_instance_numbers'] = state['coordinates_df']['active_instance_numbers'].apply(eval)
        load_image()
        update_label_counts()
        
# Function to delete all labels in the current slice
def delete_all_labels_slides():
    if tk.messagebox.askyesno("Confirm Delete", "Are you sure you want to delete all labels in the current slice?"):

        current_instance_number = get_instance_number(state['current_image_name'])
        # Remove this instance from all active_instance_numbers
        state['coordinates_df']['active_instance_numbers'] = state['coordinates_df']['active_instance_numbers'].apply(lambda x: [i for i in x if i != current_instance_number])
        
        # Remove rows where active_instance_numbers is empty
        state['coordinates_df'] = state['coordinates_df'][state['coordinates_df']['active_instance_numbers'].map(len) > 0].reset_index(drop=True)

        load_image()
        update_label_counts()


# Function to load labels from the previous slice
def load_labels_from_previous_slice():

    if state['current_image_idx'] > 0:
        # Retrieve the instance number of the previous image
        images_names = state['current_series_type_df']['file_name'].values.tolist()
        idx_current_image = images_names.index(state['current_image_name'])
        previous_image_name = images_names[idx_current_image - 1]
        previous_instance_number = get_instance_number(previous_image_name)
        current_instance_number = get_instance_number(state['current_image_name'])  
        for i, row in state['coordinates_df'].iterrows():
            if previous_instance_number in row['active_instance_numbers']:
                state['coordinates_df'].at[i, 'active_instance_numbers'].append(current_instance_number)
        unselect_all()
        load_image()
        update_label_counts()

# Create function to unselect all squares
def unselect_all():
    state['coordinates_df']['selected'] = False

# Function to update the total label counts
def update_label_counts():
    coordinates_df = state['coordinates_df']
    current_instance_number = get_instance_number(state['current_image_name'])
    
    tot_green_count = len(coordinates_df[(coordinates_df['label_type'] == 'green') & (coordinates_df['series_type'] == state['current_series_type'])])
    tot_red_count = len(coordinates_df[(coordinates_df['label_type'] == 'red') & (coordinates_df['series_type'] == state['current_series_type'])])
    tot_blue_count = len(coordinates_df[(coordinates_df['label_type'] == 'blue') & (coordinates_df['series_type'] == state['current_series_type'])])
    
    total_green_label_count.config(text=f"Total Green Labels: {tot_green_count}")
    total_red_label_count.config(text=f"Total Red Labels: {tot_red_count}")
    total_blue_label_count.config(text=f"Total Blue Labels: {tot_blue_count}")

    green_count = len(coordinates_df[(coordinates_df['label_type'] == 'green') & (coordinates_df['active_instance_numbers'].apply(lambda x: current_instance_number in x)) & (coordinates_df['series_type'] == state['current_series_type'])])
    red_count = len(coordinates_df[(coordinates_df['label_type'] == 'red') & (coordinates_df['active_instance_numbers'].apply(lambda x: current_instance_number in x)) & (coordinates_df['series_type'] == state['current_series_type'])])
    blue_count = len(coordinates_df[(coordinates_df['label_type'] == 'blue') & (coordinates_df['active_instance_numbers'].apply(lambda x: current_instance_number in x)) & (coordinates_df['series_type'] == state['current_series_type'])])
    
    green_label_count.config(text=f"Green Labels in slice: {green_count}")
    red_label_count.config(text=f"Red Total Labels in slice: {red_count}")
    blue_label_count.config(text=f"Blue Total Labels in slice: {blue_count}")


def set_scollable_canvas():
    global scale_factor
    
    # Get figure size
    fig_size = fig.get_size_inches()
    fig.set_size_inches(fig_size[0] * scale_factor, fig_size[1] * scale_factor)
    # Set the new width and height of the window_id
    new_width = int(np.ceil(window_width_original * scale_factor))
    new_height = int(np.ceil(window_height_original * scale_factor))
    
    tk_canvas.itemconfig(window_id, width=new_width, height=new_height)
    tk_canvas.config(scrollregion=tk_canvas.bbox(tk.ALL))

# Function to write a report to a file
def write_report_to_file():
    report_file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if report_file_path:
        with open(report_file_path, 'w') as report_file:
            series_types = state['coordinates_df']['series_type'].unique()
            for series_type in series_types:
                report_file.write(f"Series Type: {series_type}\n")
                series_df = state['coordinates_df'][state['coordinates_df']['series_type'] == series_type]
                green_count = len(series_df[series_df['label_type'] == 'green'])
                red_count = len(series_df[series_df['label_type'] == 'red'])
                blue_count = len(series_df[series_df['label_type'] == 'blue'])
                report_file.write(f"  Green Labels: {green_count}\n")
                report_file.write(f"  Red Labels: {red_count}\n")
                report_file.write(f"  Blue Labels: {blue_count}\n")
                report_file.write("\n")
        tk.messagebox.showinfo("Report Saved", f"Report saved to {report_file_path}")

# Function to zoom in on the image
def zoom_in():
    global scale_factor
    scale_factor = scale_factor * 1.1

    set_scollable_canvas()

    # Redraw the canvas
    canvas.draw()
    
def reset_view():
    global scale_factor
    scale_factor = 1
    set_scollable_canvas()
    load_image()

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
file_menu.add_command(label="Save Report to File", command=write_report_to_file)
file_menu.add_command(label="Export images with Labels to File", state="disabled")

file_menu_button.config(menu=file_menu)

## -- Image frame
# Create a Matplotlib figure and axis
fig, ax = plt.subplots()

# For debug convenience
# ax.set_title("Click on the plot to place a square")
# image_file_path = "/Users/nc-mbp-4564/Documents/neurology/ANTONELLI/ANTONELLI - RMN encefalo 2018/DICOM/MP000001"
# # Get image
# ds = dcmread(image_file_path)
# # Plot the image 
# image_array = ds.pixel_array
# ax.clear()
# ax.imshow(image_array, cmap='gray')
# ax.set_title(f"Image: {state['current_image_name']}")



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
window_id = tk_canvas.create_window((0, 0), window=canvas_widget, anchor="nw")
tk_canvas.config(scrollregion=tk_canvas.bbox(tk.ALL))


## -- Interaction frame

# Create a frame for the buttons at the top
button_frame = tk.Frame(root)
button_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

# Create buttons to navigate images
previous_image_button = tk.Button(button_frame, text="Previous Image", command=previous_image)
previous_image_button.grid(row=0, column=0, padx=5, pady=5)

# Create a slider to move between images
slider = tk.Scale(button_frame, from_=0, to=0, orient=tk.HORIZONTAL, command=update_image_slider)
slider.grid(row=0, column=1, columnspan=2, sticky='ew', padx=5, pady=5)

next_image_button = tk.Button(button_frame, text="Next Image", command=next_image)
next_image_button.grid(row=0, column=3, padx=5, pady=5)

# Create dropdown to select the series label_type
series_type_combo = ttk.Combobox(button_frame, values=[], state='readonly', width=20)
series_type_combo.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

# Create a buttom to zoom in
zoom_in_button = tk.Button(button_frame, text="Zoom In", command=zoom_in)
zoom_in_button.grid(row=1, column=2, padx=5, pady=5)

# Create a button to reset the view
reset_view_button = tk.Button(button_frame, text="Reset View", command=reset_view)
reset_view_button.grid(row=1, column=3, padx=5, pady=5)

# Create a vertical separator spanning multiple rows
ttk.Separator(button_frame, orient='vertical').grid(row=0, column=4, rowspan=2, sticky='ns', padx=5, pady=5)

# Add an entry for setting square size
tk.Label(button_frame, text="Square Size:").grid(row=0, column=5, padx=0, pady=0)
square_size_entry = tk.Entry(button_frame, width=5)
square_size_entry.insert(0, str(default_square_size))  # Set default square size
square_size_entry.grid(row=0, column=6, padx=0, pady=0)

# Create dropdown to select the label_type of label
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

# Get initial state for later zoom
window_width_original = tk_canvas.bbox(window_id)[2] - tk_canvas.bbox(window_id)[0]
window_height_original = tk_canvas.bbox(window_id)[3] - tk_canvas.bbox(window_id)[1]

# Configure the grid to expand properly
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Connect the click, motion, and release events for drawing and moving squares
canvas.mpl_connect('button_press_event', on_click)
canvas.mpl_connect('motion_notify_event', on_motion)
canvas.mpl_connect('button_release_event', on_release)
# Bind the series label_type combo box to the selection function
series_type_combo.bind("<<ComboboxSelected>>", on_series_type_selected)

## ---- Init code sequence ---- 
# Ask user name before starting
def ask_user_name():
    user_name = simpledialog.askstring("Input", "Surname")
    if user_name is None:
        user_name = 'unknown'
    else:
        user_name = ''.join(e for e in user_name if e.isalnum())
    return user_name
user_name = ask_user_name()


# Backup function
def save_backup():
    # Create a folder to store the backup
    backup_folder = os.path.join(os.path.dirname(__file__), 'backup')
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # Save the coordinates DataFrame to a CSV file
    backup_file_path = os.path.join(backup_folder, f"coordinates_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    state['coordinates_df']['active_instance_numbers'] = state['coordinates_df']['active_instance_numbers'].apply(lambda x: [int(i) for i in x])
    state['coordinates_df'].to_csv(backup_file_path, index=False)


# Function to periodically save backup
def periodic_backup():
    global state
    threshold = 60*10  # Save every 60 seconds
    while True:
        time.sleep(threshold)
        save_backup()
        print(f"Backup saved at {datetime.now()}")


# Start the periodic backup in a separate thread
backup_thread = threading.Thread(target=periodic_backup, daemon=True)
backup_thread.start()

# Function to periodically check the last save time and show a popup if needed
def check_last_save():
    trheshold = 60*10  # 10 minutes
    global last_save_time
    while True:
        time.sleep(trheshold)
        tk.messagebox.showwarning("Save Reminder", "It's been more than 10 minutes since the last save.")
        last_save_time = datetime.now()


# Start the periodic check in a separate thread
save_check_thread = threading.Thread(target=check_last_save, daemon=True)
save_check_thread.start()

# Function to handle window close event
def on_closing():
    global last_save_time
    time_since_last_save = (datetime.now() - last_save_time).total_seconds()
    if time_since_last_save > 60:  # 10 minutes
        if not tk.messagebox.askyesno("Unsaved Changes", "You have unsaved changes since last 10 min. Do you want to exit without saving?"):
            return
    root.destroy()

# Bind the window close event to the on_closing function
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the Tkinter event loop
root.mainloop()
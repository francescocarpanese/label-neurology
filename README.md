A tool to simplify the process of counting cerebral microbleeds in MRI scans, reading DICOM files.

![example](output_neurology.gif)

The main challenge for the neurologist when counting microbleeds is keeping track of previous slices to avoid double-counting the same microbleed across multiple slices.

This project aims to streamline that process. By clicking on a microbleed in the image, a square is drawn around it with a solid line. When moving to the next slice, the user can import annotations from the previous slice. These imported annotations appear as dashed lines to indicate they are inherited from the previous slice, representing the same microbleed. As a result, each microbleed is counted only once in the total count.

Additionally, when an inherited microbleed disappears from view after a few slices, the user can delete it from the current slice. If the user deletes a microbleed that is linked to other slices, only the instance on the active slice is removed, leaving other slices unaffected.

This way the user can keep track of the microbleeds across slices and avoid double-counting them, wihout the burden of manually keeping track of them.

# Installation

## Windows
- Download the latest version of the program [here](https://github.com/francescocarpanese/label-neurology/releases/download/v.1.0.2/label-neurology.zip)
- Unzip the folder.
- Copy the file `main.exe` in the location of your preference. 
- Double click on `main.exe` to run the program.

The location of the `main.exe` will contain the backup files for the annotation.

## Linux/MacOs
- Clone the repository `git clone https://github.com/francescocarpanese/label-neurology.git`
- Open a terminal.
- Navigate the folder `cd label-neurology`
- It is recommended to use a conda environment.
- Run `pip install -r requirements.txt` to install the dependencies.
- Run the program with `python main.py`

# Features
- Import annotations from previous slices.
- Count only 1 time linked microbleeds across slices.
- Delete annotations from the current slice.
- Save the annotations in a csv file.
- Load the annotations from a csv file.
- Different color to distinguish between type of microbleeds.
- Zoom in/out.
- Save report file with the count of microbleeds per patient.
- Automatic backup of the annotations every 10 minutes.

# Contributing
Open a branch and create a pull request.

# Contact
If you have any question/request reach out at francescocarpanese [at] hotmail [dot] it.



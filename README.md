Duplicate Finder App
Overview
This Python application aims to assist users in finding and managing duplicate files within specified folders. It provides a user-friendly GUI for selecting folders, initiating scans, and managing duplicate files. The application is built using the PyQt5 framework.

Key Features
Select Folders:

Click on the "Select Folders" button to choose folders for duplicate scanning.
Start Scan:

After selecting folders, click on the "Start Scan" button to initiate the scanning process.
Duplicate files will be identified based on file size.

Display Results:

Duplicate files will be displayed in a list, organized by sets.
Results can be sorted by file name, file size, or modification date.

Delete Duplicates:

Use the "Delete Selected Duplicates" button to remove selected duplicate files.
A confirmation dialog will be displayed before deletion.

Preview Files:

Click on the "Preview Selected File" button to open and preview the first selected duplicate file.

Advanced Options:

Access advanced options via the "Advanced Options" button to customize the scanning process.
Specify file types, size threshold, and include hidden files.

Application Architecture :

The application is structured with a main window (DuplicateFinderApp) that includes a set of buttons and a list widget for displaying results.
A separate thread (DuplicateScannerThread) is utilized for scanning duplicate files asynchronously.

Installation and Usage :
- Ensure you have Python installed on your system.
Install required Python packages using the following command:
- pip install PyQt5
  
Run the application using the following command:
python <filename>.py

# CASABee

CASABee is an open-source tool devoted to the analysis of the sperm motility and concentration in honey bee drones.

![](https://raw.githubusercontent.com/jodivaso/CASABee/master/readme_video.gif)

## Features

- Automatic detection and tracking of motile and static sperms from videos
- Computation of the concentration
- Edit mode to manually label motile and static sperms
- Generation of videos where motile and static sperms are tracked
- Result can be exported to a CSV file

## Installation and Execution

The following commands clone the repository, install the requirements and execute the program.

```
git clone https://github.com/jodivaso/CASABee.git
pip install -r requirements.txt
cd CASABee
python3 CASABee.py
```

## Binary Files

Alternatively, you can obtain the binary files for Windows 10 (64bits) [here.](https://unirioja-my.sharepoint.com/:u:/g/personal/jodivaso_unirioja_es/EdFpy_dr4IRFlGWBS0pqf8MBLh2VQgvI_NmmbvA-2p11ow?e=zAnGkF)

Just download it, unzip and execute CASABee.exe.

## Specifications

CASABee has been tested with videos in AVI format. The program has been tested on Windows 10 (64-bit) and Linux (Ubuntu 20.04). 
There are no specific requirements to use this software, but at least 8GB of RAM are recommended for analyzing large sets of videos. The program makes considerable use of parallelization techniques to speed-up the computations, so a processor with several cores is also recommended.

## GUI

The graphical user interface is quite simple. The top bar has four buttons: open videos, reset, export results to CSV and edit mode.

Once a video (or a set of videos) is selected, the analysis starts. Once it finishes, you can click on the video to play it with
the labels. Static sperms are labelled in red. Motile sperms are coloured, numbered and tracked in the video.

## Edit Mode

The last button of the top bar is the edit mode. Once a video is selected, in that mode one manually label and modify the detected motile and static sperms:

- Pressing the key ```h``` one can hide the labels and see the first frame of the video. Releasing the key makes the labels appear again
- New motile sperms can be added by clicking on a point (the center) and dragging to select the radio
- Motile sperms can be deleted: right-click on the center
- New static sperms can be added: double click on the initial point, click on the next point, click on the next point and so on until finishing with a double-click
- For each cluster of static sperms, there appears the estimated number in magent. One can modify the number by clicking on it
- Each cluster is coloured in yellow when hovering over it
- The results are automatically updated after each change in the edit mode
- The video with the labels is recomputed once finished the edition
- With ```CTRL + z``` one can undo the last change


## Parameters

The default parameters works well in most cases, but one can also tune the parameters used for the analysis:

- Min radius
- Max radius
- Param1
- Param2
- Mean cell size
- Scale
- Camera height
- Diluent parts

## Acknowledgements

This work was supported by the Spanish MINECO (grants PID2020-112673RB-100 and PID2020-116641GB-I00), and the DGA-FSE (grant A07_17R)
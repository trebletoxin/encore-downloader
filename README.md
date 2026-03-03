# Encore Downloader
This tool is meant to be used to download all charts that are posted on [enchor.us](https://www.enchor.us/) for use in Clone Hero.

At this time, all charts downloaded are converted from .sng to chart formats compatible with Clone Hero 1.0.0.4080

Once CH 1.1.0 is released and supports .sng format charts, this will be updated to allow direct downloads without conversion.

## NOTES - DO NOT SKIP THIS

Allowing this tool to fully download all charts will require roughly 400GB of disk space. If you do not have enough space to accomidate this, it will fill up your disk.

It is **HEAVILY** recommended to use a new folder separate from your current songs folder to download all the charts too. As ~80,000 new folders will be created,
it will cause working with any other folders in your current songs folder very difficult. 

## NEW! GUI for Windows

A GUI executable has been built for Windows.

A simple user interface — select your chart directory and start. That is all that's needed. Additional options are available as well — these mirror the CLI arguments.

Again, it is recommended that you create a new folder to download charts to and add it to clone hero after downloading everything.

### Usage

Download the executable from the [releases](https://github.com/trebletoxin/encore-downloader/releases).

## Command Line Options for all OS's

```
  -chf CLONE_HERO_FOLDER, --clone-hero-folder CLONE_HERO_FOLDER
                        Clone Hero songs folder to output charts to. This option is required
  -t THREADS, --threads THREADS
                        Maximum number of threads to allow - defaults to 4 and is recommended
  -soe, --stop-on-error
                        Continue on error during conversion or download. 
                        Only used for debugging
  -p PAGE, --page PAGE
                        Starting page for Encore downloads - defaults to 1. 
                        Only used for debugging
  -s SEARCH, --search SEARCH
                        String entry to search on Encore - defaults to blank string (empty)
                        Only used for debugging
  -d, --drums
                        Only downloads charts containing drum parts
  -sc, --schema-cleanup
                        Only run this flag if you have run an old version of this script.
                        Renames previously downloaded charts to match the naming schema 
                        that Bridge uses.
  -rp, --remove-playlist
                        Removes "playlist=" and "playlist_track=" lines from the song.ini of 
                        every chart. This includes both new downloads, and previously 
                        downloaded charts in your directory.
```
### CLI Usage

To download, hit "Code" at the top right, then download as a zip and extract it.

### Windows (CLI)

A pre-built .exe file is added in the repository to allow this tool to be ran without setting up a python environment.

`cd C:\Users\yourusername\Downloads\encore-downloader` (if you extract the zip in your downloads folder, replace yourusername with your Windows username. Navigate to where you extracted the tool)

`.\main.exe -chf C:\Users\yourusername\Documents\CloneHero-EncoreSongs` (CloneHero-EncoreSongs being a new folder, add it to Clone Hero once the download is complete)

### Linux

As Linux usually includes python, simply get the requirement libraries added then run it

`pip3 install -r requirements.txt`

`python3 ./main.py -chf /home/yourusername/clonehero/CloneHero-EncoreSongs` (CloneHero-EncoreSongs being a new folder, add it to Clone Hero once the download is complete. Replace yourusername with your linux username)

mainGUI.py requires requirementsGUI.txt to be installed. 

### macOS

macOS is not tested, but should work assuming you get a python environment setup and working. If issues are found, create an issue to get it corrected.

## Credit

[Jetsurf](https://github.com/Jetsurf) - [Encore-Downloader](https://github.com/Jetsurf/encore-downloader) - For making this awesome downloader. Many thanks from me, as this would never have gotten this far without your support.

[Geomitron](https://github.com/Geomitron) - [Bridge](https://github.com/Geomitron/Bridge) - The inspiration for this tool, and [enchor.us](https://www.enchor.us/) to make this possible

[Matthew Sitton](https://github.com/mdsitton) - [SngCli](https://github.com/mdsitton/SngFileFormat) - For detailed breakdown of the .sng file. This was essential in the creation a custom python handler for the sng format.

[chriskiehl](https://github.com/chriskiehl) - [Gooey](https://github.com/chriskiehl/Gooey) - Simple GUI builder for python projects.

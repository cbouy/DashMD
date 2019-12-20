# DashMD

Real time monitoring and visualization of Amber MD simulations

DashMD let's you track the status, temperature, pressure, volume, density, and energy of your currently running simulation in an interactive way.
You can also plot the RMSD of your trajectories and visualize them directly with [NGL](https://github.com/arose/ngl).

## Screenshots

#### Main tab
<img src="https://user-images.githubusercontent.com/27850535/71206876-f3981500-22a5-11ea-9a33-2c394872eb50.png" width=500>

#### Visualization
<img src="https://user-images.githubusercontent.com/27850535/71206898-001c6d80-22a6-11ea-8efe-2551cbd4b06d.png" width=500>

#### RMSD tab
<img src="https://user-images.githubusercontent.com/27850535/71206907-06aae500-22a6-11ea-8707-35c85c74fc4a.png" width=500>

#### Density tab
<img src="https://user-images.githubusercontent.com/27850535/71206923-0c082f80-22a6-11ea-95c8-f2ed11dd53dc.png" width=500>

## Installation

DashMD runs on python and a bit of JavaScript, and depends on the following python packages: `pandas, bokeh, pytraj` which are all automatically installed as requirements. To install, simply run the following command :

```bash
  pip install git+https://github.com/cbouy/DashMD.git
```

## Usage

Simply type `dashmd` in a terminal and it should open a new tab in your web browser.

:warning: Currently, DashMD expects all of your files (mdinfo, prmtop, mdout, mdcrd/netcdf) to be in the same directory.

Start by navigating to the folder containing the `mdinfo` file then press on the `Load` button (which should turn green if the folder contains a `mdinfo` file). The Temperature, Pressure...etc will automatically be read from the mdinfo file and plotted on the corresponding tabs, and the structure from the latest Amber Restart file will be plotted on the `View` tab.

In order to plot the Temperature, Pressure...etc. for a specific simulation file, select the MDOUT file (bottom of the Dashboard tab, only files ending in `.mdout` or `.out` will be listed), then press `Plot`. This might take a while depending on the size of the file.

To visualize a structure or plot the RMSD, click on the corresponding tab and select both Topology file and Trajectory file and click on the corresponding button. Only files ending with `.top`, `.prmtop`, `.parm7` or `.parm` will be listed for the topology. The RMSD calculation is performed by slicing your trajectory in around 200 frames if possible, for faster calculations.

For the `View` tab, only files with the `.rst` or `.rst7` extension are listed.

For the `RMSD` tab, only files ending with `.nc`, `.netcdf`, or `.ncdf` will be listed.
You can select multiple trajectory files to plot by pressing on the `Ctrl` key on your keyboard while selecting the trajectories.
You can restrict the atoms selected for RMSD calculation by specifying a mask as specified in the `pytraj` documentation [here](https://amber-md.github.io/pytraj/latest/atom_mask_selection.html). A `protein` keyword has been added for easier selection of all protein residues (it's a substitute for `:ALA,ARG`... and all of their protonated forms)

If necessary, more detailed options are available in the command line:
```
usage: dashmd [-h] [-v] [--port INT] [--update INT] [--default-dir STR]
              [--log level]

Monitor and visualize MD simulations from Amber in real time

optional arguments:
  -h, --help         show this help message and exit
  -v, --version      Show version and exit
  --port INT         Port number used by the bokeh server (default: 5100)
  --update INT       Update rate to check and load new data, in seconds (default: 20)
  --default-dir STR  Default directory (default: .)
  --log level        Set level of the logger (default: INFO)
```

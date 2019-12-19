# DashMD

Real time monitoring and visualization of Amber MD simulations

DashMD let's you track the status, temperature, pressure, volume, density, and energy of your currently running simulation in an interactive way.
You can also plot the RMSD of your trajectories and visualize them directly with [NGL](https://github.com/arose/ngl).

## Screenshots

<img src="https://user-images.githubusercontent.com/27850535/71206876-f3981500-22a5-11ea-9a33-2c394872eb50.png" width=500>
<img src="https://user-images.githubusercontent.com/27850535/71206898-001c6d80-22a6-11ea-8efe-2551cbd4b06d.png" width=500>
<img src="https://user-images.githubusercontent.com/27850535/71206907-06aae500-22a6-11ea-8707-35c85c74fc4a.png" width=500>
<img src="https://user-images.githubusercontent.com/27850535/71206923-0c082f80-22a6-11ea-95c8-f2ed11dd53dc.png" width=500>

## Installation

DashMD runs on python and a bit of JavaScript, and depends on the following python packages: `pandas, seaborn, bokeh, pytraj` which are all automatically installed as requirements. To install, simply run the following command :

```bash
  pip install git+https://github.com/cbouy/DashMD.git
```

## Usage

Simply type `dashmd` in a terminal and it should open a new tab in your web browser. More options are available:

```
usage: dashmd [-h] [-v] [--port INT] [--update INT] [--default-dir STR]
              [--log level]

Monitor and visualize MD simulations from Amber in real time

optional arguments:
  -h, --help         show this help message and exit
  -v, --version      Show version and exit
  --port INT         Port number used by the bokeh server (default: 5100)
  --update INT       Update rate to check and load new data, in seconds (default: 10)
  --default-dir STR  Default directory (default: .)
  --log level        Set level of the logger (default: INFO)
```

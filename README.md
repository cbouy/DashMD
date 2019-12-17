# DashMD

Real time monitoring and visualization of Amber MD simulations

DashMD let's you track the status, temperature, pressure, volume, density, and energy of your currently running simulation in an interactive way.
You can also plot the RMSD of your trajectories and visualize them directly with [NGL](https://github.com/arose/ngl).

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

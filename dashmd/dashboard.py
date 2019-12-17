import re, os, time, copy, glob, sys, logging
from io import StringIO
from math import pi
from collections import OrderedDict
from functools import partial
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import pytraj as pt
import seaborn as sns
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import nglview
from bokeh.models import (
    ColumnDataSource, CustomJS, CustomJSTransform,
    Legend, PrintfTickFormatter, Range1d, Div,
)
from bokeh.models.widgets import (
    TextInput, Button, Div, Toggle, Select, Slider, MultiSelect,
)
from bokeh.layouts import column
from bokeh.transform import transform, cumsum
from bokeh.plotting import figure
from utils import *

log = logging.getLogger("dashmd")


class Dashboard:
    def __init__(self, default_dir):
        # MD directory and files selection
        self.md_dir = TextInput(title="Path to MD directory containing mdin and mdout files", value=default_dir, width=750)
        self.anim_button = Toggle(label="▶ Load", button_type="warning", width=80, height=50, active=False)
        # container for the buttons that are created while the user types in the textinput
        self.autocomp_results = column(children=[])
        # file used to display temperature, pressure...etc. plots
        self.mdout_sel = Select(
            title="MDout file", width=230,
            value=None, options=[],
        )
        # button to load content
        self.mdout_button = Button(width=80, height=50, label="Plot", button_type="primary")
        self.mdout_files = [None]
        self.md_mdout_files = []

        # mdinfo figures
        progressbar_tooltip = """
        <span style="color:#428df5">@completed{0,0}</span> out of <span style="color:#428df5">@total{0,0}</span> steps (<span style="color:#428df5">@remaining{0,0}</span> remaining)
        """
        self.progressbar = figure(
            title="Current progress", x_range=Range1d(0, 10),
            tooltips=progressbar_tooltip,
            height=70, width=350, tools="hover", toolbar_location=None)
        self.progressbar.xgrid.grid_line_color = None
        self.progressbar.ygrid.grid_line_color = None
        self.progressbar.axis.visible = False
        self.progressbar.outline_line_color = "#444444"
        self.steps_CDS = ColumnDataSource({
            "total":     [np.nan],
            "completed": [np.nan],
            "remaining": [np.nan],
            "color": ['#428df5'],
        })
        self.progressbar.hbar(
            y=0, left=0, right="completed",
            source=self.steps_CDS, height=0.5, color="color",
        )
        self.progressbar.hover[0].mode = "hline"

        self.calc_speed = Div(
            width=150, height=50, text="Calculation speed:",
            style={"font-weight": "bold", "color": "#444444", "margin-top": "5px"}
        )

        self.eta = Div(
            width=100, height=50, text="ETA:",
            style={"font-weight": "bold", "color": "#444444", "margin-top": "5px"}
        )

        self.last_update = Div(
            width=280, height=50, text="Last update:",
            style={"font-weight": "bold", "color": "#444444", "margin-top": "5px"}
        )

        # number of mdout files displayed on the dashboard at max
        self.slider = Slider(start=1, end=10, value=2, step=1, callback_policy="mouseup", title="Number of simulations displayed")
        self.dashboard_CDS = ColumnDataSource({
            "y_coords": [0, 1],
            "mdout": ["heat.out", "prod.out"],
            "time":  [42, 200],
            "angle": [1.09, 5.193],
            "color": ["#f54b42", "#4287f5"],
        })
        dashboard_tooltip = """
        <span style="color:@color">@mdout</span>: @time{0,0.00} ns
        """
        # pie plot
        self.pie = figure(
            plot_height=300, width=500, title="Simulations length", toolbar_location=None,
            tools="hover", tooltips=dashboard_tooltip, x_range=Range1d(-0.5, 1.0))

        self.rpie = self.pie.wedge(
            x=0, y=1, radius=0.4, source=self.dashboard_CDS,
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_color="white", fill_color='color', legend="mdout" )
        self.pie.axis.axis_label=None
        self.pie.axis.visible=False
        self.pie.grid.grid_line_color = None
        self.pie.legend.label_text_font_size = '9pt'
        self.pie.legend.border_line_width = 0
        self.pie.legend.border_line_alpha = 0
        self.pie.legend.spacing = 0
        self.pie.legend.margin = 0
        # hbar plot
        self.bar = figure(
            width=850, plot_height=300, toolbar_location=None,
            tools="hover", tooltips=dashboard_tooltip)
        self.rbar = self.bar.hbar(
            y="y_coords", left=0, right="time", source=self.dashboard_CDS,
            height=0.8, color="color")
        self.bar.x_range.set_from_json("start", 0)
        self.bar.xaxis.axis_label="Time (ns)"
        self.bar.yaxis.axis_label=None
        self.bar.yaxis.visible=False
        self.bar.hover[0].mode = "hline"

        ## Mdout figures
        self.mdinfo_CDS = ColumnDataSource(copy.deepcopy(empty_mddata_dic))
        self.moving_avg_trans = CustomJSTransform(v_func=moving_avg_func)
        ticker = PrintfTickFormatter(format="%4.0e")
        # Temperature
        self.temperature_fig = figure(plot_height=size[1], plot_width=size[0],
            active_scroll="wheel_zoom",
        )
        self.temperature_fig.toolbar.autohide = True
        self.temperature_fig.xaxis.axis_label = "Number of steps"
        self.temperature_fig.yaxis.axis_label = "Temperature (K)"
        self.temperature_fig.xaxis.formatter = ticker
        r = self.temperature_fig.line(
            "Nsteps","Temperature", color=palette[0], source=self.mdinfo_CDS, _width=1, alpha=0.15)
        self.temperature_fig.line(transform("Nsteps", self.moving_avg_trans), transform("Temperature", self.moving_avg_trans),
                 color=colorscale(palette[0],0.85), source=self.mdinfo_CDS, line_width=3)
        self.temperature_fig.add_tools(make_hover([r]))

        # Pressure
        self.pressure_fig = figure(plot_height=size[1], plot_width=size[0],
            active_scroll="wheel_zoom",
        )
        self.pressure_fig.toolbar.autohide = True
        self.pressure_fig.xaxis.axis_label = "Number of steps"
        self.pressure_fig.yaxis.axis_label = "Pressure"
        self.pressure_fig.xaxis.formatter = ticker
        r = self.pressure_fig.line("Nsteps","Pressure", color=palette[1], source=self.mdinfo_CDS, line_width=1, alpha=0.15)
        self.pressure_fig.line(transform("Nsteps", self.moving_avg_trans), transform("Pressure", self.moving_avg_trans),
                 color=colorscale(palette[1],0.85), source=self.mdinfo_CDS, line_width=3)
        self.pressure_fig.add_tools(make_hover([r]))

        # Energy
        self.energy_fig = figure(plot_height=size[1], plot_width=size[0],
            active_scroll="wheel_zoom",
        )
        etot  = self.energy_fig.line("Nsteps","Etot",  color=palette[2], source=self.mdinfo_CDS, line_width=1)
        ektot = self.energy_fig.line("Nsteps","EKtot", color=palette[3], source=self.mdinfo_CDS, line_width=1)
        eptot = self.energy_fig.line("Nsteps","EPtot", color=palette[4], source=self.mdinfo_CDS, line_width=1)
        legend = Legend(items=[
            ("Total"   , [etot]),
            ("Kinetic" , [ektot]),
            ("Potential" , [eptot]),
        ], location="top_right")
        self.energy_fig.add_layout(legend, 'right')
        self.energy_fig.add_tools(make_hover([etot]))
        self.energy_fig.legend.location = "top_left"
        self.energy_fig.legend.click_policy="hide"
        self.energy_fig.toolbar.autohide = True
        self.energy_fig.xaxis.axis_label = "Number of steps"
        self.energy_fig.yaxis.axis_label = "Energy"
        self.energy_fig.xaxis.formatter = ticker

        # Volume
        self.vol_fig = figure(plot_height=size[1], plot_width=size[0],
            active_scroll="wheel_zoom",
        )
        self.vol_fig.toolbar.autohide = True
        self.vol_fig.xaxis.axis_label = "Number of steps"
        self.vol_fig.yaxis.axis_label = "Volume"
        self.vol_fig.xaxis.formatter = ticker
        r = self.vol_fig.line("Nsteps","Volume", color=palette[6], source=self.mdinfo_CDS, line_width=1, alpha=0.15)
        self.vol_fig.line(transform("Nsteps", self.moving_avg_trans), transform("Volume", self.moving_avg_trans),
                 color=colorscale(palette[6],0.85), source=self.mdinfo_CDS, line_width=3)
        self.vol_fig.add_tools(make_hover([r]))

        # Density
        self.density_fig = figure(plot_height=size[1], plot_width=size[0],
            active_scroll="wheel_zoom",
        )
        self.density_fig.toolbar.autohide = True
        self.density_fig.xaxis.axis_label = "Number of steps"
        self.density_fig.yaxis.axis_label = "Density"
        self.density_fig.xaxis.formatter = ticker
        r = self.density_fig.line("Nsteps","Density", color=palette[7], source=self.mdinfo_CDS, line_width=1, alpha=0.15)
        self.density_fig.line(transform("Nsteps", self.moving_avg_trans), transform("Density", self.moving_avg_trans),
                 color=colorscale(palette[7],0.85), source=self.mdinfo_CDS, line_width=3)
        self.density_fig.add_tools(make_hover([r]))

        ## RMSD figure
        self.empty_rmsd_dic = {k:[] for k in ["Time","RMSD"]}
        self.rmsd_CDS = ColumnDataSource(self.empty_rmsd_dic)
        self.rmsd_fig = figure(plot_height=size[1], plot_width=size[0],
            active_scroll="wheel_zoom",
        )
        self.rmsd_fig.toolbar.autohide = True
        self.rmsd_fig.xaxis.axis_label = "Time (ps)"
        self.rmsd_fig.yaxis.axis_label = "RMSD (Å)"
        self.rmsd_fig.xaxis.formatter = ticker
        r = self.rmsd_fig.line(
            "Time","RMSD", color=palette[8], source=self.rmsd_CDS, line_width=2)
        self.rmsd_fig.add_tools(make_hover([r], tooltips=[
            ("Time (ps)", "@Time{0,0}"),
            ("RMSD (Å)", "@RMSD")
        ]))
        self.rmsd_button = Button(width=100, label="Calculate RMSD", button_type="primary")
        self.trajectory = MultiSelect(
            title="Trajectory file(s)", width=400,
            value=None, options=[],
        )
        self.topology = Select(
            title="Topology file", width=200,
            value=None, options=[],
        )
        # NGLview
        self.view_button = Button(width=80, label="Visualize")
        self.view_canvas = Div(width=size[0], height=size[1], css_classes=["ngldiv"], text="")
        # others
        self.mdout_min = {}
        self.mdout_dt = {}
        self.add_callbacks()


    def autocomp_callback(self, attr, old, new):
        """List all directories for the current typed path, output as buttons to click"""
        path = os.path.join(new + "*", "")
        opts = [] if new == "" else glob.glob(path)
        opts = sorted(opts, key=lambda x: x.split("/")[-2].lower())
        buttons = [
            Button(width=750, label=opt) for opt in opts
        ]
        for b in buttons:
            cb = CustomJS(args=dict(md_dir=self.md_dir, button=b), code="""
            md_dir.value_input = button.label;
            md_dir.value = button.label;
            """)
            b.js_on_click(cb)
        self.autocomp_results.children = buttons
        mdinfo_file = os.path.join(new, "mdinfo")
        if os.path.exists(mdinfo_file):
            self.anim_button.button_type = "success"
        else:
            self.anim_button.button_type = "warning"


    def traj_top_callback(self, attr, old, new):
        log.debug(f"Updating list of trajectory and topology files")
        try:
            traj = glob.glob(os.path.join(self.md_dir.value, "*.nc"))
            traj = [os.path.basename(f) for f in traj]
            traj.sort(key=lambda f: os.path.getmtime(os.path.join(self.md_dir.value, f)), reverse=True)
            self.trajectory.options = traj
            # search for .top, .prmtop, .parm7 or .prm
            top = [
                f for f in os.listdir(self.md_dir.value)
                    if re.search(r'.+\.(prm)?top$', f) or re.search(r'.+\.pa?rm7?$', f)
            ]
            self.topology.options = top
            if top:
                self.topology.value = top[0]
        except FileNotFoundError:
            pass


    def compute_rmsd(self):
        topology = os.path.join(self.md_dir.value, self.topology.value)
        trajectories = [os.path.join(self.md_dir.value, f) for f in self.trajectory.value]
        trajectories.sort(key=lambda f: os.path.getmtime(f), reverse=False)
        traj = pt.iterload(trajectories, topology)
        stepsize=get_stepsize(traj)
        frames = list(traj.iterframe(step=stepsize, autoimage=True, rmsfit=False,
            mask=":ALA,ARG,ASH,ASN,ASP,CYM,CYS,CYX,GLH,GLN,GLU,GLY,HID,HIE,HIP,HYP,HIS,ILE,LEU,LYN,LYS,MET,PHE,PRO,SER,THR,TRP,TYR,VAL@CA,C,O,N"))
        log.debug(f"Computing RMSD for top {topology} and traj {trajectories} with a step of {stepsize}")
        ref = frames[0]
        results = {"Time": [], "RMSD": []}
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            for rmsd, frame in zip(ex.map(partial(compute_rmsd, ref=ref), frames), frames):
                results["Time"].append(frame.time)
                results["RMSD"].append(rmsd)
        self.rmsd_CDS.data = results


    def view_structure(self):
        # TODO: parse traj and top and link them to data (with softlinks ?)
        self.js_view_structure.code = """
            // Set up NGL Viewport and Stage if it doesn't exist
            if (!document.getElementById('nglviewport')) {
                // Create viewport div
                var vp = document.createElement('div');
                vp.setAttribute("id", "nglviewport");
                vp.setAttribute("style", "height: 600px;")
                // Insert it inside the ngldiv Div
                var ngldiv = document.getElementsByClassName('ngldiv')[0];
                ngldiv.appendChild(vp)

                // Create NGL Stage object
                var stage = new NGL.Stage( "nglviewport" );

                // Handle window resizing
                window.addEventListener( "resize", function( event ){
                    stage.handleResize();
                }, false );
            }

            // Setup to load data from rawgit
            NGL.DatasourceRegistry.add(
                "data", new NGL.StaticDatasource( "//cdn.rawgit.com/arose/ngl/v2.0.0-dev.32/data/" )
            );

            // Code for example: parser/prmtop

            stage.loadFile("data://DPDP.prmtop").then(function (o) {
              NGL.autoLoad("data://DPDP.nc").then(function (frames) {
                o.addTrajectory(frames, {
                  initialFrame: 0,
                  deltaTime: 200
                })
                o.addRepresentation("licorice", {scale: 0.5})
                o.addRepresentation("spacefill", {sele: "not :B"})
                o.addRepresentation("cartoon")
                o.addRepresentation("backbone")
                stage.autoView()
              })
            })
        """
        # trigger javascript callback by adding an invisible character to the button label
        self.view_button.label += " "


    def clear_canvas(self):
        log.debug("Clearing canvas")
        self.mdinfo_CDS.data = copy.deepcopy(empty_mddata_dic)


    # search if min or md
    def read_mdout_header(self, mdout):
        log.debug(f"Reading header of {mdout} mdout file")
        mdout_path = os.path.join(self.md_dir.value, mdout)
        found_min = False
        with open(mdout_path, 'r') as f:
            for line in f:
                re1 = re.search(r"imin\s*=\s*([01])", line)
                if re1:
                    self.mdout_min[mdout] = bool(int(re1.group(1)))
                    found_min = True
                re2 = re.search(r"dt\s*=\s*([\.0-9]+)", line)
                if re2:
                    self.mdout_dt[mdout] = float(re2.group(1))
                if self.mdout_dt.get(mdout, False) and found_min:
                    log.debug(f"Finished reading header of {mdout}. Closing file.")
                    break


    def is_min(self, mdout):
        """Returns True if minimization, False if MD, None if the 'imin' keyword was not found"""
        try:
            t = self.mdout_min[mdout]
        except KeyError:
            log.debug(f"Parsing {mdout} mdout file to see if it's a minimization")
            self.read_mdout_header(mdout)
            t = self.mdout_min.get(mdout)
        log.debug(f"{mdout} is a minimization: {t}")
        return t


    def stream_mdout(self):
        """Parse and stream data from mdout files (minimization or MD simulation)"""
        self.clear_canvas()
        mdout = self.mdout_sel.value
        mdout_path = os.path.join(self.md_dir.value, mdout)
        mdout_data = copy.deepcopy(empty_mddata_dic)
        # open file
        with open(mdout_path, 'r') as f:
            log.debug(f"Parsing data from {mdout} mdout file")
            lines = []
            # stop reading when reaching the following lines
            for line in f:
                if ("A V E R A G E S   O V E R" in line) or ("Maximum number of minimization cycles reached" in line):
                    break
                lines.append(line)
        # check if min or md:
        parse_func = parse_min_data if self.is_min(mdout) else parse_md_data
        # parse in parallel
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            for res in ex.map(parse_func, lines):
                for k,v in res.items():
                    mdout_data[k].extend(v)
        # convert to numpy
        for key, lst in mdout_data.items():
            mdout_data[key] = np.array(lst)
        # stream to CDS
        log.debug(f"Done. Streaming the data from {mdout}")
        self.mdinfo_CDS.stream(mdout_data)
        mdout_data = copy.deepcopy(empty_mddata_dic)


    def latest_mdout_files(self):
        """List all mdout files present in the MD directory, sorted by modification time"""
        mdout_files = [
            f for f in os.listdir(self.md_dir.value)
                if re.search(r'.+\.m?d?out$', f) and ("nohup.out" not in f)
        ]
        mdout_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.md_dir.value, f)), reverse=True)
        return mdout_files


    def get_mdout_files(self):
        """Update the list of mdout files and automatically select the latest one"""
        log.debug("Updating the list of mdout files")
        self.mdout_files = [None]
        # set mdout file to read
        self.mdout_files = self.latest_mdout_files()
        mdout_options = self.mdout_sel.options
        self.mdout_sel.options = self.mdout_files
        # if new mdout is created
        if len(self.mdout_files) > len(mdout_options):
            self.mdout_sel.value = self.mdout_files[0]


    def parse_mdinfo(self):
        """Parse and stream data read from the mdinfo file"""
        log.debug("Parsing mdinfo file")
        mdinfo_path = os.path.join(self.md_dir.value, "mdinfo")

        with open(mdinfo_path, 'r') as f:
            lines = f.readlines()
        mdinfo_data = copy.deepcopy(empty_mddata_dic)
        # min or md
        latest_mdout_file = self.latest_mdout_files()[0]
        parse_func = parse_min_data if self.is_min(latest_mdout_file) else parse_md_data

        for i,line in enumerate(lines):
            # data
            res = parse_func(line)
            for k,v in res.items():
                mdinfo_data[k].extend(v)
            # number of steps
            re_steps = re.search(r"Total steps :\s*(\d+) \| Completed :\s*(\d+) \| Remaining :\s*(\d+)", line)
            if re_steps:
                total = int(re_steps.group(1))
                completed = int(re_steps.group(2))
                remaining = int(re_steps.group(3))
                steps_patch = {
                    "total":     [(0, total)],
                    "completed": [(0, completed)],
                    "remaining": [(0, remaining)],
                }
                self.steps_CDS.patch(steps_patch)
                progress = 100 * completed / total
                self.progressbar.title.text = f"Progress: {progress:6.2f}%"
                self.progressbar.x_range.set_from_json("end", total)

            # calculation speed (ns/day)
            re_speed = re.search(r'Average timings for last', line)
            if re_speed:
                re_speed = re.search(r'ns/day =\s*([\.0-9]+)', lines[i+2])
                speed = float(re_speed.group(1))
                self.calc_speed.text = f"Calculation speed:<br/>{speed} ns/day"

            # time remaining
            re_time = re.search(r'Estimated time remaining:\s*(.+).$', line)
            if re_time:
                time_left = re_time.group(1)
                self.eta.text = f"ETA:<br/>{time_left}"
                break

        # last update
        self.last_update.text = f"Last update:<br/>{pretty_date(os.path.getmtime(mdinfo_path))}"
        update_time = os.path.getmtime(mdinfo_path)
        if time.time() - update_time > 3*60: # not updated recently
            self.last_update.style = {"font-weight": "bold", "color": "#d62727", "margin-top": "5px"}
        else:
            self.last_update.style = {"font-weight": "bold", "color": "#444444", "margin-top": "5px"}

       # only update plots if monitoring the latest mdout file
        if self.mdout_sel.value == latest_mdout_file:
            # fetch previous stream data as dict
            last_mdinfo_stream = self.mdinfo_CDS.to_df().tail(1).reset_index(drop=True).T.to_dict().get(0)
            if last_mdinfo_stream:
                # format the dict
                for key, value in last_mdinfo_stream.items():
                    last_mdinfo_stream[key] = [value]
                # update if mdinfo is different from the previous stream
                if mdinfo_data != last_mdinfo_stream:
                    log.debug("Streaming new data from mdinfo")
                    for key, value in mdinfo_data.items():
                        mdinfo_data[key] = np.array(value)
                    self.mdinfo_CDS.stream(mdinfo_data)


    def display_simulations_length(self):
        """Displays simulation length"""
        log.debug("Computing total time of simulation(s) displayed")
        current_time = OrderedDict()
        # discard min files and limit to XX most recent MD files
        self.md_mdout_files = [f for f in self.mdout_sel.options if not self.is_min(f)][:self.slider.value]
        for mdout in self.md_mdout_files:
            mdout_path = os.path.join(self.md_dir.value, mdout)
            i = 0
            for line in readlines_reverse(mdout_path):
                i+=1
                re1 = re.search(r"NSTEP =\s*(\d+)", line)
                if re1:
                    current_time[mdout] = int(re1.group(1)) * self.mdout_dt.get(mdout, 0.002) * 1e-3 # in ns
                    break
                if i > 150:
                    break
        data = pd.DataFrame.from_dict(
            current_time, orient="index", columns=["time"]
        ).reset_index().rename(columns={"index":"mdout"})
        # compute properties for the pie plot
        data['angle'] = data['time']/data['time'].sum() * 2*pi
        # color palette
        palette = sns.color_palette("deep", len(current_time))
        data['color'] = palette.as_hex()
        # reverse index order for the barplot
        data = data.reindex(index=data.index[::-1]).reset_index(drop=True)
        data = data.reset_index().rename(columns={"index":"y_coords"})
        # update
        self.dashboard_CDS.data = {k: data[k].tolist() for k in data.columns}
        total_time = data["time"].sum()
        self.pie.title.text = f"Simulations length: {total_time:.2f} ns"


    def update_dashboard(self):
        log.debug("Starting update of the dashboard")
        self.get_mdout_files()
        self.parse_mdinfo()
        self.display_simulations_length()
        log.debug("Finished updating the dashboard")


    def callback_slider(self, attr, old, new):
        log.debug(f"Slider update detected: from {old} to {new}")
        self.display_simulations_length()


    def add_callbacks(self):
        log.debug("Adding callbacks to the widgets")
        # User input
        self.md_dir.on_change("value_input", self.autocomp_callback)
        self.md_dir.on_change("value", self.traj_top_callback)
        # RMSD
        self.rmsd_button.on_click(self.compute_rmsd)
        # NGLView
        self.js_view_structure = CustomJS(code="")
        # hack to execute both python and JS code on button click
        self.view_button.js_on_change("label", self.js_view_structure)
        self.view_button.on_click(self.view_structure)
        # MDout parsing
        self.mdout_button.on_click(self.stream_mdout)
        self.slider.on_change("value_throttled", self.callback_slider)

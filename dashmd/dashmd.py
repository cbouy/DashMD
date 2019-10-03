#!/usr/bin/env python
# coding: utf-8

from bokeh.plotting import show
from bokeh.models.widgets import Tabs, Panel
from bokeh.layouts import row, column, grid
from .dashboard import Dashboard


def create_doc(doc, title, default_dir, update):
    """Creates a Bokeh document that the server will display"""
    doc.title = title
    document = Dashboard(default_dir)
    document.add_callbacks()

    def callback_load_dir(new_value):
        if document.anim_button.active:
            document.anim_button.label = "◼ Stop"
            document.anim_button.button_type = "danger"
            document.autocomp_results.children = []
            global mdinfo_callback
            # first update of the dashboard
            document.get_mdout_files()
            document.parse_mdinfo()
            for mdout in document.mdout_files:
                document.read_mdout_header(mdout)
            document.display_time()
            document.mdinfo_callback = doc.add_periodic_callback(document.update_dashboard, update*1e3)
        else:
            document.anim_button.label = "▶ Load"
            document.anim_button.button_type = "success"
            doc.remove_periodic_callback(document.mdinfo_callback)
    document.anim_button.on_click(callback_load_dir)

    # arrange display with tabs
    dashboard = Panel(
        title="Dashboard",
        child=grid([
        row([
            column([
                row([document.md_dir, document.anim_button]), document.autocomp_results, document.progressbar, document.pie
            ]),
            column(
                row([document.mdout_sel, document.mdout_button]),
                row([document.calc_speed]),
                row([document.eta]),
                row([document.last_update]),
                row([document.slider]),
            ),
        ]),
        #row([document.bar]),
        ])
    )
    temp_tab = Panel(title="Temperature", child=document.temperature_fig)
    press_tab = Panel(title="Pressure", child=document.pressure_fig)
    e_tab = Panel(title="Energy", child=document.energy_fig)
    vol_tab = Panel(title="Volume", child=document.vol_fig)
    dens_tab = Panel(title="Density", child=document.density_fig)
    rmsd_tab = Panel(title="RMSD", child=grid([column([
        row([document.rmsd_top, document.rmsd_traj, document.rmsd_button]),
        document.rmsd_fig
    ])]))
    tabs = Tabs(tabs=[ dashboard, rmsd_tab, temp_tab, press_tab, e_tab, vol_tab, dens_tab])
    doc.add_root(tabs)

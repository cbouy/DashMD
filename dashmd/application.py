import logging, os
from bokeh.models.widgets import Tabs, Panel
from bokeh.layouts import row, column, grid
from dashboard import Dashboard

log = logging.getLogger("dashmd")


def create_app(doc, default_dir="./", update=10, port=5100):
    """Creates a Bokeh document that the server will display"""
    # start loading the dashboard
    log.debug(f"Creating Bokeh app")
    log.debug(f"Default directory: {os.path.realpath(default_dir)}")
    log.debug(f"Update rate for the dashboard: {update} seconds")
    doc.title = "DashMD"
    document = Dashboard(default_dir, port)

    def callback_load_dir(new_value):
        if document.anim_button.active:
            document.anim_button.label = "◼ Stop"
            document.anim_button.button_type = "danger"
            document.autocomp_results.children = []
            # first update of the dashboard
            document.get_mdout_files()
            document.parse_mdinfo()
            for mdout in document.mdout_files[:document.slider.value]:
                document.read_mdout_header(mdout)
            document.display_simulations_length()
            document.view_structure()
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
            column([document.md_dir, document.autocomp_results]),
            document.anim_button,
        ]),
        row([
            column([document.pie]),
            column([
                document.progressbar,
                document.calc_speed,
                document.eta,
                document.last_update,
                document.slider,
            ]),
        ]),
        row([document.bar]),
        row([document.mdout_sel, document.mdout_button]),
        ], sizing_mode="scale_both")
    )
    temp_tab = Panel(title="Temperature", child=document.temperature_fig)
    press_tab = Panel(title="Pressure", child=document.pressure_fig)
    e_tab = Panel(title="Energy", child=document.energy_fig)
    vol_tab = Panel(title="Volume", child=document.vol_fig)
    dens_tab = Panel(title="Density", child=document.density_fig)
    rmsd_tab = Panel(title="RMSD", child=grid([column([
        row([document.topology, document.trajectory, column(document.mask, document.rmsd_button)]),
        document.rmsd_fig,
    ])]))
    view_tab = Panel(title="View", child=grid([
        column([
            row([document.topology, document.rst_traj, document.view_button, document.ngl_help_button]),
            row([document.view_canvas, document.ngl_help_div])
        ])
    ]))
    tabs = Tabs(tabs=[ dashboard, view_tab, rmsd_tab, temp_tab, press_tab, e_tab, vol_tab, dens_tab])
    doc.add_root(tabs)

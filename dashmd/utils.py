import os, logging, copy, re
from datetime import datetime
from multiprocessing import cpu_count
import numpy as np
from bokeh.models import HoverTool
from bokeh.palettes import brewer

# number of workers for calculations
max_workers = cpu_count()
# size of figures
size = (800,500)
# colorpalette
palette = brewer['Set1'][9]
# tooltips on hover
tooltips = [
    ("Step", "@Nsteps"),
    ("Time (ps)", "@Time"),
    ("Temperature (K)", "@Temperature"),
    ("Pressure", "@Pressure"),
    ("Etot", "@Etot"),
    ("EKtot", "@EKtot"),
    ("EPtot", "@EPtot"),
    ("Volume", "@Volume"),
    ("Density", "@Density"),
]
#
empty_mddata_dic = {k:[] for k in [
    "Nsteps", "Time", "Temperature", "Pressure",
    "Etot", "EKtot", "EPtot",
    "Volume", "Density",
]}

class BokehFilter(logging.Filter):
    """Filter bokeh warning messages"""
    def filter(self,record):
        # filter messages about displaying empty buttons
        return False if "Layout has no children" in record.msg else True

class TornadoFilter(logging.Filter):
    """Filter tornado warning messages"""
    def filter(self,record):
        # filter missing favicon
        return False if "favicon.ico" in record.msg else True

# Add the filters to the root logger
bokeh_logger = logging.getLogger("bokeh")
for handler in bokeh_logger.handlers:
    handler.addFilter(BokehFilter())
tornado_logger = logging.getLogger("tornado")
for handler in tornado_logger.handlers:
    handler.addFilter(TornadoFilter())


def readlines_reverse(filename):
    """Generator that reads a file from end to begining"""
    with open(filename) as qfile:
        qfile.seek(0, os.SEEK_END)
        position = qfile.tell()
        line = ''
        while position >= 0:
            qfile.seek(position)
            next_char = qfile.read(1)
            if next_char == "\n":
                yield line[::-1]
                line = ''
            else:
                line += next_char
            position -= 1
        yield line[::-1]


# JS function to compute the moving average on 10% of total points
moving_avg_func = """
    function movingAvg(array, count, qualifier){

        // calculate average for subarray
        var avg = function(array, qualifier){
            var sum = 0, count = 0, val;
            for (var i in array){
                val = array[i];
                if (!qualifier || qualifier(val)){
                    sum += val;
                    count++;
                }
            }
            return sum / count;
        };

        var result = [], val;

        // calculate average for each subarray and add to result
        for (var i=0, len=array.length - count; i <= len; i++){
            val = avg(array.slice(i, i + count), qualifier);
            if (!isNaN(val)){
                result.push(val);
            }
        }
        return result;
    }

    if (xs.length < 200)
        return xs;
    else
        var count = Math.round(0.1 * xs.length);
        return movingAvg(xs, count);
"""

# colors
def clamp(val, minimum=0, maximum=255):
    if val < minimum:
        return minimum
    if val > maximum:
        return maximum
    return round(val)


def colorscale(hexstr, scalefactor):
    """
    Scales a hex string by ``scalefactor``. Returns scaled hex string.
    To darken the color, use a float value between 0 and 1.
    To brighten the color, use a float value greater than 1.
    """
    hexstr = hexstr.strip('#')
    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr
    r, g, b = int(hexstr[:2], 16), int(hexstr[2:4], 16), int(hexstr[4:], 16)
    r = clamp(r * scalefactor)
    g = clamp(g * scalefactor)
    b = clamp(b * scalefactor)
    return "#%02x%02x%02x" % (r, g, b)


# create hovertool
def make_hover(renderers, tooltips=tooltips):
    hover = HoverTool(
        renderers=renderers,
        mode="vline",
        tooltips=tooltips
    )
    return hover


def get_stepsize(traj, min_points=200):
    """Returns a stepsize to display at least min_points data points on the graph"""
    n = traj.n_frames
    if n <= min_points:
        return 1
    else:
        return n // min_points


def compute_rmsd(frame, ref):
    """Compute RMSD between a reference and a frame"""
    return ref.rmsd(frame)


def parse_md_data(line):
    """Parse data from a MD simulation mdout file"""
    data = copy.deepcopy(empty_mddata_dic)
    re1 = re.search(r"NSTEP =\s*(\d+)\s+TIME\(PS\) =\s*([\.0-9]+)\s+TEMP\(K\) =\s*([\.0-9]+)\s+PRESS =\s*(-?[\.0-9]+)", line)
    if re1:
        data["Nsteps"].append(int(re1.group(1)))
        data["Time"].append(float(re1.group(2)))
        data["Temperature"].append(float(re1.group(3)))
        data["Pressure"].append(float(re1.group(4)))
    re2 = re.search(r"Etot\s+=\s*(-?[\.0-9]+)\s+EKtot\s+=\s*(-?[\.0-9]+)\s+EPtot\s+=\s*(-?[\.0-9]+)", line)
    if re2:
        data["Etot"].append(float(re2.group(1)))
        data["EKtot"].append(float(re2.group(2)))
        data["EPtot"].append(float(re2.group(3)))
    re3 = re.search(r"EKCMT\s+=\s*(-?[\.0-9]+)\s+VIRIAL\s+=\s*(-?[\.0-9]+)\s+VOLUME\s+=\s*(-?[\.0-9]+)", line)
    if re3:
        data["Volume"].append(float(re3.group(3)))
    re4 = re.search(r"\s+Density\s+=\s*([\.0-9]+)", line)
    if re4:
        data["Density"].append(float(re4.group(1)))
    return data


def parse_min_data(line):
    """Parse data from a minimization mdout file"""
    data = copy.deepcopy(empty_mddata_dic)
    re1 = re.search(r"^\s+(\d+)\s+(-?[\.0-9]+E[+\-]\d+)\s+-?[\.0-9]+E[+\-]\d+\s+-?[\.0-9]+E[+\-]\d+\s+[A-Z0-9]+\s+\d+$", line)
    if re1:
        data["Nsteps"].append(int(re1.group(1)))
        data["Etot"].append(float(re1.group(2)))
        for key in ["Time", "Temperature", "Pressure", "EKtot", "EPtot", "Volume", "Density"]:
            data[key].append(np.nan)
    return data


# print time since last edit of file
def pretty_date(last):
        now = datetime.now()
        last = datetime.fromtimestamp(last)
        d = now - last
        total_seconds = abs(d.total_seconds())
        days, remainder = divmod(total_seconds, 24*3600)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days < 1:
            if hours < 1:
                if minutes < 1:
                    if seconds < 10:
                        return "just now"
                    return f"{seconds:.0f} second{'s' if seconds > 1 else ''} ago"
                return f"{minutes:.0f} minute{'s' if minutes > 1 else ''} ago"
            return f"{hours:.0f} hour{'s' if hours > 1 else ''} ago"
        return f"{days:.0f} day{'s' if days > 1 else ''} ago"

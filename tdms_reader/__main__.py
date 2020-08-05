import argparse
import glob
import os
import re
import sys
from collections import defaultdict

import pandas as pd
import simplelogging
from bokeh.models import (
    ColumnDataSource,
    Whisker,
    HoverTool,
    Band,
)
from bokeh.plotting import figure, output_file, show
from nptdms import TdmsFile
from scipy import integrate

# logging
log = simplelogging.get_logger()

# load the tdms file

ABS_PATH = os.path.abspath(os.getcwd())
CSV_PATH = os.path.join(ABS_PATH, "CSV DATA")
PLOT_PATH = os.path.join(ABS_PATH, "PLOT DATA")


def create_arg_parser():
    """"Creates and returns the ArgumentParser object."""

    parser = argparse.ArgumentParser(
        description="Computation and Graphing of TDMS CO2 Data."
    )
    parser.add_argument("--data", type=str, help="Path to the data directory.")
    return parser


def output_directories():
    for out_paths in [CSV_PATH, PLOT_PATH]:
        try:
            os.mkdir(out_paths)
        except FileExistsError:
            log.info(f"Already created {out_paths}")
            pass


def vivdict():
    return defaultdict(vivdict)


def load_data(path):
    # Handles nested dictionaries for us
    output_directories()
    sample_dict = vivdict()
    directory_listing = [
        os.path.join(path, directory) for directory in os.listdir(path)
    ]
    for directory in directory_listing:
        """
        Example:
        directory == '2020.07.30_14.23.02_2E2M_Control 3'
        sample == 2E2M
        sample_type == Control
        sample_rep == 3
        """
        sample = re.split(r"[_\-]", directory)[-2]
        sample_type = " ".join(re.split(r"[_\-]", directory)[-1].split(" ")[0:-1])
        sample_rep = " ".join(re.split(r"[_\-]", directory)[-1].split(" ")[-1])

        # Get rid of Index file
        file = list(
            filter(lambda x: not re.findall(r"index", x), glob.glob(f"{directory}\*"))
        )
        if len(file) > 1:
            log(f"Multiple files not supported. Split up {directory}")
        else:
            file = file[0]
        # Load the TDMS File
        try:
            tdms_file = TdmsFile(file)
            df = tdms_file.as_dataframe()
            df = df[
                list(filter(lambda x: re.findall(r"Timestampe|CO2", x), df.columns))
            ]
            df.columns = ["CO2", "Time"]
            df["Time"] = df["Time"].sub(df["Time"].min()).sub(40)
            df.set_index("Time", inplace=True)
            initial_condition = df[:-30].mean()
            df = df.sub(initial_condition)
            sample_dict[sample][sample_type][sample_rep] = df

        except [FileNotFoundError, OSError] as e:
            log(f"{e}\t File: {file} \t Directory: {directory}")
    return sample_dict


def write_and_plot(sample_dict):
    # Merge all the sample data
    sample_families = list(sample_dict.keys())
    composite_data = vivdict()
    integral_data = []
    std_data = {}

    for family in sample_families:
        for method, _ in sample_dict[family].items():
            composite_data[family][method] = cd = pd.concat(
                sample_dict[family][method], axis=1
            ).apply(lambda g: pd.Series.interpolate(g, method="cubic"))

            # Integral
            heating = cd[0:150]
            row_integral = (
                heating.ewm(span=5).mean().apply(lambda g: integrate.trapz(g))
            )
            row_integral_std = row_integral.std()
            integral = pd.DataFrame(
                {"Integral": row_integral.mean(), "STD": row_integral_std},
                index=[f"{family}_{method}"],
            )
            integral["lower"] = row_integral.mean() - row_integral_std
            integral["upper"] = row_integral.mean() + row_integral_std
            integral_data.append(integral)

            # Mean Data
            cd_mean = cd.mean(axis=1).reset_index()
            cd_mean.columns = ["Time", "CO2"]
            cd_mean.to_csv(
                os.path.join(CSV_PATH, f"{family}_{method}.csv"), sep=",", index=False
            )

            # STD Data
            cd_mean = cd.mean(axis=1)
            source_data = cd_mean.reset_index()
            source_data.columns = ["Time", "CO2"]
            cd_std = cd.std(axis=1).rolling(window=3).mean().fillna(method="backfill")
            source_data["lower"] = source_data.CO2 - cd_std.reset_index()[0]
            source_data["upper"] = source_data.CO2 + cd_std.reset_index()[0]
            std_data[f"{family} {method} STD"] = cd_std

            # Graphing our data
            output_file(os.path.join(PLOT_PATH, f"{family}-{method}.html"))
            source = ColumnDataSource(source_data)
            p = figure(
                title=f"{family} {method}",
                x_axis_label="Time",
                y_axis_label="CO2 Release",
                background_fill_color="#efefef",
            )
            p.line(
                source=source, x="Time", y="CO2",
            )
            band = Band(
                base="Time",
                lower="lower",
                upper="upper",
                source=source,
                level="underlay",
                fill_alpha=1.0,
                line_width=1,
                line_color="black",
            )
            p.add_layout(band)
            p.title.text = f"{family} {method}"
            p.xgrid[0].grid_line_color = None
            p.ygrid[0].grid_line_alpha = 0.5
            p.xaxis.axis_label = "Time"
            p.yaxis.axis_label = "CO_2"

            show(p)

    integral_df = pd.concat(integral_data).reset_index()
    groups = integral_df["index"]
    output_file(os.path.join(PLOT_PATH, f"Integral Data.html"))
    source = ColumnDataSource(integral_df)
    p = figure(
        x_range=groups,
        toolbar_location=None,
        title="CO2 Integral",
        background_fill_color="#efefef",
    )
    p.circle(
        x="index", y="Integral", color="red", fill_alpha=0.2, size=10, source=source
    )
    p.add_layout(
        Whisker(
            source=source, base="index", upper="upper", lower="lower", level="overlay"
        )
    )
    p.xaxis.major_label_orientation = "vertical"
    p.y_range.start = integral_df["Integral"].min() - integral_df["STD"].max() - 5
    p.y_range.end = integral_df["Integral"].max() + integral_df["STD"].max() + 5

    hover = HoverTool()
    hover.tooltips = [("Sample", "@index"), ("Value", "@Integral"), ("STD", "@STD")]

    hover.mode = "vline"

    p.add_tools(hover)
    show(p)


if __name__ == "__main__":
    arg_parser = create_arg_parser()
    parsed_args = arg_parser.parse_args(sys.argv[1:])
    if parsed_args:
        if os.path.exists(parsed_args.data):
            try:
                raw_dta = load_data(parsed_args.data)
                write_and_plot(sample_dict=raw_dta)
            except TypeError as e :
                log.debug(f"{e}")
    else:
        log.debug(f"Doesn't look like you entered a proper directory: {parsed_args}")

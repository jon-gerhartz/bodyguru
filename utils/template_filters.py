from datetime import datetime


def fmt_dt(ts, fmt_str):
    fmtd_dt = ts.strftime(fmt_str)
    return fmtd_dt


def fmt_dt_str(dt_str, dt_str_fmt, fmt_to):
    dt_obj = datetime.strptime(dt_str, dt_str_fmt)
    fmtd_dt = dt_obj.strftime(fmt_to)
    return fmtd_dt

from components import render_length_converter, render_temperature_converter


def render_units(texts: dict[str, str]) -> None:
    render_length_converter(texts)
    render_temperature_converter(texts)

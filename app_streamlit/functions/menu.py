import streamlit as st
from streamlit_option_menu import option_menu

def streamlit_menu(example=1, title=None, options=None, icons=None, onChange=None):
    if options is None:
        options = ["Home", "Scholarships", "Contact"]
    if icons is None:
        icons = ["house", "book", "envelope"]

    if example == 1:
        # Sidebar menu
        with st.sidebar:
            selected = option_menu(
                menu_title=title,
                options=options,
                icons=icons,
                menu_icon="cast",
                default_index=0,
                key="menu_sidebar",
            )
        return selected

    if example == 2:
        # Horizontal menu (default style)
        selected = option_menu(
            menu_title=title,
            options=options,
            icons=icons,
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            key="menu_horizontal",
        )
        return selected

    if example == 3:
        # Horizontal menu (custom style)
        selected = option_menu(
            menu_title=title,
            options=options,
            icons=icons,
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "green"},
            },
            key="menu_custom",
        )
        return selected
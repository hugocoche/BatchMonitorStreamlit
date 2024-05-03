import streamlit as st

st.set_page_config(layout="wide", page_icon=":shark:")

st.write("# Welcome dear User ")

st.write(
    """
            This is a simple web application that allows you to create batches of items and visualize them and
            to resolve some linear programming problems.
            """
)

st.write("There is actually three pages in this web application : ")
st.write("1. The first page allows you to construct the demand.")
st.write(
    "2. The second page allows you to create batches of items. Btw dont forget to clean the old data before creating a new batch."
)
st.write(
    "3. The third page allows you to visualize the batches of items you created and the solutions of the different linear programming problems.(warning: sometimes you will just need to reload the batch list and the demand to see the results)"
)

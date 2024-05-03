from io import BytesIO
import streamlit as st
import pandas as pd
import os
from BatchMonitor import ItemListRequest, ItemRequest  # type: ignore
import pickle

if (
    st.radio(
        "Select the way you want to create your Demand", ["Manually", "From a file"]
    )
    == "Manually"
):
    b1, b2, b3, _ = st.columns([1, 1, 1, 1])

    Item_requested = b1.text_input(
        "Item Requested", value=None, placeholder="Type a name..."
    )
    if Item_requested is not None:
        Item_requested = Item_requested.capitalize().rstrip()

    Item_requested_quantity_min = b2.number_input(
        "Minimal Requested Quantity (Default None)",
        value=None,
        placeholder="Type a value...",
    )
    Item_requested_quantity_max = b3.number_input(
        "Maximal Requested Quantity (default inf)",
        value=1.797e308,
        placeholder="Type a value ...",
    )

    if Item_requested_quantity_max >= 10**7:
        Item_requested_quantity_max = float(
            "{:.2e}".format(Item_requested_quantity_max)
        )

    if "deja_vu" not in st.session_state:
        st.session_state["deja_vu"] = []

    if "Demand" not in st.session_state:
        st.session_state["Demand"] = None

    c1, c2, _ = st.columns([1, 1, 1])

    if c1.button("Construct demand"):
        if (
            Item_requested is not None
            and Item_requested_quantity_min is not None
            and Item_requested_quantity_max is not None
        ):
            if Item_requested not in st.session_state["deja_vu"]:
                if "Demand" not in st.session_state or not isinstance(
                    st.session_state["Demand"], ItemListRequest
                ):
                    st.session_state["Demand"] = ItemListRequest(
                        [
                            ItemRequest(
                                Item_requested,
                                Item_requested_quantity_min,
                                Item_requested_quantity_max,
                            )
                        ]
                    )
                    st.session_state["deja_vu"].append(Item_requested)
                else:
                    st.session_state["Demand"].items.append(
                        ItemRequest(
                            Item_requested,
                            Item_requested_quantity_min,
                            Item_requested_quantity_max,
                        )
                    )
                    st.session_state["deja_vu"].append(Item_requested)
            else:
                st.write("Item already in the list")
        else:
            st.write("Please fill all the fields")

    if c2.button("remove previous item"):
        if st.session_state["Demand"] is not None and isinstance(
            st.session_state["Demand"], ItemListRequest
        ):
            if len(st.session_state["Demand"]) == 0:
                del st.session_state["Demand"]
                st.write("No item to remove")
            else:
                st.session_state["Demand"].items.pop()
                st.session_state["deja_vu"].pop()
        st.rerun()

else:

    if "deja_vu" not in st.session_state:
        st.session_state["deja_vu"] = []

    if "Demand" not in st.session_state:
        st.session_state["Demand"] = None

    if (
        st.selectbox(
            "Select the type of the file you want to upload",
            ["csv/xlsx", "json"],
        )
        == "csv/xlsx"
    ):

        st.write(
            " This feature is still in development, to use it correctly you have to create a file with the following structure :"
        )
        st.write(
            "    - The first row should is not really important, it can be used to describe the content of the columns"
        )
        st.write(
            "    - The following rows should contain the name of the items and their quantity minimum and maximum (maximum is optional, default value is inf) "
        )

        uploaded_file: pd.DataFrame | BytesIO | None = None

        uploaded_file = st.file_uploader("Upload a file", type=["csv", "xlsx"])

        b1, _ = st.columns([1, 1])

        if uploaded_file is not None:
            _, file_extension = os.path.splitext(uploaded_file.name)
            if file_extension == ".csv":
                uploaded_file = pd.DataFrame(pd.read_excel(uploaded_file, index_col=0))
            elif file_extension == ".xlsx":
                uploaded_file = pd.DataFrame(pd.read_excel(uploaded_file, index_col=0))

            if b1.button("construct demand"):
                for row in uploaded_file.itertuples():
                    Item_Name, Item_Quantity_min, Item_Quantity_max = (
                        row
                        if len(row) == 3
                        else [
                            row[0],
                            row[1],
                            round(float("{:.2e}".format(1.797e308)), 2),
                        ]
                    )
                    if Item_Name not in st.session_state["deja_vu"]:
                        if "Demand" not in st.session_state or not isinstance(
                            st.session_state["Demand"], ItemListRequest
                        ):
                            st.session_state["Demand"] = ItemListRequest(
                                [
                                    ItemRequest(
                                        Item_Name,
                                        Item_Quantity_min,
                                        Item_Quantity_max,
                                    )
                                ]
                            )
                            st.session_state["deja_vu"].append(Item_Name)
                        else:
                            st.session_state["Demand"].items.append(
                                ItemRequest(
                                    Item_Name,
                                    Item_Quantity_min,
                                    Item_Quantity_max,
                                )
                            )
                            st.session_state["deja_vu"].append(Item_Name)
                    else:
                        st.write("Item already in the list")
    else:

        uploaded_file = st.file_uploader("Upload a file", type=["json"])

        if uploaded_file is not None:
            st.session_state["Demand"] = ItemListRequest.from_json(
                f"{uploaded_file.name}"
            )


if st.session_state["Demand"] is not None and "Demand" in st.session_state:
    for item in st.session_state["Demand"].items:
        demand_info = pd.DataFrame(
            {
                "Item Name": [item.name],
                "Item Quantity min": [item.minimum_quantity],
                "Item Quantity max": [item.maximum_quantity],
            }
        )
        demand_info = demand_info.set_index("Item Name")
        st.table(demand_info)

if st.sidebar.button("Clear demand"):
    st.session_state["deja_vu"] = []
    del st.session_state["Demand"]
    st.rerun()

if st.sidebar.button("Export demand"):
    if len(st.session_state["Demand"]) > 0 and isinstance(
        st.session_state["Demand"], ItemListRequest
    ):
        with open("demand.pkl", "wb") as d:
            pickle.dump(st.session_state["Demand"], d)
        st.write("Demand exported ;) !")
    else:
        st.write(
            "object is not an instance of ItemListRequest or object is empty, export failed"
        )

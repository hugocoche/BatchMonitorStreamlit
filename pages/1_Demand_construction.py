import streamlit as st
import pandas as pd
import os
from BatchMonitor import ItemListRequest, ItemRequest  # type: ignore
import json

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

    if "Demand_list" not in st.session_state:
        st.session_state["Demand_list"] = None

    c1, c2, _ = st.columns([1, 1, 1])

    if c1.button("Construct demand"):
        if (
            Item_requested is not None
            and Item_requested_quantity_min is not None
            and Item_requested_quantity_max is not None
        ):
            if Item_requested not in st.session_state["deja_vu"]:
                if "Demand_list" not in st.session_state or not isinstance(
                    st.session_state["Demand_list"], ItemListRequest
                ):
                    st.session_state["Demand_list"] = ItemListRequest(
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
                    st.session_state["Demand_list"].items.append(
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
        if st.session_state["Demand_list"] is not None and isinstance(
            st.session_state["Demand_list"], ItemListRequest
        ):
            if len(st.session_state["Demand_list"]) == 0:
                del st.session_state["Demand_list"]
                st.write("No item to remove")
            else:
                st.session_state["Demand_list"].items.pop()
                st.session_state["deja_vu"].pop()
        st.rerun()

else:

    if "deja_vu" not in st.session_state:
        st.session_state["deja_vu"] = []

    if "Demand_list" not in st.session_state:
        st.session_state["Demand_list"] = None

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

        uploaded_file = st.file_uploader("Upload a file", type=["csv", "xlsx"])

        b1, _ = st.columns([1, 1])

        if uploaded_file is not None:
            _, file_extension = os.path.splitext(uploaded_file.name)
            if file_extension == ".csv":
                df = pd.DataFrame(pd.read_csv(uploaded_file, index_col=0))
            elif file_extension == ".xlsx":
                df = pd.DataFrame(pd.read_excel(uploaded_file, index_col=0))

            if b1.button("construct demand"):
                for row in df.itertuples():
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
                        if "Demand_list" not in st.session_state or not isinstance(
                            st.session_state["Demand_list"], ItemListRequest
                        ):
                            st.session_state["Demand_list"] = ItemListRequest(
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
                            st.session_state["Demand_list"].items.append(
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

        if st.button("construct demand"):
            if uploaded_file is not None:
                # st.session_state["Demand"] = ItemListRequest.from_json(
                #     f"{uploaded_file.name}"
                # )
                df = pd.DataFrame(pd.read_json(uploaded_file))
                st.table(df)
            else:
                st.write("Please upload a file")


if st.session_state["Demand_list"] is not None and "Demand_list" in st.session_state:
    for item in st.session_state["Demand_list"].items:
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
    del st.session_state["Demand_list"]
    st.rerun()


if st.session_state["Demand_list"] is not None and isinstance(
    st.session_state["Demand_list"], ItemListRequest
):
    st.session_state["export_demand_list"] = st.session_state["Demand_list"]
    json_export_demand_list = json.dumps(
        obj=st.session_state["export_demand_list"],
        default=lambda o: o.__dict__,
        indent=4,
    )
    if st.sidebar.download_button(
        "Download demand_list", json_export_demand_list, "demand_list.json", "json"
    ):
        pass

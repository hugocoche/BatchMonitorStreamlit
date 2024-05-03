import streamlit as st
import pandas as pd
from BatchMonitor import BatchLists, BatchCollection, Batch, Item_in_batch, create_df_from_json  # type: ignore
import json
import os

if (
    st.radio(
        "Select the way you want to create your batches", ["Manually", "From a file"]
    )
    == "Manually"
):
    st.markdown("## Seller")

    Seller_name = st.text_input("Seller Name", value=None, placeholder="Type a name...")

    st.markdown("## Batch Creation")

    Batch_Name = st.text_input("Batch Name", value=None, placeholder="Type a name...")

    Batch_Value = st.number_input(
        "Batch Value", value=None, placeholder="Type a value..."
    )

    exposant: int | float = 0
    if st.toggle("I need an exposant"):
        exposant = st.number_input("Exposant", value=0, placeholder="Type a value...")

    if Batch_Value is not None and exposant != 0:
        Batch_Value = Batch_Value * 10**exposant

    c1, c2, _ = st.columns([1, 2, 1])

    Item_Name = c1.text_input("Item Name", value=None, placeholder="Type a name...")
    if Item_Name is not None:
        Item_Name = Item_Name.lower()
    Item_Value = c2.number_input(
        "Item Quantity", value=None, placeholder="Type a value..."
    )

    if "already_seen" not in st.session_state:
        st.session_state["already_seen"] = []

    if "all_batches" not in st.session_state:
        st.session_state["all_batches"] = []

    if "batch_collection" not in st.session_state:
        st.session_state["batch_collection"] = None

    d1, d2, _ = st.columns(
        [
            1,
            1,
            1,
        ]
    )

    if d1.button("Create a batch"):
        if Seller_name and Batch_Name and Batch_Value and Item_Name and Item_Value:
            if (Seller_name, Batch_Name) not in st.session_state["already_seen"]:
                if "batch_collection" not in st.session_state or not isinstance(
                    st.session_state["batch_collection"], BatchLists
                ):
                    st.session_state["batch_collection"] = BatchLists(
                        batchlists=[
                            BatchCollection(
                                batch_list=[
                                    Batch(
                                        Batch_Name,
                                        Batch_Value,
                                        [Item_in_batch(Item_Name, Item_Value)],
                                    )
                                ],
                                seller=Seller_name,
                            )
                        ]
                    )
                else:
                    for batchcollection in st.session_state[
                        "batch_collection"
                    ].batchlists:
                        if batchcollection.seller == Seller_name:
                            batchcollection.batch_list.append(
                                Batch(
                                    Batch_Name,
                                    Batch_Value,
                                    [Item_in_batch(Item_Name, Item_Value)],
                                )
                            )
                            break
                    else:
                        st.session_state["batch_collection"].batchlists.append(
                            BatchCollection(
                                batch_list=[
                                    Batch(
                                        Batch_Name,
                                        Batch_Value,
                                        [Item_in_batch(Item_Name, Item_Value)],
                                    )
                                ],
                                seller=Seller_name,
                            )
                        )
                st.session_state["already_seen"].append((Seller_name, Batch_Name))
                st.session_state["all_batches"].append(
                    {
                        "Seller": Seller_name,
                        "Batch Name": Batch_Name,
                        "Batch Value": Batch_Value,
                        "Items": [{"Item Name": Item_Name, "Item Value": Item_Value}],
                    }
                )
            else:
                for batchcollection in st.session_state["batch_collection"].batchlists:
                    if batchcollection.seller == Seller_name:
                        for batch in batchcollection.batch_list:
                            if batch.name == Batch_Name and batch.price == Batch_Value:
                                for i, item in enumerate(batch.items):
                                    if item.name == Item_Name:
                                        st.write(
                                            "This item is already in the current batch"
                                        )
                                        break
                                batch.items.append(Item_in_batch(Item_Name, Item_Value))
                for lot in st.session_state["all_batches"]:
                    if (
                        lot["Seller"] == Seller_name
                        and lot["Batch Name"] == Batch_Name
                        and lot["Batch Value"] == Batch_Value
                    ):
                        if isinstance(lot["Items"], list):
                            if Item_Name not in [
                                item["Item Name"] for item in lot["Items"]
                            ]:
                                lot["Items"].append(
                                    {"Item Name": Item_Name, "Item Value": Item_Value}
                                )
        else:
            st.write("Please fill all the fields")

    if d2.button("Remove previous one"):
        if st.session_state["batch_collection"] is not None:
            last_batch_list = st.session_state["batch_collection"].batchlists[-1]
            if len(last_batch_list) > 0:
                last_batch_list.batch_list[-1].items.pop()
                st.session_state["all_batches"][-1]["Items"].pop()
                if len(st.session_state["all_batches"][-1]["Items"]) == 0:
                    st.session_state["all_batches"].pop()
                    st.session_state["batch_collection"].batchlists.pop()
                    st.session_state["already_seen"].pop()
            else:
                st.write("No item to remove")
            st.rerun()

else:

    if "already_seen" not in st.session_state:
        st.session_state["already_seen"] = []

    if "all_batches" not in st.session_state:
        st.session_state["all_batches"] = []

    if "batch_collection" not in st.session_state:
        st.session_state["batch_collection"] = None

    b1, _ = st.columns([1, 1])

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
        st.write("    - The first row should contain the names of the batches")
        st.write(
            "    - The following rows should contain the name of the items and their values"
        )
        st.write("    - The last but one row should contain the values of the batches")
        st.write(
            "    - The last row should contain the name(s) of the seller(s) for each batch"
        )

        uploaded_file = st.file_uploader("Upload a file", type=["csv", "xlsx"])

        if uploaded_file is not None:
            _, file_extension = os.path.splitext(uploaded_file.name)
            if file_extension == ".csv":
                df = pd.DataFrame(pd.read_csv(uploaded_file, index_col=0))
            elif file_extension == ".xlsx":
                df = pd.DataFrame(pd.read_excel(uploaded_file, index_col=0))

    else:

        uploaded_file = st.file_uploader("Upload a file", type=["json"])
        if uploaded_file is not None:
            json_df = pd.read_json(uploaded_file)
            st.write(json_df)
            df = create_df_from_json(json_df)

    if uploaded_file is not None:
        for Numbers in df.iloc[:-2].values.tolist():
            if not all(isinstance(x, (int, float)) for x in Numbers):
                st.write("Please make sure all values are numbers")
                break
        else:
            if b1.button("Create batches"):
                for Batch_Name, Batch_Value, Seller_name in zip(
                    df.columns.tolist(),
                    df.iloc[-2].tolist(),
                    df.iloc[-1].tolist(),
                ):
                    for Item_Name, Item_Value in zip(
                        df.index[:-2].tolist(),
                        df[Batch_Name].iloc[:-2].tolist(),
                    ):
                        if (Seller_name, Batch_Name) not in st.session_state[
                            "already_seen"
                        ]:
                            if (
                                "batch_collection" not in st.session_state
                                or not isinstance(
                                    st.session_state["batch_collection"], BatchLists
                                )
                            ):
                                st.session_state["batch_collection"] = BatchLists(
                                    batchlists=[
                                        BatchCollection(
                                            batch_list=[
                                                Batch(
                                                    Batch_Name,
                                                    Batch_Value,
                                                    [
                                                        Item_in_batch(
                                                            Item_Name, Item_Value
                                                        )
                                                    ],
                                                )
                                            ],
                                            seller=Seller_name,
                                        )
                                    ]
                                )
                                st.session_state["already_seen"].append(
                                    (Seller_name, Batch_Name)
                                )
                            else:
                                for batchcollection in st.session_state[
                                    "batch_collection"
                                ].batchlists:
                                    if batchcollection.seller == Seller_name:
                                        batchcollection.batch_list.append(
                                            Batch(
                                                Batch_Name,
                                                Batch_Value,
                                                [Item_in_batch(Item_Name, Item_Value)],
                                            )
                                        )
                                        break
                                else:
                                    st.session_state[
                                        "batch_collection"
                                    ].batchlists.append(
                                        BatchCollection(
                                            batch_list=[
                                                Batch(
                                                    Batch_Name,
                                                    Batch_Value,
                                                    [
                                                        Item_in_batch(
                                                            Item_Name, Item_Value
                                                        )
                                                    ],
                                                )
                                            ],
                                            seller=Seller_name,
                                        )
                                    )
                            st.session_state["already_seen"].append(
                                (Seller_name, Batch_Name)
                            )
                            st.session_state["all_batches"].append(
                                {
                                    "Seller": Seller_name,
                                    "Batch Name": Batch_Name,
                                    "Batch Value": Batch_Value,
                                    "Items": [
                                        {
                                            "Item Name": Item_Name,
                                            "Item Value": Item_Value,
                                        }
                                    ],
                                }
                            )
                        else:
                            for batchcollection in st.session_state[
                                "batch_collection"
                            ].batchlists:
                                if batchcollection.seller == Seller_name:
                                    for batch in batchcollection.batch_list:
                                        if (
                                            batch.name == Batch_Name
                                            and batch.price == Batch_Value
                                        ):
                                            batch.items.append(
                                                Item_in_batch(Item_Name, Item_Value)
                                            )
                            for sous_liste in st.session_state["all_batches"]:
                                if (
                                    sous_liste["Batch Name"] == Batch_Name
                                    and sous_liste["Batch Value"] == Batch_Value
                                ):
                                    if isinstance(sous_liste["Items"], list):
                                        sous_liste["Items"].append(
                                            {
                                                "Item Name": Item_Name,
                                                "Item Value": Item_Value,
                                            }
                                        )
                st.rerun()

for batch in st.session_state["all_batches"]:
    st.markdown(
        f"#### {batch['Seller']} - {batch['Batch Name']} - Value : {batch['Batch Value']} dollars"
    )
    if "Items" in batch:
        batch_info = pd.DataFrame(batch["Items"])
        batch_info = batch_info.set_index("Item Name")
        st.table(batch_info)

if st.sidebar.button("Clear batches"):
    st.session_state["all_batches"] = []
    st.session_state["already_seen"] = []
    del st.session_state["batch_collection"]
    st.rerun()

if st.session_state["batch_collection"] is not None and isinstance(
    st.session_state["batch_collection"], BatchLists
):
    st.session_state["export_batch_collection"] = st.session_state["batch_collection"]
    json_export_batch_collection = json.dumps(
        obj=st.session_state["export_batch_collection"],
        default=lambda o: o.__dict__,
        indent=4,
    )
    if st.sidebar.download_button(
        "Download Batch list", json_export_batch_collection, "Batch_list.json", "json"
    ):
        pass

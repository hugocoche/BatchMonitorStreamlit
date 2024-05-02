import streamlit as st
import pandas as pd
from BatchMonitor import BatchLists, BatchCollection, Batch, Item_in_batch
import pickle
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

    exposant = 0
    if st.toggle("I need an exposant"):
        exposant = st.number_input("Exposant", value=0, placeholder="Type a value...")

    Batch_Value = Batch_Value * 10**exposant if exposant != 0 else Batch_Value

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
                                batch.items.append(Item_in_batch(Item_Name, Item_Value))
                for sous_liste in st.session_state["all_batches"]:
                    if (
                        sous_liste["Batch Name"] == Batch_Name
                        and sous_liste["Batch Value"] == Batch_Value
                    ):
                        if isinstance(sous_liste["Items"], list):
                            sous_liste["Items"].append(
                                {"Item Name": Item_Name, "Item Value": Item_Value}
                            )
                st.rerun()
        else:
            st.write("Please fill all the fields")

    if d2.button("Remove previous one"):
        if st.session_state["batch_collection"] is not None:
            last_batch_list = st.session_state["batch_collection"].batchlists[-1]
            if len(last_batch_list) > 0:
                last_batch_list.batch_list[-1].items.pop()
                st.session_state["all_batches"].pop()
            else:
                st.write("No item to remove")

    if st.sidebar.button("Clear batches"):
        st.session_state["all_batches"] = []
        st.session_state["already_seen"] = []
        del st.session_state["batch_collection"]
        st.write("All batches have been cleared")
        st.rerun()

    for batch in st.session_state["all_batches"]:
        st.markdown(
            f"#### {Seller_name} - {batch['Batch Name']} - Value : {batch['Batch Value']} dollars"
        )
        if "Items" in batch:
            batch_info = pd.DataFrame(batch["Items"])
            batch_info = batch_info.set_index("Item Name")
            st.table(batch_info)

    if st.sidebar.button("Export Batch list"):
        if st.session_state["batch_collection"] is not None and isinstance(
            st.session_state["batch_collection"], BatchLists
        ):
            with open("batch_collection.pkl", "wb") as f:
                pickle.dump(st.session_state["batch_collection"], f)
            st.write("batch list has been exported ;) !")
        else:
            st.write(
                "batch_collection is not an instance of BatchCollection, export failed."
            )
            st.write(
                f"batch_collection is of type {type(st.session_state['batch_collection'])}."
            )

else:
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

    if "already_seen" not in st.session_state:
        st.session_state["already_seen"] = []

    if "all_batches" not in st.session_state:
        st.session_state["all_batches"] = []

    if "batch_collection" not in st.session_state:
        st.session_state["batch_collection"] = None

    uploaded_file = st.file_uploader("Upload a file", type=["csv", "xlsx"])

    b1, b2, b3, _ = st.columns([1, 1, 1, 1])

    if uploaded_file is not None:
        _, file_extension = os.path.splitext(uploaded_file.name)
        if file_extension == ".csv":
            uploaded_file = pd.DataFrame(pd.read_csv(uploaded_file, index_col=0))
        elif file_extension == ".xlsx":
            uploaded_file = pd.DataFrame(pd.read_excel(uploaded_file, index_col=0))

        for Numbers in uploaded_file.iloc[:-2].values.tolist():
            if not all(isinstance(x, (int, float)) for x in Numbers):
                st.write("Please make sure all values are numbers")
                break
        else:
            if b1.button("Create batches"):
                for Batch_Name, Batch_Value, Seller_name in zip(
                    uploaded_file.columns.tolist(),
                    uploaded_file.iloc[-2].tolist(),
                    uploaded_file.iloc[-1].tolist(),
                ):
                    for Item_Name, Item_Value in zip(
                        uploaded_file.index[:-2].tolist(),
                        uploaded_file[Batch_Name].iloc[:-2].tolist(),
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
        st.write("All batches have been cleared")
        st.rerun()

    if st.sidebar.button("Export Batch list"):
        if st.session_state["batch_collection"] is not None and isinstance(
            st.session_state["batch_collection"], BatchLists
        ):
            with open("batch_collection.pkl", "wb") as f:
                pickle.dump(st.session_state["batch_collection"], f)
            st.write("batch list has been exported ;) !")
        else:
            st.write(
                "batch_collection is not an instance of BatchLists, export failed."
            )
            st.write(
                f"batch_collection is of type {type(st.session_state['batch_collection'])}."
            )

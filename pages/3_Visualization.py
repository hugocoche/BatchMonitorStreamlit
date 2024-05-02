import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import pickle
import copy
import os
from BatchMonitor import (
    BatchLists,
    BatchCollection,
    minBatchExpense,
    maxEarnings,
    ItemListRequest,
    createDatabaseFromBatchLists,
    indice_batch_current_seller,
    batch_list_global,
)


def original_prices(Batches: BatchLists, index) -> list:
    if Batches is not None and index is not None:
        st.session_state["original_prices"] = [
            batch.price for batch in Batches.batchlists[index].batch_list
        ]

    return st.session_state["original_prices"]


if st.sidebar.button("Load the the demand and the batches"):
    if os.path.exists("batch_collection.pkl") and os.path.exists("demand.pkl"):
        with open("batch_collection.pkl", "rb") as f:
            st.session_state["Batches"] = pickle.load(f)
        with open("demand.pkl", "rb") as d:
            st.session_state["Demand"] = pickle.load(d)
        st.write("Necessary loaded !")
    else:
        st.write("You need to export the demand and the batches first !")

if st.sidebar.button("Clear All"):
    default_values: list[tuple]
    default_values = [
        ("Batches", None),
        ("Demand", None),
        ("database", None),
        ("exchange_rate", 1.0),
        ("tax_rate", 0.0),
        ("custom_duty", 0.0),
        ("transport_fee", 0.0),
        ("Minimum_Expense", None),
        ("Maximum_Expense", None),
        ("Minimum_Benefit", None),
        ("Maximum_Benefit", None),
        ("price_constraints", {}),
        ("batch_constraints", {}),
    ]

    for key, default_value in default_values:
        if key in st.session_state:
            st.session_state[key] = default_value
    st.rerun()

if "price" not in st.session_state:
    st.session_state["price"] = 0

if "Batches" in st.session_state and st.session_state["Batches"] is not None:
    Batches_copy = copy.deepcopy(st.session_state["Batches"])
    st.session_state["database"] = createDatabaseFromBatchLists(Batches_copy)
    st.write("Database created from the batch list ")
    if len(st.session_state["database"].columns) < 12:
        st.table(st.session_state["database"])
    else:
        st.write("Dataframe too big to be showed")


@st.cache_data(experimental_allow_widgets=True, show_spinner=False)
def basic_graph(data: pd.DataFrame) -> alt.Chart:
    st.markdown("#### Visualisation of the batches")

    options = list(st.session_state["database"].index[:-1])
    options.insert(0, "All")
    option = st.selectbox("What do you want ?", options)

    data = []
    if option == "All":
        for i in range(len(st.session_state["database"]) - 1):
            for j in range(len(st.session_state["database"].columns)):
                data.append(
                    {
                        "index": st.session_state["database"].index[i],
                        "Batch": st.session_state["database"].columns[j],
                        "Quantity": st.session_state["database"].iloc[i, j],
                    }
                )
    else:
        for j in range(len(st.session_state["database"].columns)):
            data.append(
                {
                    "index": "default",
                    "Batch": st.session_state["database"].columns[j],
                    "Quantity": st.session_state["database"].iloc[
                        st.session_state["database"].index.get_loc(option), j
                    ],
                }
            )

    df = pd.DataFrame(data)

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Batch:N", axis=alt.Axis(labelAngle=-45)),
            y="Quantity:Q",
            color="index:N",
            tooltip=["index", "Batch", "Quantity"],
        )
        .properties(width="container", height=600)
    )

    st.altair_chart(chart, use_container_width=True)


if "database" in st.session_state and st.session_state["database"] is not None:
    basic_graph(st.session_state["database"])


if (
    "Batches" in st.session_state
    and st.session_state["Batches"] is not None
    and "Demand" in st.session_state
    and st.session_state["Demand"] is not None
    and "database" in st.session_state
    and st.session_state["database"] is not None
):
    """Choice of the seller."""
    if "selected_seller" not in st.session_state:
        st.session_state["selected_seller"] = st.selectbox(
            "Which seller to choose ?",
            ["All"]
            + [batches.seller for batches in st.session_state["Batches"].batchlists],
        )
    else:
        st.session_state["selected_seller"] = st.selectbox(
            "Which seller to choose ?",
            [batches.seller for batches in st.session_state["Batches"].batchlists]
            + ["All"],
            index=(
                (
                    [
                        batches.seller
                        for batches in st.session_state["Batches"].batchlists
                    ]
                    + ["All"]
                ).index(st.session_state["selected_seller"])
                if st.session_state["selected_seller"]
                in ["All"]
                + [batches.seller for batches in st.session_state["Batches"].batchlists]
                else 1
            ),
        )

    seller = st.session_state["selected_seller"]

    """Choice of the method to use."""
    method = st.selectbox("What method you want ?", ["Primal", "Dual"])

    default_values = [
        ("exchange_rate", 1.0),
        ("tax_rate", 0.0),
        ("custom_duty", 0.0),
        ("transport_fee", 0.0),
        ("Minimum_Expense", None),
        ("Maximum_Expense", None),
        ("Minimum_Benefit", None),
        ("Maximum_Benefit", None),
        ("price_constraints", dict()),
        ("batch_constraints", dict()),
        ("category_of_variables", "Continuous"),
    ]

    for key, default_value in default_values:
        if key not in st.session_state:
            st.session_state[key] = default_value

    if st.toggle("More options"):
        """Options for the optimization problem. You can set the exchange rate, tax rate, custom duty and transport fee for exemple."""
        """You can choose to fix the same rate for all the batches or to fix different rates for each seller."""
        o1, _ = st.columns([1, 1])
        b1, b2, b3, b4, b5, b6, _ = st.columns([1, 1, 1, 1, 1, 1, 1])
        w1, _ = st.columns([2.0, 1])
        d1, d2, d3, d4, _ = st.columns([1, 1, 1, 1, 1])
        a1, _ = st.columns([1, 1])
        c1, c2, _ = st.columns([1, 1, 1])
        e1, e2, e3, e4, e5, _ = st.columns([1, 1, 1, 1, 1, 1])
        f1, f2, f3, f4, f5, _ = st.columns([1, 1, 1, 1, 1, 1])
        g1, _ = st.columns([1, 1])

        number_of_rates = o1.selectbox("Number of rates", ["One", "Multiple"])

        if number_of_rates == "One":
            exchange_rate = b1.number_input("exchange rate", value=1.0)
            tax_rate = b2.number_input("tax rate", value=0.0)
            custom_duty = b3.number_input("custom duty", value=0.0)
            transport_fee = b4.number_input("transport fee", value=0.0)

            st.session_state["exchange_rate"] = exchange_rate
            st.session_state["tax_rate"] = tax_rate
            st.session_state["custom_duty"] = custom_duty
            st.session_state["transport_fee"] = transport_fee

        elif number_of_rates == "Multiple":
            default_values = [
                ("exchange_rate_multiple", np.array([])),
                ("tax_rate_multiple", np.array([])),
                ("custom_duty_multiple", np.array([])),
                ("transport_fee_multiple", np.array([])),
            ]

            for key, default_value in default_values:
                if key not in st.session_state or not isinstance(
                    st.session_state[key], np.ndarray
                ):
                    st.session_state[key] = default_value

            exchange_rate = b1.number_input("exchange rate")
            tax_rate = b2.number_input("tax rate")
            custom_duty = b3.number_input("custom duty")
            transport_fee = b4.number_input("transport fee")

            if b5.button("Add values"):
                st.session_state["exchange_rate_multiple"] = np.append(
                    st.session_state["exchange_rate_multiple"], exchange_rate
                )
                st.session_state["tax_rate_multiple"] = np.append(
                    st.session_state["tax_rate_multiple"], tax_rate
                )
                st.session_state["custom_duty_multiple"] = np.append(
                    st.session_state["custom_duty_multiple"], custom_duty
                )
                st.session_state["transport_fee_multiple"] = np.append(
                    st.session_state["transport_fee_multiple"], transport_fee
                )

            st.session_state["exchange_rate"] = st.session_state[
                "exchange_rate_multiple"
            ]
            st.session_state["tax_rate"] = st.session_state["tax_rate_multiple"]
            st.session_state["custom_duty"] = st.session_state["custom_duty_multiple"]
            st.session_state["transport_fee"] = st.session_state[
                "transport_fee_multiple"
            ]

            df = pd.DataFrame(
                {
                    "exchange_rate": st.session_state["exchange_rate_multiple"],
                    "tax_rate": st.session_state["tax_rate_multiple"],
                    "custom_duty": st.session_state["custom_duty_multiple"],
                    "transport_fee": st.session_state["transport_fee_multiple"],
                }
            )

            w1.table(df)

            if b6.button("Clear Values"):
                st.session_state["exchange_rate_multiple"] = np.array([])
                st.session_state["tax_rate_multiple"] = np.array([])
                st.session_state["custom_duty_multiple"] = np.array([])
                st.session_state["transport_fee_multiple"] = np.array([])

        st.session_state["Minimum_Expense"] = d1.number_input(
            "Minimum Expense", value=None
        )
        st.session_state["Maximum_Expense"] = d2.number_input(
            "Maximum Expense", value=None
        )
        st.session_state["Minimum_Benefit"] = d3.number_input(
            "Minimum Benefit", value=None
        )
        st.session_state["Maximum_Benefit"] = d4.number_input(
            "Maximum Benefit", value=None
        )

        if a1.toggle("Constraints Creation"):
            if c1.checkbox("Batch constraint"):
                batch_name = e1.text_input(
                    "Batch name", value=None, placeholder="Type a name..."
                )
                min_quantity = e2.number_input(
                    "Minimum quantity", value=None, min_value=0
                )
                max_quantity = e3.number_input(
                    "Maximum quantity", value=None, max_value=None
                )
                if e4.button("Create batch constraint"):
                    if (
                        batch_name not in st.session_state["batch_constraints"].keys()
                        and batch_name is not None
                    ):
                        if min_quantity > max_quantity:
                            st.write(
                                "Minimum quantity must be less than maximum quantity"
                            )
                        st.session_state["batch_constraints"][batch_name] = (
                            min_quantity,
                            max_quantity,
                        )
                    else:
                        st.write("Batch constraint already created !")
                    info_1 = pd.DataFrame(
                        st.session_state["batch_constraints"]
                    ).transpose()
                    info_1 = info_1.rename(
                        columns={0: "Minimum quantity", 1: "Maximum quantity"}
                    )
                    st.table(info_1)

                if e5.button("Clear batch constraint"):
                    st.session_state["batch_constraints"] = {}

            if c2.checkbox("Price constraint"):
                object_name = f1.text_input(
                    "Item name", value=None, placeholder="Type a name..."
                )
                min_value = f2.number_input("Minimum value", value=0, min_value=0)
                max_value = f3.number_input("Maximum value", value=None, max_value=None)
                if f4.button("Create price constraint"):
                    if (
                        object_name not in st.session_state["price_constraints"].keys()
                        and object_name is not None
                    ):
                        if min_value > max_value:
                            st.write("Minimum value must be less than maximum value")
                        st.session_state["price_constraints"][object_name] = (
                            min_value,
                            max_value,
                        )
                    else:
                        st.write("Price constraint already created !")
                    info_2 = pd.DataFrame(
                        st.session_state["price_constraints"]
                    ).transpose()
                    info_2 = info_2.rename(
                        columns={0: "Minimum value", 1: "Maximum Value"}
                    )
                    st.table(info_2)

                if f5.button("Clear price constraint"):
                    st.session_state["price_constraints"] = {}

        else:
            default_values = [
                ("exchange_rate", 1),
                ("tax_rate", 0),
                ("custom_duty", 0),
                ("transport_fee", 0),
            ]

            for key, default_value in default_values:
                if key in st.session_state:
                    st.session_state[key] = default_value

        if g1.selectbox(" More than one type of variables ?", ["No", "Yes"]) == "No":
            st.session_state["category_of_variables"] = st.text_input(
                "Category of variables (Continuous, Integer)"
            )
            st.session_state["category_of_variables"] = st.session_state[
                "category_of_variables"
            ].capitalize()
        else:
            z1, z2, _ = st.columns([1, 1, 1])
            if "dictio_variable" not in st.session_state:
                st.session_state["dictio_variable"] = {}
            for batches in st.session_state["Batches"].batchlists:
                for batch in batches.batch_list:
                    if batch.name not in st.session_state["dictio_variable"].keys():
                        st.session_state["dictio_variable"][batch.name] = None

            if "compteur" not in st.session_state:
                st.session_state["compteur"] = 0
                st.session_state["Batch_name"] = [
                    name for name in st.session_state["dictio_variable"].keys()
                ]

            if st.session_state["Batch_name"]:
                batch_name = st.selectbox(
                    "Batch name",
                    st.session_state["Batch_name"],
                    key="batch_name_selectbox",
                )
                type_variable = z1.selectbox(
                    "Category of variable ",
                    ["Continuous", "Integer"],
                    key="type_variable_selectbox",
                )

                if z2.button("Append"):
                    st.session_state["dictio_variable"][batch_name] = type_variable
                    st.session_state["Batch_name"].remove(batch_name)
                    st.write(
                        f" you need to enter {len(st.session_state['Batch_name'])} type of variables"
                    )
                    st.rerun()

            if st.button("Reset"):
                st.session_state["dictio_variable"] = {
                    name: None for name in st.session_state["dictio_variable"].keys()
                }
                st.session_state["Batch_name"] = [
                    name for name in st.session_state["dictio_variable"].keys()
                ]
                st.rerun()

            if len(st.session_state["Batch_name"]) == 0:
                st.write("All the type of variables are entered")
                st.session_state["category_of_variables"] = st.session_state[
                    "dictio_variable"
                ]
                st.session_state["compteur"] = 0

            df = pd.DataFrame(
                list(st.session_state["dictio_variable"].items()),
                columns=["Batch Name", "Variable Type"],
            )
            df = df.set_index("Batch Name")
            st.table(df)

    """Variation of the prices of the lots."""
    if "Mini" and "Maxi" and "step" not in st.session_state:
        st.session_state["Mini"] = 1
        st.session_state["Maxi"] = -1
        st.session_state["step"] = 0

    a1, a2, a3, _ = st.columns([1, 1, 1, 1])
    st.session_state["Mini"] = a1.number_input(
        "Minimum", value=-1, max_value=st.session_state.get("Maxi", 1)
    )
    st.session_state["Maxi"] = a2.number_input(
        "Maximum", value=1, min_value=st.session_state["Mini"]
    )
    st.session_state["step"] = a3.number_input("Step", value=0, min_value=0)

    if st.toggle("I need an exposant (only for minimum and maximum)"):
        st.session_state["exposant"] = st.number_input(
            "Exposant", value=0, placeholder="Type a value..."
        )
        st.session_state["Mini"] = (
            st.session_state["Mini"] * 10 ** st.session_state["exposant"]
            if st.session_state["exposant"] != 0
            else st.session_state["Mini"]
        )
        st.session_state["Maxi"] = (
            st.session_state["Maxi"] * 10 ** st.session_state["exposant"]
            if st.session_state["exposant"] != 0
            else st.session_state["Maxi"]
        )

    st.session_state["price"] = st.number_input(
        "Variation",
        value=0,
        min_value=st.session_state["Mini"],
        max_value=st.session_state["Maxi"],
        step=st.session_state["step"],
    )

    if seller == "All":
        st.session_state["Batches_used"] = batch_list_global(
            st.session_state["database"]
        ).batchlists[0]
        og_price = [
            batch.price for batch in st.session_state["Batches_used"].batch_list
        ]
    else:
        index = indice_batch_current_seller(st.session_state["Batches"], seller)
        st.session_state["Batches_used"] = st.session_state["Batches"].batchlists[index]
        og_price = original_prices(st.session_state["Batches"], index)


@st.cache_data(experimental_allow_widgets=True, show_spinner=False)
def graph_optimization_batches(
    Batches: BatchCollection,
    demand_list: ItemListRequest,
    price,
    og_price,
    method,
    category_of_variables,
    exchange_rate,
    tax_rate,
    customs_duty,
    transport_fee,
    minimum_expense=None,
    maximum_expense=None,
    minimum_benefit=None,
    maximum_benefit=None,
    batch_constraints=None,
    price_constraints=None,
) -> alt.Chart:
    if Batches is not None and demand_list is not None and price is not None:

        for i in range(len(Batches.batch_list)):
            Batches.batch_list[i].price += int(price)

        for i in range(len(Batches.batch_list)):
            if Batches.batch_list[i].price < 0:
                Batches.batch_list[i].price = 0

        data = []

        if method == "Primal":

            result = minBatchExpense(
                Batches,
                demand_list,
                category_of_variables,
                exchange_rate,
                tax_rate,
                customs_duty,
                transport_fee,
                minimum_expense,
                maximum_expense,
                batch_constraints,
            )

            x = [
                result["Batch quantities"][lot]
                for lot in result["Batch quantities"].keys()
            ]

            for i in range(len(Batches.batch_list)):
                data.append({"Name": Batches.batch_list[i].name, "Value": x[i]})

        elif method == "Dual":

            result = maxEarnings(
                Batches,
                demand_list,
                category_of_variables,
                exchange_rate,
                tax_rate,
                customs_duty,
                transport_fee,
                minimum_benefit,
                maximum_benefit,
                price_constraints,
            )

            x = [result["Item prices"][item] for item in result["Item prices"].keys()]

            for i in range(len(demand_list.items)):
                data.append({"Name": demand_list.items[i].name, "Value": x[i]})

        for i in range(len(Batches.batch_list)):
            Batches.batch_list[i].price = og_price[i]

        df = pd.DataFrame(data)

        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("Name:N", axis=alt.Axis(labelAngle=-45)),
                y="Value:Q",
                color=alt.value("lightblue"),
                tooltip=["Name", "Value"],
            )
            .properties(width="container", height=600)
        )

        st.altair_chart(chart, use_container_width=True)


@st.cache_data(experimental_allow_widgets=True, show_spinner=False)
def batches_quantity_price_variation(
    Batches: BatchCollection,
    demand_list: ItemListRequest,
    og_price,
    mini,
    maxi,
    Step,
    category_of_variables,
    exchange_rate,
    tax_rate,
    customs_duty,
    transport_fee,
    minimum_expense=None,
    maximum_expense=None,
    batch_constraints=None,
) -> alt.Chart:
    if Batches is not None and demand_list is not None and Step is not None:
        batches = copy.deepcopy(Batches)
        list_dict: dict[str, list]
        list_dict = {}

        for i in range(len(batches.batch_list)):
            list_dict[batches.batch_list[i].name] = []

        batch_selected = st.selectbox(
            "Which referent batch to choose ?", list_dict.keys()
        )

        step = Step
        if step > 100:
            st.write("The step is too high, step fixed to 100")
            step = 100

        for i in range(len(batches.batch_list)):
            if batches.batch_list[i].name == batch_selected:
                index_batch_selected = i

        list_dict["res_fun"] = []

        batches.batch_list[index_batch_selected].price = og_price[index_batch_selected]

        range_price = np.linspace(int(mini), int(maxi), int(step))

        with st.spinner("Please wait"):
            for price in range_price:
                if batches.batch_list[index_batch_selected].price + int(price) < 0:
                    batches.batch_list[index_batch_selected].price = 0
                else:
                    batches.batch_list[index_batch_selected].price += int(price)

                result = minBatchExpense(
                    batches,
                    demand_list,
                    category_of_variables,
                    exchange_rate,
                    tax_rate,
                    customs_duty,
                    transport_fee,
                    minimum_expense,
                    maximum_expense,
                    batch_constraints,
                )

                res = [
                    result["Batch quantities"][str(lot)]
                    for lot in result["Batch quantities"].keys()
                ]

                for i in range(len(res)):
                    list_dict[batches.batch_list[i].name].append(res[i])

                list_dict["res_fun"].append(result["Total cost"])

                batches.batch_list[index_batch_selected].price = og_price[
                    index_batch_selected
                ]

        data = pd.DataFrame(list_dict)
        data["range_price"] = range_price

        batch_data = data.drop(columns=["res_fun"])
        batch_data = batch_data.melt(
            "range_price", var_name="batch", value_name="quantity"
        )

        batch_chart = (
            alt.Chart(batch_data)
            .transform_calculate(
                Variation="datum.range_price",
                Quantity="datum.quantity",
                Batches="datum.batch",
            )
            .mark_line(size=3, point=True)
            .encode(
                x=alt.X("Variation:Q", title="Variation"),
                y=alt.Y("Quantity:Q", title="Quantity"),
                color=alt.Color("Batches:N", title="Batches"),
                tooltip=[
                    alt.Tooltip("Variation:Q"),
                    alt.Tooltip("Quantity:Q"),
                    alt.Tooltip("Batches:N"),
                ],
            )
            .properties(width="container", height=500)
        )
        st.altair_chart(batch_chart, use_container_width=True)

        res_fun_chart = (
            alt.Chart(data)
            .transform_calculate(Variation="datum.range_price", Total="datum.res_fun")
            .mark_line(size=3, point=True)
            .encode(
                x=alt.X("Variation:Q", title="Variation"),
                y=alt.Y("Total:Q", title="Total"),
                tooltip=[alt.Tooltip("Total:Q")],
            )
            .properties(width="container", height=500)
        )
        st.altair_chart(res_fun_chart, use_container_width=True)


@st.cache_data(experimental_allow_widgets=True, show_spinner=False)
def item_quantity_batch_price_variation(
    Batches: BatchCollection,
    demand_list: ItemListRequest,
    og_price,
    mini,
    maxi,
    Step,
    category_of_variables,
    exchange_rate,
    tax_rate,
    customs_duty,
    transport_fee,
    minimum_benefit=None,
    maximum_benefit=None,
    price_constraints=None,
) -> alt.Chart:
    if (
        Batches is not None
        and demand_list is not None
        and Step is not None
        and mini < maxi
    ):
        batches = copy.deepcopy(Batches)
        list_dict: dict[str, list]
        list_dict = {}
        list_batch: dict[str, list]
        list_batch = {}

        for i in range(len(demand_list.items)):
            list_dict[demand_list.items[i].name] = []

        for i in range(len(batches.batch_list)):
            list_batch[batches.batch_list[i].name] = []

        batch_selected = st.selectbox(
            "Which referent batch to choose ?", list_batch.keys()
        )

        step = Step
        if step > 100:
            st.write("The step is too high, step fixed to 100")
            step = 100

        for i in range(len(batches.batch_list)):
            if batches.batch_list[i].name == batch_selected:
                index_batch_selected = i

        list_dict["res_fun"] = []

        batches.batch_list[index_batch_selected].price = og_price[index_batch_selected]

        range_price = np.linspace(int(mini), int(maxi), int(step))

        with st.spinner("Please wait"):
            for price in range_price:
                if batches.batch_list[index_batch_selected].price + int(price) < 0:
                    batches.batch_list[index_batch_selected].price = 0
                else:
                    batches.batch_list[index_batch_selected].price += int(price)

                result = maxEarnings(
                    batches,
                    demand_list,
                    category_of_variables,
                    exchange_rate,
                    tax_rate,
                    customs_duty,
                    transport_fee,
                    minimum_benefit,
                    maximum_benefit,
                    price_constraints,
                )

                res = [
                    result["Item prices"][str(item)]
                    for item in result["Item prices"].keys()
                ]

                for i in range(len(res)):
                    list_dict[demand_list.items[i].name].append(res[i])

                list_dict["res_fun"].append(result["Total benefit"])

                for i in range(len(batches.batch_list)):
                    batches.batch_list[i].price = og_price[i]

        data = pd.DataFrame(list_dict)
        data["range_price"] = range_price

        item_data = data.drop(columns=["res_fun"])
        item_data = item_data.melt("range_price", var_name="item", value_name="price")

        item_chart = (
            alt.Chart(item_data)
            .transform_calculate(
                Variation="datum.range_price", Price="datum.price", Items="datum.item"
            )
            .mark_line(size=3, point=True)
            .encode(
                x=alt.X("Variation:Q", title="Variation"),
                y=alt.Y("Price:Q", title="Price"),
                color=alt.Color("Items:N", title="Items"),
                tooltip=[
                    alt.Tooltip("Variation:Q"),
                    alt.Tooltip("Price:Q"),
                    alt.Tooltip("Items:N"),
                ],
            )
            .properties(width="container", height=500)
        )

        st.altair_chart(item_chart, use_container_width=True)

        res_fun_chart = (
            alt.Chart(data)
            .transform_calculate(Variation="datum.range_price", Profit="datum.res_fun")
            .mark_line(size=3, point=True)
            .encode(
                x=alt.X("Variation:Q", title="Variation"),
                y=alt.Y("Profit:Q", title="Profit"),
                tooltip=[alt.Tooltip("Profit:Q")],
            )
            .properties(width="container", height=500)
        )
        st.altair_chart(res_fun_chart, use_container_width=True)


if (
    "Batches" in st.session_state
    and st.session_state["Batches"] is not None
    and "Demand" in st.session_state
    and st.session_state["Demand"] is not None
    and "database" in st.session_state
    and st.session_state["database"] is not None
    and "category_of_variables" in st.session_state
    and st.session_state["category_of_variables"] is not None
):
    st.markdown("#### Visualization of the Problem's Resolution")
    graph_optimization_batches(
        st.session_state["Batches_used"],
        st.session_state["Demand"],
        st.session_state["price"],
        og_price,
        method,
        st.session_state["category_of_variables"],
        st.session_state["exchange_rate"],
        st.session_state["tax_rate"],
        st.session_state["custom_duty"],
        st.session_state["transport_fee"],
        st.session_state["Minimum_Expense"],
        st.session_state["Maximum_Expense"],
        st.session_state["Minimum_Benefit"],
        st.session_state["Maximum_Benefit"],
        st.session_state["batch_constraints"],
        st.session_state["price_constraints"],
    )

    if method == "Primal":
        st.markdown(
            "#### Study of one batch price variation on the demand for all the batches"
        )
        st.write(
            "You need to modify the minimum, maximum and step values to see the variation of the quantity of the batch"
        )
        batches_quantity_price_variation(
            st.session_state["Batches_used"],
            st.session_state["Demand"],
            og_price,
            st.session_state["Mini"],
            st.session_state["Maxi"],
            st.session_state["step"],
            st.session_state["category_of_variables"],
            st.session_state["exchange_rate"],
            st.session_state["tax_rate"],
            st.session_state["custom_duty"],
            st.session_state["transport_fee"],
            st.session_state["Minimum_Expense"],
            st.session_state["Maximum_Expense"],
            st.session_state["batch_constraints"],
        )
    elif method == "Dual":
        st.markdown(
            "#### Study of the Effect of a Price Variation for One Batch on the Prices of Items"
        )
        st.write(
            "You need to modify the minimum, maximum and step values to see the variation of the price of the item"
        )
        item_quantity_batch_price_variation(
            st.session_state["Batches_used"],
            st.session_state["Demand"],
            og_price,
            st.session_state["Mini"],
            st.session_state["Maxi"],
            st.session_state["step"],
            st.session_state["category_of_variables"],
            st.session_state["exchange_rate"],
            st.session_state["tax_rate"],
            st.session_state["custom_duty"],
            st.session_state["transport_fee"],
            st.session_state["Minimum_Benefit"],
            st.session_state["Maximum_Benefit"],
            st.session_state["price_constraints"],
        )

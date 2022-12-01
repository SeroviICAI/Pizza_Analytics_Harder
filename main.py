import os
import re
import sys
from typing import List, Tuple

import pandas as pd
import plotly.express as px
from IPython.display import display

import excel
import report
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom.minidom import parseString

pd.set_option('display.max_rows', 15)
pd.set_option('display.max_columns', 5)
pd.set_option('display.width', 1000000)
pd.set_option('display.colheader_justify', 'center')
pd.set_option('display.precision', 3)


class DescribedDataFrame(pd.DataFrame):
    # normal properties
    _metadata = ["name", "description"]

    @property
    def _constructor(self):
        return DescribedDataFrame


def extract() -> Tuple[pd.Series, List[DescribedDataFrame]]:
    dataframe_container = []
    temp = pd.read_csv('data/data_dictionary.csv', encoding='latin')
    description = pd.Series(data=list(temp['Description']), index=temp['Field'])

    for csv_name in os.listdir("data/"):
        if not csv_name == "data_dictionary.csv" and csv_name.endswith('.csv'):
            if csv_name == "orders.csv" or csv_name == "order_details.csv":
                dataframe = DescribedDataFrame(pd.read_csv('data/' + csv_name, delimiter=';', encoding='cp1252'))
            else:
                dataframe = DescribedDataFrame(pd.read_csv('data/' + csv_name, delimiter=',', encoding='latin'))
            dataframe.name = csv_name.split('.csv')[0]
            dataframe_container.append(dataframe)
    return description, dataframe_container


def clean_dataframes(dataframe_container: List[DescribedDataFrame]) -> List[DescribedDataFrame]:
    orders, order_details, pizzas, pizza_types = dataframe_container

    # Sorting dataframes for filling nan's afterwards...
    orders.sort_values(by='order_id', ascending=True, ignore_index=True, inplace=True)
    order_details.sort_values(by=['order_id', 'order_details_id'], ascending=True, ignore_index=True, inplace=True)

    def change_quantities(quantity):
        return int(quantity) if (isinstance(quantity, str) and quantity.isdigit()) else float('nan')

    def reformat_pizzas(pizza):
        if isinstance(pizza, float):
            return pizza
        for char, initial in {'@': 'a', '0': 'o', '3': 'e'}.items():
            pizza = pizza.replace(char, initial)
        return re.sub(r"-|\s+", '_', pizza)

    # Reformatting the pizzas with their specified syntax and quantities
    order_details['quantity'] = order_details['quantity'].apply(change_quantities)
    order_details['pizza_id'] = order_details['pizza_id'].apply(reformat_pizzas)
    order_details = order_details.ffill(axis=0).bfill(axis=0)

    # Reformatting dates and times
    orders['date'] = pd.to_datetime(orders['date'], errors='coerce').dt.strftime('%d/%m/%Y')
    orders['time'] = pd.to_datetime(orders['time'], errors='coerce').dt.strftime('%H:%M:%S')
    orders = orders.ffill(axis=0).bfill(axis=0)
    return [orders, order_details, pizzas, pizza_types]


def concat_dataframes(description: pd.Series, dataframe_container: List[DescribedDataFrame]) -> DescribedDataFrame:
    orders, order_details, pizzas, pizza_types = dataframe_container

    # Formatting orders' dates and times
    orders.set_index('order_id', inplace=True)
    orders = pd.to_datetime(orders['date'] + orders['time'], format='%d/%m/%Y%H:%M:%S')

    # Pizzas
    pizzas = pizzas[['pizza_id', 'price']].set_index('pizza_id')
    pizzas_dict = pizzas['price'].to_dict()

    # Not a very neat line of code, but when grouping by order_id, quantities are not taken into account. One solution
    # is duplicating each row by how many times the pizzas has been ordered.
    order_details = order_details.reindex(order_details.index.repeat(order_details['quantity'])).reset_index(drop=True)
    order_details = pd.DataFrame(order_details.groupby(['order_id'])['pizza_id'].apply(list), columns=["order_details"])
    order_details.index.name = 'order_id'

    def get_price_order(order: List[str]) -> float:
        return sum([pizzas_dict[pizza_id] for pizza_id in order])

    order_details['price'] = order_details['order_details'].map(get_price_order)

    # Creating our work-dataframe
    frame = {'Timestamp': orders, 'Order_details': (pizzas := order_details['order_details']),
             'Amount_ordered': pizzas.str.len(),
             'Price': order_details['price']}
    result = DescribedDataFrame(frame)
    result.name = 'summed_dataframe'
    result.description = description
    return result


def weekly_pizzas(dataframe: DescribedDataFrame, types_only: bool = False) -> pd.DataFrame:
    dataframe = dataframe.copy()
    if types_only:
        dataframe['Order_details'] = dataframe['Order_details'].apply(lambda order_details: [pizza.rsplit('_', 1)[0]
                                                                                             for pizza in order_details]
                                                                      )
    weeks = pd.DataFrame(dataframe.groupby([dataframe['Timestamp'
                                                      ].dt.strftime('%W')])['Order_details'].apply(sum))
    weeks = weeks.rename(columns={"summed_dataframe": "Pizzas"})
    weeks.index.name = "week"
    weeks = weeks.explode('Pizzas').pivot_table(index="week", columns='Pizzas',
                                                aggfunc="size", fill_value=0)
    return weeks


def count_ingredients(dataframe: DescribedDataFrame, pizzas_dataframe: DescribedDataFrame) -> Tuple[pd.Series,
                                                                                                    pd.DataFrame]:
    pizzas_dataframe = pizzas_dataframe[['pizza_type_id', 'ingredients']].set_index('pizza_type_id')

    def check_missing_ingredients(ingredients: str):
        if 'Sauce' not in ingredients:
            ingredients += ', Tomato Sauce'
        if 'Mozzarella Cheese' not in ingredients:
            ingredients += ', Mozzarella Cheese'
        return ingredients

    pizzas_dataframe['ingredients'] = pizzas_dataframe['ingredients'].apply(check_missing_ingredients)
    pizzas_dataframe['ingredients'] = pizzas_dataframe['ingredients'].apply(lambda string: string.split(', '))
    pizzas_dict = pizzas_dataframe['ingredients'].to_dict()

    def get_ingredients(order_details: List[str]) -> List[str]:
        total_ingredients_list = []
        for ingredients_list in [pizzas_dict[pizza.rsplit('_', 1)[0]] for pizza in order_details]:
            total_ingredients_list += ingredients_list
        return total_ingredients_list

    dataframe['Ingredients'] = dataframe['Order_details'].apply(get_ingredients)

    # Get total count of each ingredient
    temp = pd.Series([item for sublist in dataframe['Ingredients'] for item in sublist])
    total_count = temp.groupby(temp).size()
    total_count.name = "Total_Count"
    total_count.index.name = "Ingredients"

    # Separate by weeks
    weeks_ingredients = pd.DataFrame(dataframe.groupby([dataframe['Timestamp'
                                                                  ].dt.strftime('%W')])['Ingredients'].apply(sum))
    weeks_ingredients = weeks_ingredients.rename(columns={"summed_dataframe": "Ingredients"})
    weeks_ingredients.index.name = "week"

    weeks_ingredients = weeks_ingredients.explode('Ingredients').pivot_table(index="week", columns='Ingredients',
                                                                             aggfunc="size", fill_value=0)
    return total_count, weeks_ingredients


def visualize_ingredients_consumed(series: pd.Series, dataframe_pizzas: pd.DataFrame,
                                   dataframe_ingredients: pd.DataFrame) -> None:
    # Amount of total ingredients consumed by each type
    series.sort_values(ascending=False, inplace=True)
    fig = px.bar(series, labels={'Ingredients': 'Ingredient', 'value': 'Amount consumed'},
                 title='Amount of total ingredients consumed over a year by each Type',
                 color="value", template='ggplot2')
    fig.update_layout(showlegend=False)
    fig.update_xaxes(tickangle=60)
    fig.show()

    # Amount and type of pizzas ordered each week
    # Some quick adjustments first...
    dataframe_pizzas.reset_index(inplace=True)
    dataframe_pizzas['week'] = dataframe_pizzas['week'].apply(int)

    dataframe_pizzas = dataframe_pizzas.melt(id_vars='week', value_vars=dataframe_pizzas.columns[1:])
    fig = px.bar(dataframe_pizzas, x='value', y='Pizzas', labels={'value': 'Amount consumed'},
                 title='Amount of total ingredients consumed per week by each Type',
                 color="value", template='ggplot2', animation_frame='week', height=950)
    fig.update_layout(showlegend=False, xaxis_range=[0, 80], yaxis={'categoryorder': 'total ascending'})
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 2000
    fig.update_xaxes(tickangle=60)
    fig.show()

    # Amount and type of ingredients consumed each week
    # Some quick adjustments first...
    dataframe_ingredients.reset_index(inplace=True)
    dataframe_ingredients['week'] = dataframe_ingredients['week'].apply(int)

    dataframe_ingredients = dataframe_ingredients.melt(id_vars='week', value_vars=dataframe_ingredients.columns[1:])
    fig = px.bar(dataframe_ingredients, x='value', y='Ingredients', labels={'value': 'Amount consumed'},
                 title='Amount of total ingredients consumed per week by each Type',
                 color="value", template='ggplot2', animation_frame='week', height=950)
    fig.update_layout(showlegend=False, xaxis_range=[0, 1200], yaxis={'categoryorder': 'total ascending'})
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 2000
    fig.update_xaxes(tickangle=60)
    fig.show()
    return


def predict_next_week(dataframe: pd.DataFrame) -> None:
    display(predictions := dataframe[dataframe.columns].median().to_frame(name="Amount"))
    # XML of ingredient amounts predictions
    root = Element('root')
    comment = Comment("Vague prediction of next week ingredients amount.")
    root.append(comment)

    dataframe = SubElement(root, 'file', name='name')
    dataframe.text = "prediction_ingredients"
    for ingredient in predictions.index:
        column = SubElement(dataframe, 'ingredient', {'ingredient_name': 'Nduja Salami' if (ingredient ==
                                                                                            'Nduja Salami')
                                                      else ingredient})
        SubElement(column, 'amount', name='amount').text = str(predictions.loc[ingredient, 'Amount'])

    xml_string = parseString(tostring(root)).toprettyxml(indent="   ")
    with open("predictions.xml", "w") as file:
        file.write(xml_string)
    return predictions.to_csv('predictions.csv', sep=',')


def main():
    description, dataframe_container = extract()

    # Brief description of each dataframe
    root = Element('root')
    comment = Comment("Brief analysis of nan's, nulls, data types and data counts of each dataframe")
    root.append(comment)
    for dataframe_pd in dataframe_container:
        # dataframe_pd.info()
        dataframe = SubElement(root, 'file', name='name')
        dataframe.text = dataframe_pd.name
        SubElement(dataframe, 'length', name='count').text = str(len(dataframe_pd.index))
        for column in dataframe_pd.columns:
            dataframe_column = dataframe_pd[column]
            column = SubElement(dataframe, 'column', {'column_name': column})
            SubElement(column, 'nan', name='nan_count').text = str((dataframe_column.isna()).sum())
            SubElement(column, 'null', name='null_count').text = str((dataframe_column.isnull()).sum())
            SubElement(column, 'data_type', name='data_type').text = str(dataframe_column.dtype)
            SubElement(column, 'unique', name='count').text = str(dataframe_column.nunique())

    xml_string = parseString(tostring(root)).toprettyxml(indent="   ")
    with open("analysis_dataframes.xml", "w") as file:
        file.write(xml_string)

    # Clean dataframes
    dataframe_container = clean_dataframes(dataframe_container)
    print("Cleaned dataframes:")
    display(dataframe_container[0])
    display(dataframe_container[1])

    # Creating main dataframe to work with.
    dataframe_pd = concat_dataframes(description, dataframe_container)
    dataframe_pd.to_csv("processed_data/clean_dataframe.csv", sep=',')
    print("\nSummed dataframe")
    display(dataframe_pd)
    # display(dataframe.describe())

    # Now let's create some useful dataframes to solve our problem.
    # Amount and type of pizzas ordered each week
    weeks = weekly_pizzas(dataframe_pd, types_only=True)
    weeks.to_csv("processed_data/pizzas_weeks(with types_only).csv", sep=',')
    # Creating csv weekly pizzas with sizes as well for utility in the report
    weekly_pizzas(dataframe_pd, types_only=False).to_csv("processed_data/pizzas_weeks(with sizes).csv", sep=',')
    print("\nPizzas per week:")
    display(weeks)

    # Amount of total ingredients consumed by each type
    pizza_types = dataframe_container[-1]
    total_count, weeks_ingredients = count_ingredients(dataframe_pd, pizza_types)
    print("\nTotal amount of ingredients:")
    display(total_count)

    # Amount and type of ingredients consumed each week
    weeks_ingredients.to_csv("processed_data/ingredients_weeks.csv", sep=',')
    print("\nIngredients per week:")
    display(weeks_ingredients)

    # You can visualize some graphs via this function, however the report will be done on pdf, so animations
    # and other interactive resources cannot be implemented.
    # visualize_ingredients_consumed(total_count, weeks, weeks_ingredients)
    print("\nConclusion:")
    predict_next_week(weeks_ingredients)
    report.create_report()
    excel.create_excel()


if __name__ == '__main__':
    sys.exit(main())

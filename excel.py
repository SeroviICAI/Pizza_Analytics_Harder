import os
import pandas as pd


def create_excel():
    clean_dataframe, ingredients_weeks, pizzas_weeks_sizes, pizzas_weeks = [pd.read_csv("processed_data/" + csv_name,
                                                                                        encoding='latin')
                                                                            for csv_name in os.listdir("processed_data/"
                                                                                                       )]
    clean_dataframe.set_index('order_id', inplace=True)
    ingredients_weeks.set_index('week', inplace=True)
    pizzas_weeks_sizes.set_index('week', inplace=True)
    pizzas_weeks.set_index('week', inplace=True)

    writer = pd.ExcelWriter("report_maven_excel.xlsx",  engine="xlsxwriter", datetime_format='mmm d yyyy hh:mm:ss')

    # Sheet 1
    clean_dataframe['Timestamp'] = pd.to_datetime(clean_dataframe['Timestamp'], format='%Y-%m-%d %H:%M:%S')
    clean_dataframe.to_excel(writer, sheet_name="Orders, Timestamp and Details")
    worksheet = writer.sheets["Orders, Timestamp and Details"]
    worksheet.set_column(1, 1, 20)
    worksheet.set_column(2, 2, 20)
    worksheet.set_column(3, 3, 20)

    # Sheet 2
    months = clean_dataframe[['Timestamp', 'Amount_ordered', 'Price']]
    months = months.groupby(months['Timestamp'].dt.month)[['Amount_ordered', 'Price']].sum()
    months.to_excel(writer, sheet_name="Orders, Month and Details")
    worksheet = writer.sheets["Orders, Month and Details"]
    chart = writer.book.add_chart({'type': 'line'})
    chart.add_series({'values': f'=\'Orders, Month and Details\'!$C$2:$C$'
                                f'{(columns := months.shape[0] + 1)}',
                      'categories': f'=\'Orders, Month and Details\'!$A$2:$A${columns}',
                      'name': "Monthly income (Maven pizzas)",
                      'name_font': {'size': 14, 'bold': True}})
    chart.set_style(36)
    worksheet.insert_chart('G2', chart, {'x_scale': 3, 'y_scale': 2})

    # Sheet 3
    pizzas_sizes_sum = pizzas_weeks_sizes.sum(axis=0).to_frame(name="Amount")
    pizzas_sizes_sum['Size'] = pizzas_sizes_sum.index
    pizzas_sizes_sum.reset_index(inplace=True)
    pizzas_sizes_sum['Pizza'] = pizzas_sizes_sum['Size'].apply(lambda pizza: pizza.rsplit('_', 1)[0])
    pizzas_sizes_sum['Size'] = pizzas_sizes_sum['Size'].apply(lambda pizza: pizza.rsplit('_', 1)[1].upper())
    pizzas_sizes_sum.sort_values('Pizza', ascending=True, inplace=True)
    # Create sheet
    pizzas_sizes_sum.to_excel(writer, sheet_name="Amount of Pizzas with Sizes")
    worksheet = writer.sheets["Amount of Pizzas with Sizes"]
    chart = writer.book.add_chart({'type': 'column'})
    chart.add_series({'values': f'=\'Amount of Pizzas with Sizes\'!$C$2:$C$'
                                f'{(columns := pizzas_sizes_sum.shape[0] + 1)}',
                      'categories': f'=\'Amount of Pizzas with Sizes\'!$B$2:$B${columns}',
                      'name': "Amount of Pizzas with Sizes ordered",
                      'name_font': {'size': 14, 'bold': True}})
    chart.set_style(37)
    worksheet.insert_chart('G2', chart, {'x_scale': 3, 'y_scale': 2})

    # Sheet 4
    pizzas_weeks.T.to_excel(writer, sheet_name="Amount of Pizzas per Week")

    # Sheet 5
    ingredients_weeks.T.to_excel(writer, sheet_name="Amount of Ingredients per Week")
    writer.close()

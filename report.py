import dataframe_image as dfi
import matplotlib.pyplot as plt
import numpy as np

import time
import os
import pandas as pd

import warnings
import requests
import seaborn as sns
from fpdf import FPDF

TITLE = "Maven Pizza Data Report"
WIDTH = 210
HEIGHT = 297

warnings.simplefilter("ignore", UserWarning)
img_data = requests.get('https://apps.icai.comillas.edu/iconos/logo-icai.png').content
with open('images/logo-icai.png', 'wb') as handler:
    handler.write(img_data)


class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(w=0, h=10, txt='Page ' + str(self.page_no()), border=0, align='C')


def create_report():
    # Create PDF
    pdf = PDF()  # A4 (210 by 297 mm)

    # Page 1
    pdf.add_page()
    create_letterhead(pdf)
    create_title(TITLE, pdf)
    write_to_pdf(pdf, "1. The table below illustrates the Amount of pizzas ordered and their Prices per Week in Maven"
                      " Pizza:")
    pdf.ln(15)
    create_visualizations()
    pdf.image("images/table_orders.png", h=HEIGHT / 1.8, w=WIDTH / 3.3, x=(WIDTH / 2 - 30))
    pdf.ln(10)

    # Page 2
    pdf.add_page()
    create_letterhead(pdf)
    create_title(TITLE, pdf)
    write_to_pdf(pdf, "2. The visualisations below show the Total Amount of pizzas ordered Annually and by Type:")
    pdf.ln(15)

    pdf.image("images/barplot_pizzas.png", w=WIDTH / 2 - 10, x=5, y=80)
    pdf.image("images/pie_categories.png", w=WIDTH / 2 - 10, x=WIDTH / 2, y=80)
    pdf.ln(100)
    write_to_pdf(pdf, "3. The pie below shows the Amount of pizzas ordered Annually by their Sizes:")
    pdf.ln(15)
    pdf.image("images/pie_sizes.png", h=HEIGHT / 4, x=(WIDTH / 2 - 63))
    pdf.ln(10)

    # Page 3
    pdf.add_page()
    create_letterhead(pdf)
    create_title(TITLE, pdf)
    write_to_pdf(pdf, "4. The barplot below show the Total Amount of pizzas ordered Annually with their Sizes:")
    pdf.ln(15)
    pdf.image("images/barplot_pizzas_sizes.png", w=WIDTH / 1.2)
    pdf.ln(10)

    # Page 4
    pdf.add_page()
    create_letterhead(pdf)
    create_title(TITLE, pdf)
    write_to_pdf(pdf, "5. The barplot below show the Total Amount of Ingredients consumed Annually:")
    pdf.ln(15)
    pdf.image("images/barplot_ingredients.png", w=WIDTH / 1.2)
    pdf.ln(10)

    # Page 5
    pdf.add_page()
    create_letterhead(pdf)
    create_title(TITLE, pdf)
    write_to_pdf(pdf, "6. With the given values we can vaguely predict the following amounts for any week:")
    pdf.ln(15)
    pdf.image("images/predictions_1.png", h=HEIGHT / 1.7, x=20, y=80)
    pdf.image("images/predictions_2.png", h=HEIGHT / 1.7, x=WIDTH / 2 + 20, y=80)
    pdf.ln(10)

    # Generate the PDF
    pdf.output("report_maven.pdf")


def create_letterhead(pdf):
    pdf.image("images/logo-icai.png", 5, 5, 75, 28.35)


def create_title(title, pdf):
    # Add main title
    pdf.set_font('Helvetica', 'b', 20)
    pdf.ln(40)
    pdf.write(5, title)
    pdf.ln(10)

    # Add date of report
    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(r=128, g=128, b=128)
    today = time.strftime("%d/%m/%Y")
    pdf.write(4, f'{today}')

    # Add line break
    pdf.ln(10)


def write_to_pdf(pdf, words):
    # Set text colour, font size, and font type
    pdf.set_text_color(r=0, g=0, b=0)
    pdf.set_font('Helvetica', '', 12)
    pdf.write(5, words)


def create_visualizations():
    clean_dataframe = pd.read_csv("processed_data/clean_dataframe.csv", encoding='latin')
    ingredients_weeks = pd.read_csv("processed_data/ingredients_weeks.csv", encoding='latin')
    pizzas_weeks_sizes = pd.read_csv("processed_data/pizzas_weeks(with sizes).csv", encoding='latin')
    pizzas_weeks = pd.read_csv("processed_data/pizzas_weeks(with types_only).csv", encoding='latin')
    
    pizza_types = pd.read_csv("data/pizza_types.csv", encoding='latin')
    ingredients_weeks.set_index('week', inplace=True)
    pizzas_weeks_sizes.set_index('week', inplace=True)
    pizzas_weeks.set_index('week', inplace=True)

    # Creating table from clean_dataframe
    clean_dataframe['Timestamp'] = pd.to_datetime(clean_dataframe['Timestamp'], format='%Y-%m-%d %H:%M:%S')
    weekly_orders = pd.DataFrame(clean_dataframe.groupby([clean_dataframe['Timestamp'].
                                                         dt.strftime('%W')])[['Amount_ordered', 'Price']].apply(sum))
    weekly_orders.index.name = "Week"
    weekly_orders.reset_index(inplace=True)
    weekly_orders['Week'] = weekly_orders['Week'].apply(int)
    weekly_orders['Amount_ordered'] = weekly_orders['Amount_ordered'].apply(int)
    amount_mean = weekly_orders['Amount_ordered'].mean()

    def higher_than_mean(value):
        return 'color: %s' % ("red" if value < amount_mean else "green" if value > amount_mean else "black")

    styled_df = weekly_orders.style.format({'Price': "{:.2f}",
                                            }).hide(axis='index') \
        .set_properties(**{'border': '1.3px black'}) \
        .bar(subset=["Price", ], color='lightgreen') \
        .applymap(higher_than_mean, subset=['Amount_ordered'])
    dfi.export(styled_df, 'images/table_orders.png')

    # Setting seaborn style
    sns.set_style('darkgrid')

    # Generating barplot of pizzas
    pizzas_sum = pizzas_weeks.sum(axis=0).to_frame(name="Amount")
    pizzas_sum['Pizza'] = pizzas_sum.index
    pizzas_sum.reset_index(inplace=True)
    pizzas_sum.sort_values('Amount', ascending=False, inplace=True)

    fig = plt.figure(1, figsize=(20, 20))
    sns.barplot(data=pizzas_sum, x='Amount', y='Pizza', palette=sns.cubehelix_palette(len(pizzas_sum)))
    plt.title('Pizzas ordered in a year in Maven Pizza', fontweight="bold", fontsize=20)
    plt.xlabel('Pizzas', fontsize=15)
    plt.ylabel('Amount ordered', fontsize=15)
    # Save the plot as a PNG
    plt.savefig('images/barplot_pizzas.png', bbox_inches='tight', pad_inches=0)
    # fig.show()

    # Generating barplot of pizzas with sizes
    pizzas_sizes_sum = pizzas_weeks_sizes.sum(axis=0).to_frame(name="Amount")
    pizzas_sizes_sum['Size'] = pizzas_sizes_sum.index
    pizzas_sizes_sum.reset_index(inplace=True)
    pizzas_sizes_sum.sort_values('Amount', ascending=False, inplace=True)
    pizzas_sizes_sum['Pizza'] = pizzas_sizes_sum['Size'].apply(lambda pizza: pizza.rsplit('_', 1)[0])
    pizzas_sizes_sum['Size'] = pizzas_sizes_sum['Size'].apply(lambda pizza: pizza.rsplit('_', 1)[1].upper())

    fig = plt.figure(2, figsize=(20, 20))
    sns.barplot(data=pizzas_sizes_sum, x='Amount', y='Pizza', hue='Size', palette=sns.cubehelix_palette(5))
    plt.title('Pizzas ordered in a year in Maven Pizza (separated by size)', fontweight="bold", fontsize=20)
    plt.xlabel('Pizzas', fontsize=15)
    plt.ylabel('Amount ordered', fontsize=15)
    # Save the plot as a PNG
    plt.savefig('images/barplot_pizzas_sizes.png', bbox_inches='tight', pad_inches=0)
    # fig.show()

    # Generate barplot of ingredients
    ingredients_sum = ingredients_weeks.sum(axis=0)
    ingredients_sum.index.name = 'Ingredients'
    ingredients_sum.sort_values(ascending=False, inplace=True)

    fig = plt.figure(3, figsize=(20, 20))
    sns.barplot(x=ingredients_sum.values, y=ingredients_sum.index, palette=sns.cubehelix_palette(len(ingredients_sum)))
    plt.title('Ingredients consumed in a year in Maven Pizza', fontweight="bold", fontsize=20)
    plt.xlabel('Ingredient', fontsize=15)
    plt.ylabel('Amount consumed', fontsize=15)
    # Save the plot as a PNG
    plt.savefig('images/barplot_ingredients.png', bbox_inches='tight', pad_inches=0)
    # fig.show()

    # Generate pie of pizza categories
    pizza_categories = pizzas_weeks.sum(axis=0).to_frame(name="Amount")
    pizza_categories['Pizza'] = pizza_categories.index
    pizza_categories.reset_index(inplace=True)

    def categorize(pizza):
        return pizza_types[pizza_types['pizza_type_id'] == pizza]['category'].values[0]

    pizza_categories['Category'] = pizza_categories['Pizza'].apply(categorize)
    pizza_categories = pizza_categories.groupby("Category")['Amount'].sum()
    fig = plt.figure(4, figsize=(10, 10))
    explode = (0, 0.05, 0, 0)
    plt.pie(pizza_categories.values, explode=explode, labels=pizza_categories.index, autopct='%1.1f%%', startangle=90,
            colors=sns.cubehelix_palette(len(pizza_categories) + 1), wedgeprops={'linewidth': 3.0},
            textprops={'size': 'x-large'})
    plt.title('Amount of pizzas ordered in a year by Category', fontweight="bold", fontsize=20)
    plt.savefig('images/pie_categories.png', bbox_inches='tight', pad_inches=0)
    # fig.show()

    pizza_sizes = pizzas_sizes_sum.groupby("Size")['Amount'].sum()
    fig, ax = plt.subplots(figsize=(10, 5), subplot_kw=dict(aspect="equal"))

    wedges, texts = ax.pie(pizza_sizes.values, wedgeprops=dict(width=0.5), startangle=-40,
                           colors=sns.cubehelix_palette(len(pizza_categories) + 1))

    kw = dict(arrowprops=dict(arrowstyle="-", color='black', linewidth=2), zorder=0, va="center")
    for p, label in zip(wedges, list(map(lambda size: size + f' ({pizza_sizes[size]} pizzas)', pizza_sizes.index))):
        ang = (p.theta2 - p.theta1) / 2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = "angle,angleA=0,angleB={}".format(ang)
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        ax.annotate(label, xy=(x, y), xytext=(1.35 * np.sign(x), 1.4 * y),
                    horizontalalignment=horizontalalignment, fontsize=15, **kw)
    plt.title('Amount of pizzas ordered in a year by Size', fontweight="bold", fontsize=20)
    plt.savefig('images/pie_sizes.png', bbox_inches='tight', pad_inches=0)
    # fig.show()

    prediction_df = ingredients_weeks[ingredients_weeks.columns].median().to_frame(name="Amount")
    dfi.export(prediction_df[:len(prediction_df) // 2], 'images/predictions_1.png')
    dfi.export(prediction_df[len(prediction_df) // 2:], 'images/predictions_2.png')

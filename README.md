# Pizza Analytics Harder: A data analytics project.

## What's the objective?
The objective of this mini project is to predict how many ingredients and of what kind would be needed in the
near future, whilst having to work with some super desorganized .csv files.

## What data structure do we want?
Probably some sort of dataframe is the best way to go. They are easy to manipulate and to work with. Panels
(3 dimensional) could have been a good idea, but they were deprecated long ago, and maybe it exceeds the level
of complexity required for such problem.

## Where can we start?
First and foremost, the dataframes are really desorganised, so a good first step would be filling the missing
values (ffill and bfill maybe) and obatining dataframes coherent with the data dictionary and pizza types csv.

Furthermore, there are too many data files to work with that working with them can get quite messy, plus
some contain non-interesting data (such as order_details_id, which serves just like an index). It would be a
great idea to sum up those files in one compact dataframe. Just by a glimpse of it, the order details occupy
far too many rows for just one order. Perhaps, making lists or dictionaries with all the details of an order,
and write them on one single line, is more readable, and easier to work with.

Note that there is a data_dictionary file which specifies what does each column represent. Maybe we could add
those descriptions as metadata of a customized dataframe object.

This dataset will contain the order id as index, the timestamp (date and time joined, there is no real need to
have them separated), the order details (list of pizzas ordered. If a pizza is ordered "n" times in a single
order, there would be "n" ocurrences of that specific pizza) and the price of that order (as sum of prices of
all the ordered pizzas).

## What more can be useful for our analysis?
Having more than one dataframe to work with is no issue. In fact, it helps structuring your data into separate
variables. As we are working with ingredient amounts, it is important how many ingredients were consumed across
the year and their kind (Tomato sauce, Mozzarella cheese, ...). Additionaly, we can create another dataframe
containing the amount of ingredients and kind consumed each week. Notice that the nature of both structures is
different. The total amount of ingredients consumed by each kind can be stored in "long" form. A pandas Series
should be enough, with the ingredients as indexes and the amount consumed as values. Instead, for the second
dataframe having the amounts of ingredients per week in long form would be a bit messy. The data would better
be stored in "wide" form where our indexes would be the week number. (In the execution of this step another
column had to be added, a "week" column, which is an exact copy of the index but it helped easing the work
when coding the visualizations.) Having the ingredients as "wide" data makes the user check the ingredients
consumed on the n'th week by just having a look at the n'th row.

Some visualization would also help understanding the nature of our data. Plotly is an excellent library for
plotting data in Python, giving the programmer tools to create express animations and plots easily. Some of
the data which would be better visualized on a graph, rather than a table, would be these last two dataframes.
For the total amount of ingredients consumed across the year, a barplot would be enough to rapidly tell which
ingredients are more relevant/used in the business. When analysing this per week, maybe an animation that shows
how the amounts of ingredients used change each week is the way to go, in order to tell the uses and tendencies
these ingredients follow.

## Predict near future:
The median of the amount of ingredients is accurate enough, as the data have a high variance, and the median is less altered by outlayers than the mean. Implementing a more complex model, such as a Sequence, or Linear Regression, is not really needed for so small amounts of data (53 weeks).

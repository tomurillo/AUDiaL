def Content():
    # Name : [file, title, alt text, url, ontology, diagram type, session id prefix]
    CONTENT = {"Austrian Population": ["austria_pop_barchart.svg",
                              "Population of Austria by region and sex",
                              "This bar chart shows the population of Austria, divided by region. Each region has three bars showing the total population "
                              "for the years 1994, 2004 and 2014 respectively. Each bar is further divided into male and female values.",
                              "bar-chart-austria", "austria_pop_barchart.rdf", "Bar Chart", "ap"],
               "Leonardo DiCaprio": ["caprio_plain.png",
                              "Leonardo DiCaprio's girlfriends throughout the years",
                              "This bar chart shows Leonardo DiCaprio's age compared to the ages of his different girlfriends as time passes. "
                              "The vertical axis shows the age value in years, the horizontal axis shows time in years.",
                              "bar-chart-leo-dicaprio", "caprio.rdf", "Bar Chart", "dc"],
               "Power in Europe": ["energy_plain.jpg",
                                     "Power Generation by Source in selected European countries 2001-2018",
                                     "This chart shows how different European countries have changed their energy production from 2001 to 2018. Each year is divided into sources (renewable, nuclear, coal, and other fossil fuels) " 
                                     "according to which percentage of the country's energy generation that year came from that source.",
                                    "bar-chart-power", "energy.rdf", "Bar Chart", "pw"]
               }
    return CONTENT

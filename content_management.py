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
                              "bar-chart-leo-dicaprio", "caprio.rdf", "Bar Chart", "dc"]}
    return CONTENT

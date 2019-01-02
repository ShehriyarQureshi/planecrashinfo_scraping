import re
import requests
from bs4 import BeautifulSoup
import datetime
import csv
import progressbar
from time import sleep


def request_to_server(url):
    response = None
    try:
        response = requests.get(url, timeout=10)
        return response
    except:
        print("sleep for 10 seconds")
        sleep(10)
        response = request_to_server(url)
        return response


base_uri = "http://www.planecrashinfo.com"
year_data = {}
csv_writer = csv.writer(open(
    "planecrashinfo_"+datetime.datetime.now().strftime("%Y%m%d%H%M%S")+".csv", 'w'))

# write data header to csv file
csv_writer.writerow(["date", "time", "location", "operator", "flight_no", "route", "ac_type", "registration", "cn_ln", "all_aboard",
                     "passengers_aboard", "crew_aboard", "all_fatalities", "passenger_fatalities", "crew_fatalities", "ground", "summary"])

# request to list of years
response = request_to_server("http://www.planecrashinfo.com/database.htm")


if(response.status_code == 200):
    parser = BeautifulSoup(response.content, 'html.parser')
    a_tags = parser.find_all("a")
    # build a dict contain the year as key and page url as value
    year_data = {a.text.strip(): {"url": base_uri + a["href"] if a["href"][0] ==
                                  "/" else base_uri + "/" + a["href"]} for a in a_tags if a.text.strip().isdigit()}

    # loop for each year
    for year, data in year_data.items():

        # request to list of year's crashes
        response_year = request_to_server(data["url"])
        parser_year = BeautifulSoup(response_year.content, 'html.parser')

        # get all <a> tag except  "Return to Home" link
        a_tags = parser_year.find_all("a")
        a_tags = [a for a in a_tags if "Return to Home" not in a.text]

        # progress bar initial
        i = 0
        bar = progressbar.ProgressBar(maxval=len(a_tags),
                                      widgets=[year + ": ", progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
        bar.start()

        for a in a_tags:
            # print("-", sep=' ', end='', flush=True)

            # request to crash detail page
            response_crash = request_to_server(
                base_uri + "/" + year + a["href"] if a["href"][0] == "/" else base_uri + "/" + year + "/" + a["href"])
            parser_crash = BeautifulSoup(response_crash.content, 'html.parser')

            # get all table content except the first row(table title)
            tr_tags = parser_crash.find_all("tr")
            tr_tags = tr_tags[1:]

            # write data to csv file
            data = [tr.find_all("td")[1].text.strip() for tr in tr_tags]

            # get all aboard
            aboard = data[9]
            pattern = re.compile(r'^\d+|^\W')
            matches = pattern.finditer(aboard)

            for match in matches:
                all_aboard_span = match.span()

            all_aboard = aboard[all_aboard_span[0]:all_aboard_span[1]]

            # get all passengers aboard
            pattern = re.compile(r'(?<=\(passengers:)\d+|(?<=\(passengers:)\W')
            matches = pattern.finditer(aboard)

            for match in matches:
                passengers_aboard_span = match.span()

            passengers_aboard = aboard[passengers_aboard_span[0]:passengers_aboard_span[1]]

            # get all crew aboard
            pattern = re.compile(r'(?<=crew:)\d+|(?<=crew:)\W')
            matches = pattern.finditer(aboard)

            for match in matches:
                crew_aboard_span = match.span()

            crew_aboard = aboard[crew_aboard_span[0]:crew_aboard_span[1]]

            # get all fatalities

            fatalities = data[10]
            pattern = re.compile(r'^\d+|^\W')
            matches = pattern.finditer(fatalities)

            for match in matches:
                all_fatalities_span = match.span()

            all_fatalities = fatalities[all_fatalities_span[0]:all_fatalities_span[1]]

            # get all passengers fatalities
            pattern = re.compile(r'(?<=\(passengers:)\d+|(?<=\(passengers:)\W')
            matches = pattern.finditer(fatalities)

            for match in matches:
                passengers_fatalities_span = match.span()

            passengers_fatalities = fatalities[passengers_fatalities_span[0]:passengers_fatalities_span[1]]

            # get all crew fatalities
            pattern = re.compile(r'(?<=crew:)\d+|(?<=crew:)\W')
            matches = pattern.finditer(fatalities)

            for match in matches:
                crew_fatalities_span = match.span()

            crew_fatalities = fatalities[crew_fatalities_span[0]:crew_fatalities_span[1]]

            # remove aboard info and store each value separately
            data.pop(9)
            data.insert(9, all_aboard)
            data.insert(10, passengers_aboard)
            data.insert(11, crew_aboard)

            # remove fatalities info and store each value separately
            data.pop(12)
            data.insert(12, all_fatalities)
            data.insert(13, passengers_fatalities)
            data.insert(14, crew_fatalities)

            csv_writer.writerow(data)

            # update the bar
            bar.update(i+1)
            i = i+1

            # sleep to overcome Server connection refused error
            sleep(0.1)

        bar.finish()
else:
    print("Cannot fetch data")

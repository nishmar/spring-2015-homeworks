#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import logging
import requests
import csv
from BeautifulSoup import BeautifulSoup


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
loghandler = logging.StreamHandler(sys.stderr)
loghandler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
log.addHandler(loghandler)

base_url = "http://www.tripadvisor.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"


parser = argparse.ArgumentParser(description='Scrape tripadvisor')
parser.add_argument('-datadir', type=str,
                    help='Directory to store raw html files',
                    default="data/")
parser.add_argument('-state', type=str,
                    help='State for which the hotel data is required.',
                    required=True)
parser.add_argument('-city', type=str,
                    help='City for which the hotel data is required.',
                    required=True)
args = parser.parse_args()


def get_city_page(city, state):
    """ Returns the URL of the list of the hotels in a city. Corresponds to
    STEP 1 & 2 of the slides.

    Parameters
    ----------
    city : str

    state : str


    Returns
    -------
    url : str
        The relative link to the website with the hotels list.

    """
    # Build the request URL
    url = base_url + "city=" + city + "&state=" + state
    # Request the HTML page
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    with open(os.path.join(args.datadir, city + '-tourism-page.html'), "w") as h:
        h.write(html)

    # Use BeautifulSoup to extract the url for the list of hotels in
    # the city and state we are interested in.

    # For example in this case we need to get the following href
    # <li class="hotels twoLines">
    # <a href="/Hotels-g60745-Boston_Massachusetts-Hotels.html" data-trk="hotels_nav">...</a>
    soup = BeautifulSoup(html)
    li = soup.find("li", {"class": "hotels twoLines"})
    city_url = li.find('a', href=True)
    return city_url['href']


def get_hotellist_page(city_url, page_count):
    """ Returns the hotel list HTML. The URL of the list is the result of
    get_city_page(). Also, saves a copy of the HTML to the disk. Corresponds to
    STEP 3 of the slides.

    Parameters
    ----------
    city_url : str
        The relative URL of the hotels in the city we are interested in.
    page_count : int
        The page that we want to fetch. Used for keeping track of our progress.

    Returns
    -------
    html : str
        The HTML of the page with the list of the hotels.
    """
    url = base_url + city_url
    # Sleep 2 sec before starting a new http request
    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    # Save the webpage
    with open(os.path.join(args.datadir, args.city + '-hotelist-' + str(page_count) + '.html'), "w") as h:
        h.write(html)
    return html


def parse_hotellist_page(html, writer):
    """Parses the website with the hotel list and prints the hotel name, the
    number of stars and the number of reviews it has. If there is a next page
    in the hotel list, it returns a list to that page. Otherwise, it exits the
    script. Corresponds to STEP 4 of the slides.

    Parameters
    ----------
    html : str
        The HTML of the website with the hotel list.

    Returns
    -------
    URL : str
        If there is a next page, return a relative link to this page.
        Otherwise, exit the script.
    """    
    soup = BeautifulSoup(html)
    # Extract hotel name, star rating and number of reviews
    hotel_boxes = soup.findAll('div', {'class' :'listing wrap reasoning_v5_wrap jfy_listing p13n_imperfect'})
    if not hotel_boxes:
        log.info("#################################### Option 2 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing_info jfy'})
    if not hotel_boxes:
        log.info("#################################### Option 3 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing easyClear  p13n_imperfect'})

	hotel_count = 0
	
    for hotel_box in hotel_boxes:
		hotel_name = hotel_box.find("a", {"target" : "_blank"}).find(text=True)
		hotel_url = hotel_box.find("a", {"target" : "_blank"})['href']
    	
		general_info_list = []
    	
		log.info("Hotel name: %s" % hotel_name.strip())
		general_info_list.append(hotel_name.strip())
		
    	#log.info("Hotel url: %s" % hotel_url)
    	
		log.info(hotel_count)
    	
		hotel_info_list = get_hotel_info(hotel_url, hotel_count)

		global hotel_count
		hotel_count = hotel_count + 1 
    	
		stars = hotel_box.find("img", {"class" : "sprite-ratings"})
		if stars:
			log.info("Stars: %s" % stars['alt'].split()[0])
			general_info_list.append(stars['alt'].split()[0])
		else:
			general_info_list.append('')

		num_reviews = hotel_box.find("span", {'class': "more"}).findAll(text=True)
		if num_reviews:
			log.info("Number of reviews: %s " % [x for x in num_reviews if "review" in x][0].strip())
			general_info_list.append([x for x in num_reviews if "review" in x][0].strip())
		else:
			general_info_list.append('')        	

		#WRITE ROW TO CSV
		writer.writerow(general_info_list + hotel_info_list)
	
    # Get next URL page if exists, otherwise exit
    div = soup.find("div", {"class" : "pagination paginationfillbtm"}) #Modified
    # check if this is the last page
    if div.find('span', {'class' : 'guiArw pageEndNext'}): #Modified
        log.info("We reached last page")
        sys.exit()
    #If not, return the url to the next page
    hrefs = div.findAll('a', href= True)
    for href in hrefs:
    	#print 'GOING THROUGH HREFS'
    	#print href
        if href.find(text = True) == '&raquo;':
            log.info("Next url is %s" % href['href'])
            return href['href']


#MY FUNCTION
def get_hotel_info(hotel_url, hotel_count):
	"""
	#Take url from each individual hotel in the hotellist page
	#Get the html
	#Save html page to data
	#Go through each html to get necessary info
	#Print to log 
	"""
	hotel_info_list = []
	
	url = base_url + hotel_url
    # Sleep 2 sec before starting a new http request
	time.sleep(2)
    # Request page
	headers = { 'User-Agent' : user_agent }
	response = requests.get(url, headers=headers)
	html = response.text.encode('utf-8')
    # Save the webpage
	with open(os.path.join(args.datadir, args.city + '-hotel-' + str(hotel_count) + '.html'), "w") as h:
		h.write(html)
        
	soup = BeautifulSoup(html)
	div = soup.find("div", {"class" : "content wrap trip_type_layout"}) 
	
	travel_ratings_box = div.find("ul", {"class": "barChart"})
	
	travel_ratings_list = travel_ratings_box.findAll("span", {"class" : "compositeCount"})
	count_ratings = 0
	ratings = ['Excellent', 'Very good', 'Average', 'Poor', 'Terrible']
	for rating_num in travel_ratings_list:
		#print 'Going through travel ratings'
		print '%s : %s' % (ratings[count_ratings], rating_num.find(text=True))
		hotel_info_list.append(rating_num.find(text=True))
		count_ratings = count_ratings + 1
	
	trip_type_box = div.find("div", {"class": "trip_type"})
	
	trip_type_list = trip_type_box.findAll("div", {"class": "value"})
	
	trip_categories = ['Families', 'Couples', 'Solo', 'Business']
	
	count_type = 0
	for trip_type in trip_type_list:
		print '%s : %s' % (trip_categories[count_type], trip_type.find(text=True))
		hotel_info_list.append(trip_type.find(text=True))
		count_type = count_type + 1
	
	rating_summary_box = div.find("div", {"id": "SUMMARYBOX"})
	
	#<span class="rate sprite-rating_s rating_s">
	#<img class="sprite-rating_s_fill rating_s_fill s45" src="http://e2.tacdn.com/img2/x.gif" alt="4.5 of 5 stars">
	#</span>
	
	rating_list = rating_summary_box.find("ul").findAll("img")
	
	rating_categories = ['Location', 'Sleep Quality', 'Rooms', 'Service', 'Value', 'Cleanliness']
	
	count_rating =0
	for rating in rating_list:
		print '%s : %s' % (rating_categories[count_rating], rating['alt'].split()[0])
		hotel_info_list.append(rating['alt'].split()[0])
		count_rating = count_rating + 1
	
	"""
    hrefs = div.findAll('a', href= True)
    for href in hrefs:
    	#print 'GOING THROUGH HREFS'
    	#print href
        if href.find(text = True) == '&raquo;':
            log.info("Next url is %s" % href['href'])
            return href['href']
	"""
	return hotel_info_list
	

if __name__ == "__main__":
    # Get current directory
    current_dir = os.getcwd()
    # Create datadir if does not exist
    if not os.path.exists(os.path.join(current_dir, args.datadir)):
        os.makedirs(os.path.join(current_dir, args.datadir))

    # Get URL to obtaint the list of hotels in a specific city
    city_url = get_city_page(args.city, args.state)
    c=0
    
    #Column names for csv file
    col_names = ['HOTEL_NAME', 'STARS', 'TOTAL_REVIEWS', 'EXCELLENT', 'VERY_GOOD', 'AVERAGE', 'POOR', 'TERRIBLE', 'FAMILY', 'COUPLE', 'SOLO', 'BUSINESS', 'LOCATION', 'SLEEPQ', 'ROOM', 'SERVICE', 'VALUE', 'CLEANLINESS']

    #OPEN CSV FILE FOR WRITTING
    with open("BostonHotels.csv", "w") as output_file: 
        writer = csv.writer(output_file)
        writer.writerow(col_names)
        while(True):
            c +=1
            html = get_hotellist_page(city_url,c)
            city_url = parse_hotellist_page(html, writer)

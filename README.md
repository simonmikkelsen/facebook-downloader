Facebook Downloader
===================

Facebook Download is a Python script for downloading a group with events and pictures from Facebook
and converting it to HTML.

Because a group can require thousands of URLs being downloaded, the script contains features for
caching url contents and for just downloading data and converting it to html in a separate operation.

The generated HTML is very generic with all formating in a style sheet, which makes it easier to
adapt the desired look.

Run with -h to see options.

Tested with <python 2.7.x.

Example
=======

List alllgroups you have access to download with your credentials.
The access key given to the -a switch can be fetched from https://developers.facebook.com/tools/explorer/

download.py --list -a VG45FGHwretumhpf3DFGdsfsdf234dfSDFhrthSfW674ergrgERGF


Download data, cache it and export to html when finished.

download.py -g 123456789 --cache cache.json -f group.html -A access_token.txt


Download the group and save it to group.html. Note that if the script fails,
e.g. due to a timeout, you will have to redo everything. Data is not saved untill
everything is downloaded.

download.py -g 123456789 -f group.html


Download data only, cache all urls to cache.json and save data structure for exporting
to data.json. The access token from above is located in the file access_token.txt

download.py -g 123456789 --cache cache.json -j data.json -A access_token.txt


Export the data structure in data.json to group.html  

download.py -j data.json -f group.html -A access_token.txt


Download data, cache it and export to html when finished.

download.py -g 123456789 -j data.json -f group.html -A access_token.txt


If you want to see what happens, add a -v to the command line. Add a -v more
to get more output.

Note: When data is exported, the main.css file must manually be copied to the
same folder as the html file.

Contributing
============

I have written this to scratch my own itch. Further more I do not have a lot of
time. Feature requests are appriciated, but I will only implement one if it
I think it will help me and if I find the time to do it.

Please fork the repo, implement features or enhancements and make a pull request.
Please remember to comment your code, make readable names and variables, and
in general make nice and understandable code.

You will be credited for you work.

Authors
=======
Simon Mikkelsen (http://simonmikkelsen.dk/)
- Main author.

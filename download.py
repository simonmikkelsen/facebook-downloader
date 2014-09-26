#!/usr/bin/python

import json
import sys
import getopt

from fbdownload.grouplister import FacebookGroupLister
from fbdownload.groupdownloader import FacebookGroupDownloader
from fbdownload.htmlexporter import FacebookHtmlExporter

# Run the program if called stand alone.
if __name__ == "__main__":
  gid = None 
  access_token = None
  access_token_file = None
  filename = None
  jsonfile = None
  getImages = 'small'
  verbose = 0
  listGroups = False
  downloadEvents = True
  cache = None
  lightEvents = False
  slow = False

  try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:g:a:f:j:vA:",
                  ["help", "group=", "access-token=", "html-file=",
                   "json-file=", "images", "list-groups", "no-events",
                   "light-events", "cache=", "access-token-file="])
  except getopt.GetoptError, err:
    print str(err)
    sys.exit(2)
  for switch, value in opts:
    if switch in ("-h", "--help"):
      print """ dl.py Downloads a Facebook group
  -h --help         Print this message
  -g --group        Give the ID fo the group you want to download.
                    This is a number and NOT a name.
     --no-events    Do not download events.
     --light-events When downloading events, do not get lists of invited and
                    declined people.
     --list-groups  List all the groups with group IDs that the given access token
                    can access.
  -a --access-token Get one e.g. using https://developers.facebook.com/tools/explorer/
  -A --access-token-file  File where an access token is saved. Can be used instead
                    of giving it using -a. The file will be updated if the script
                    asks for a new access token.
  -f --html-file    If given, the result will be saved into this html file
                    with images located in the images folder of the same directory.
  -j --json-file    If given, the result will be saved into a json structure.
                    If no group ID is given using -g or --group, this file is
                    instead read and its data is used for the further operations.
     --slow         Sleeps after downloading an URL. Some firewalls only lets a
                    certain number of connections through every minute.
     --cache        Name of a file to use as a file cache. The file makes it possible
                    to avoid having to download already downloaded text based URLs.
"""
      sys.exit(0)
    elif switch in ("-i", "--images"):
      getImages = value
    elif switch in ("-v", "--verbose"):
      verbose += 1
    elif switch in ("-g", "--group"):
      gid = value
    elif switch in ("--no-events"):
      downloadEvents = False
    elif switch in ("-a", "--access-token"):
      access_token = value
    elif switch in ("-f", "--html-file"):
      filename = value
    elif switch in ("-j", "--json-file"):
      jsonfile = value
    elif switch in ("--list-groups"):
      listGroups = True
    elif switch in ("--cache"):
      cache = value
    elif switch in ("--light-events"):
      lightEvents = True
    elif switch in ("--slow"):
      slow = True
    elif switch in ("-A", "--access-token-file"):
      access_token_file = value

  # Is there anything to do?
  if jsonfile == None and filename == None and not listGroups:
    print "Nothing to do. Neither json nor html file is given and --list-groups"
    sys.exit()

  # Parse image parts.
  imagePartsToGet = [part.strip() for part in getImages.split(",")]
  # Validate image parts.
  for part in imagePartsToGet:
    if not part in ('none', 'small', 'medium', 'large', 'n', 's', 'm', 'l'):
      print "Unsupported value for -i or --images: '%s'" % part
      sys.exit()

  # List groups.
  if listGroups:
    lister = FacebookGroupLister(access_token)
    lister.setVerbose(verbose)
    lister.listGroups()
    # Don't stop: If people want to do multiple things, let them.

  data = None
  if gid:
    # Got group ID: Download data
    downloader = FacebookGroupDownloader(gid, access_token)
    downloader.setAccessTokenFile(access_token_file)
    downloader.setCacheFile(cache)
    downloader.setVerbose(verbose)
    downloader.setJsonFile(jsonfile)
    downloader.setSlow(slow)
    downloader.setLightEvents(lightEvents)
    data = downloader.download(downloadEvents = downloadEvents)
  elif jsonfile:
    # No group specified: Read the json file instead.
    with open (jsonfile, "r") as myfile:
      filedata=myfile.read().replace('\n', '')
      data = json.loads(filedata)

  # Export data
  if filename and data:
    exporter = FacebookHtmlExporter(filename, access_token)
    exporter.setVerbose(verbose)
    exporter.setDownloadImages(imagePartsToGet)
    exporter.exportToHtml2(data)

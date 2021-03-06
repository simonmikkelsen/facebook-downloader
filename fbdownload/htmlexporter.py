from fbdownload.downloader import FacebookDownloader
import urllib2
import os.path
import json
from fbdownload.htmlhelper import HtmlHelper
import dateutil.parser
import time

class FacebookHtmlExporter(FacebookDownloader):
  '''
  Takes an object hirachy that is created from a json file
  and exports the data as a Facebook group into a html file.
  Images are downloaded in this process, if they have have
  not yet been downloaded.
  '''
  
  def __init__(self, htmlFile, access_token):
    '''
    Creates a new instance.
    
    :param htmlFile: the path to the file to export to.
    :param access_token: a Facebook access token.
    '''
    FacebookDownloader.__init__(self, access_token)
    self.htmlFile = htmlFile
    self.verbose = 0
    self.getImages = ['small']
    
  def setHtmlFile(self, filename):
    self.htmlFile = filename
  def setVerbose(self, verbose):
    self.verbose = verbose
  def setDownloadImages(self, vals):
    self.getImages = vals
    
  def getImageFileName(self, url):
    '''
    Creates an image name from the given URL.
    The url will not be downloaded, so the method attemps to find the file type ind the url.
    :param url: The url to make a file name from.
    '''
    if url.find("?") > 0:
      url = url[:url.find("?")]
    filename = "images/"+url[url.find('//')+2:].replace("&", "_amp_").replace("?", "_question_").replace("=", "_equal_").replace("%", "_perct_").replace(":", "_colon_").replace("////", "/").replace("///", "/").replace("//", "/")
    if filename.endswith("/"):
      filename = filename+str(hash(url))+u".someimg"
    return filename

  def downloadImageFromObjectID(self, object_id):
    '''
    Downloads the json for the image represented by the given object_id. The id is e.g.
    found in an event or feed that has a picture. It does not look like it
    is related to a picture but it is.
    A list of the names of the downloaded images is returned.
    :param object_id: the ID of the picture.
    '''
    # Define URL.
    url = "https://graph.facebook.com/%s/" % object_id

    # Is images already downloaded?
    names = {}
    for size in ['small', 'medium', 'large']:
      dirname = self.getDirname(size)
      barename = dirname+"/"+object_id
      if os.path.isfile(barename):
        names += barename
      for ext in ['.jpg', '.png', '.gif', '.svg']:
        fullname = barename + ext
        if os.path.isfile(fullname):
          names[size] = fullname
          break # Breaks inner for
    if len(names) > 0:
      return names

    # Download file with links to all image sizes
    try:
      objectJson = self.downloadUrl(url)
    except urllib2.HTTPError, e:
      if e.code == 400:
        print "400 Bad request of image: "+url
        return []
      elif e.code == 404:
        print "404 Not found of image: "+url
        return []
      print "Error of image: "+url
      raise e
    if type(objectJson) is str:
      return self.downloadImages(json.loads(objectJson))
    else:
      # Unsupported request error.
      return []

  def downloadImages(self, imageObj, object_id = None):
    '''
    Given a Facebook image object (some json parsed into Python variables)
    the represented image is downloaded in several sizes.
    A list of the names of the downloaded images is returned.
    
    :param imageObj: representation of the image in json objects.
    :param object_id: object_id if available.
    '''
    if object_id == None:
      if 'id' in imageObj:
        object_id = imageObj['id']
      else:
        print "Error: Cannot download image. No object Id is given and none is in the json for the dict: '"+imageObj+"'"
        return []
    # Get URLs to download: Find largest and "medium" image.
    res = {}
    mediumWidth = 600
    mediumHeight = 400;
    if 'images' in imageObj:
      largestTotal = -1
      largestMediumWidth = -1
      largestMediumHeight = -1
      for image in imageObj['images']:
        height = image['height']
        width = image['width']
        if (width > largestMediumWidth or height > largestMediumHeight) and (width <= mediumWidth and height <= mediumHeight):
          largestMediumWidth = width
          largestMediumHeight = height
          res['medium'] = image['source']
        if width * height > largestTotal:
          res['large'] = image['source']
          largestTotal = width * height
    # The smallest is always the 'picture'
    if 'picture' in imageObj:
      res['small'] = imageObj['picture']

    # Download the found sizes:
    names = {}
    for key in res:
      dlurl = res[key]
      filename = self.getFilename(key, object_id, dlurl)
      # Only download unknown images.
      if os.path.isfile(filename):
        names[key] = filename
        continue
      retry = True
      while retry:
        try:
          resp = urllib2.urlopen(dlurl)
          if self.verbose > 1:
            print "Got: "+dlurl
          imageData = resp.read()
          retry = False
        except urllib2.HTTPError, e:
          if e.code == 404:
            print u"404 Not found: "+dlurl
            retry = False
            continue
          elif e.code == 403:
            print u"403 Forbidden: "+dlurl
            retry = False
            continue
          elif e.code == 504:
            print u"504 Gateway Time-out - retrying..."
            time.sleep(1)
            retry = True
            continue
          print dlurl
          raise e
        dirname = self.getDirname(key)
        if not os.path.isdir(dirname):
          os.makedirs(dirname)
  
        imgFp = open(filename, u'wb')
        imgFp.write(imageData)
        imgFp.close()
        names[key] = filename
    return names

  def getFilename(self, imageSize, object_id, dlurl):
    '''
    Creates a uniq file name for the given paramters.
    :param imageSize: Image size as a text string, e.g. small
    :param object_id: The Facebook ID of the image.
    :param dlurl: the URL from which the image can be downloaded.
    '''
    return self.getDirname(imageSize) + u"/"+object_id+self.getImageExtension(dlurl)
  
  def getDirname(self, imageSize):
    '''
    Returns the folder in which an image with the given size can be saved.
    :param imageSize: Image size as a text string, e.g. small
    '''
    return u"images/"+imageSize
  
  def getImageExtension(self, url):
    '''
    Attempts to extract the images' file extension based on the download url.
    Will return an empty string if none can be extracted.
    :param url: the download url of the image.
    '''
    url = url.lower()
    pos = url.find("?")
    if pos > 0:
      url = url[:pos]
    if url.endswith(".jpg"):
      return '.jpg'
    elif url.endswith(".png"):
      return '.png'
    elif url.endswith(".gif"):
      return '.gif'
    elif url.endswith(".svg"):
      return '.svg'
    else:
      return ''

  def fieldToDiv(self, field, fieldName, className = None):
    '''
    Creates a html div with the given fieldClass with the contents of
    field[fieldName], if fieldName exists as a key in field.
    If not, an empty string is returned. 
    :param field: the dictionary containing multiple values.
    :param fieldName: the key expected to exist in the dict.
    :param className: the name of the css class to use. If not specified the
    fieldName is used instead.
    '''
    if not type(field) is dict:
      raise BaseException("Given field is not dict but '%s' with value '%s' and fieldName '%s'." % (type(field), str(field), fieldName))
    if className == None:
      className = fieldName
    if fieldName in field:
      html = []
      html.append(u"""<div class="%s">""" % className)
      html.append(HtmlHelper.escapeHtml(field[fieldName]))
      html.append(u"""</div>""")
      return "".join(html)
    else:
      return ""
    
  def user2Html(self, user):
    '''
    Takes a user object and returns html for it.
    :param user: The user object.
    '''
    return u"""<a href="https://facebook.com/""" +user['id']+ u'/"/>'+user['name']+u"</a>"
  
  def userList(self, users):
    '''
    Takes a list of users and returns a comma separated list of them in html.
    :param users: the list of users.
    '''
    userList = []
    for user in users:
      userList.append(u"""<div class="person">"""+self.user2Html(user)+u"""</div>""")
    return ", ".join(userList)

  def gpsDegreesToDaysMinSec(self, deg):
    '''
    Takes a decimal GPS coordinate in degrees, e.g. 56.9283128 and returns a list
    with the corresponding degrees minutes seconds (in that order).
    For a GPS coordinate with both latitude and longitude you will have to use
    this method of each of them.
    :param deg: [degrees, minutes, seconds]
    '''
    # Thanks: http://stackoverflow.com/questions/2056750/lat-long-to-minutes-and-seconds
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]

  def address2Html(self, address):
    '''
    Creates html that shows a Facebook address, e.g. a address from an event.
    :param address: the address to display.
    '''
    html = []
    html.append(u"""<div class="address">""")
    html.append(self.fieldToDiv(address, 'street', 'street'))
    html.append(self.fieldToDiv(address, 'zip', 'zip'))
    html.append(self.fieldToDiv(address, 'city', 'city'))
    html.append(self.fieldToDiv(address, 'country', 'country'))
    if 'latitude' in address and 'longitude' in address:
      lat = address['latitude']
      longi = address['longitude']
      latParts = self.gpsDegreesToDaysMinSec(lat)
      longParts = self.gpsDegreesToDaysMinSec(longi)
      serviceUrl = "http://tools.wmflabs.org/geohack/geohack.php?params=%s_%s_%s_N_%s_%s_%s_E" % (latParts[0], latParts[1], latParts[2], longParts[0], longParts[1], longParts[2])
      html.append(u"""<div class="maps">""")
      html.append(u"""<a href="%s" target="_blank">%s</a>, """ % (serviceUrl, "Maps and photos"))
      html.append(u"""<a href="http://www.openstreetmap.org/?mlat=%s&mlon=%s&zoom=16#map=16/%s/%s" target="_blank">%s</a>, """ % (lat, longi, lat, longi, "OpenStreetMap"))
      html.append(u"""GPS: %s, %s """ % (lat, longi))
      html.append(u"""</div>""")
    html.append(u"""</div>""")
    return "".join(html)

  def event2Html(self, event):
    '''
    Exports teh given events to HTML and returns it as a list of lines
    in a html file. These can be joined using "".join(list).
    '''
    html = []
    html.append(u"""<div class="event">""")
    if 'event' in event:
      eventEvent = event['event']
      html.append(self.fieldToDiv(eventEvent, 'name', 'title'))
      if 'owner' in eventEvent:
        html.append(u"""<div class="owner">""")
        html.append(self.user2Html(eventEvent['owner']))
        html.append(u"""</div>""")
      html.append(self.fieldToDiv(eventEvent, 'location', 'location'))
      if 'venue' in eventEvent:
        html.append(self.address2Html(eventEvent['venue']))
      html.append(self.fieldToDiv(eventEvent, 'start_time', 'startTime'))
      html.append(self.fieldToDiv(eventEvent, 'description', 'description'))
      if 'photos' in event:
        for photo in event['photos']:
          res = self.downloadImages(photo)
          html.append(self.image2Html(res))
      
      if 'feed' in event:
        html.append(u"""<div class="comments">""")
        html.append(self.messages2Html(event['feed']))
        html.append(u"""</div>""")
      if 'attending' in event:
        html.append(u"""<div class="attending">Attending: """)
        html.append(self.userList(event['attending']))
        html.append(u"""</div>""")
      if 'maybe' in event:
        html.append(u"""<div class="maby">Maby: """)
        html.append(self.userList(event['maybe']))
        html.append(u"""</div>""")
      if 'declined' in event:
        html.append(u"""<div class="declined">Declined: """)
        html.append(self.userList(event['declined']))
        html.append(u"""</div>""")
    html.append(u"""</div>""") #End class=event
    return html

  def events2Html(self, events):
    '''
    Creates html that shows a Facebook event.
    :param data: the data of an event.
    '''
    html = []
    for event in events:
      html += self.event2Html(event)
    return "\n".join(html)
  
  def image2Html(self, gotImages, link = None):
    '''
    Returns html for the given images.
    :param gotImages: Image objects.
    :param link: Optional link for the image.
    '''
    html = []
    if link == None and 'link' in gotImages:
      link = gotImages['link']
    for size in ['medium', 'small', 'large']:
      if size in gotImages:
        if link != None:
          html.append(u"<div class=\"picture\"><a href=\"%s\" target=\"_blank\"><img src=\"%s\" /></a></div>\n" % (link, gotImages[size]))
        else:
          html.append(u"<div class=\"picture\"><img src=\"" + gotImages[size]+u"\" /></div>\n")
        break
    html.append(u"<div class=\"downloadImages\">")
    for size in ['small', 'medium', 'large']:
      if size in gotImages:
        html.append(u"<a href=\"%s\" target=\"_blank\">%s</a> " % (gotImages[size], size.title()))
    html.append(u"</div>")
    return "".join(html)

  def message2Html(self, msg):
    '''
    Exports the given message to HTML and returns it as a list of lines
    in a html file. These can be joined using "".join(list).
    '''
    html = []
    html.append(u"""<div class="message">""")
    if 'from' in msg:
      html.append(u"""  <div class="from">""")
      html.append(self.user2Html(msg['from']))
      html.append(u"</div>\n")
    if 'message' in msg:
      html.append(u"""  <div class="body">""")
      html.append(HtmlHelper.escapeHtml(msg['message']))
      html.append(u"</div>\n")
    elif 'type' in msg and msg['type'] == 'photo' and 'story' in msg:
      html.append(u"""  <div class="body">""")
      html.append(HtmlHelper.escapeHtml(msg['story']))
      html.append(u"</div>\n")
    link = None
    if 'link' in msg:
      link = msg['link']
    addedImageWithLink = False
    if 'picture' in msg:
      gotImages = False
      if 'object_id' in msg:
        gotImages = self.downloadImageFromObjectID(msg['object_id'])
        html.append(self.image2Html(gotImages, link))
        if link != None:
          addedImageWithLink = True
    if not addedImageWithLink and link != None:
      html.append(u"<div class=\"link\" target=\"_blank\"><a href=\"" + link + u"\">" + link + u"</a></div>\n")
    if 'created_time' in msg:
      html.append(u"""  <div class="info">""")
      html.append(msg['created_time'])
      html.append(u"</div>\n")
    if 'likes' in msg:
      html.append(u"<div class=\"msgLikeCount\">Likes: " + str(len(msg['likes']['data'])) + "</div>\n")
      html.append(u"""  <div class="likes">Likes: \n""")
      for user in msg['likes']['data']:
        html.append(u"""    <div class="like">""")
        html.append(self.user2Html(user))
        html.append(u"</div>\n")
      
      html.append(u"</div>\n")
    if 'like_count' in msg and msg['like_count'] > 0:
      html.append(u"<div class=\"likeCount\">Likes: " + str(msg['like_count']) + u"</div>\n")
    if 'comments' in msg:
      html.append(u"""<div class="comments">""")
      html.append(self.messages2Html(msg['comments']['data']))
      html.append(u"</div> <!-- comments -->\n")
    html.append(u"</div>\n") # /message
    return html

  def messages2Html(self, data):
    '''
    Creates html that shows Facebook messages.
    :param data: List of Facebook messages.
    '''
    html = []
    for msg in data:
      html += self.message2Html(msg)
    return "".join(html)

  def exportToHtml(self, data):
    '''
    Export the given data to HTML, with events first and messages in the bottom.
    :param data:
    '''
    fp = open(self.htmlFile, u'wb')
    fp.write("""<html><head><meta charset="utf-8"><link href="main.css" rel="stylesheet" type="text/css" /></head><body>\n""")
    if 'events' in data:
      fp.write(self.events2Html(data['events']).encode('utf8'))
    if 'group.posts' in data:
      fp.write(self.messages2Html(data['group.posts']).encode('utf8'))
    fp.write("""</body></html>\n""")
    fp.close()
    
  def exportToHtml2(self, data):
    '''
    Export the given data to HTML, so events and messages are mixed and
    sorted by date.
    '''
    # Put all messages or events into elements for sorting.
    elements = []
    if 'events' in data:
      for event in data['events']:
        elements.append(ExportElement(event['event']['updated_time'], 'event', event))
    if 'group.posts' in data:
      for post in data['group.posts']:
        elements.append(ExportElement(post['updated_time'], 'post', post))
    
    # Sort everything.
    elements.sort()
    elements.reverse()
    
    # Export to HTML.
    fp = open(self.htmlFile, u'wb')
    fp.write("""<html><head><meta charset="utf-8"><link href="main.css" rel="stylesheet" type="text/css" /></head><body>\n""")
    for ele in elements:
      if ele.kind == 'post':
        fp.write(u"\n".join(self.message2Html(ele.element)).encode('utf8'))
      elif ele.kind == 'event':
        fp.write(u"\n".join(self.event2Html(ele.element)).encode('utf8'))
      else:
        print "Unknown kind: "+ele.kind
    fp.write("""</body></html>\n""")
    fp.close()
    
class ExportElement:
  '''
  Class that holds data to be exported, in an easy to sort format.
  '''
  def __init__(self, time, kind, element):
    # E.g. of date: 2014-11-16T20:00:00+0100
    self.time = dateutil.parser.parse(time)
    self.kind = kind
    self.element = element
  def __lt__(self, other):
    return self.time < other.time
  def __eq__(self, other):
    return self.time == other.time


import urllib2
import json
import sys
import time
import os.path

from urllib import urlencode
from urlparse import urlparse, parse_qs, urlunparse

class FacebookDownloader:
  '''
  Generic class that can download a data structure via the Facebok API
  which contains pagination. This is e.g. a list of goups or a feed.
  '''
  def __init__(self, access_token):
    '''
    Creates a new instance.
    :param access_token: A Facebook access token.
    '''
    self.data = {}
    self.access_token = access_token
    self.verbose = 0
    self.jsonFile = None
    self.cacheFile = None
    self.cache = None
    self.accessTokenFile = None
    self.slow = False
    
  def setCacheFile(self, cacheFile):
    '''
    Sets a file where downloaded text URLs are saved.
    This makes it possible to redo the download command without downloading
    the already downloaded data.
    '''
    self.cacheFile = cacheFile
    if cacheFile != None and os.path.isfile(cacheFile):
      with open (cacheFile, "r") as myfile:
        filedata=myfile.read().replace('\n', '')
        self.cache = json.loads(filedata)
    else:
      self.cache = {}
      
  def setVerbose(self, verbose):
    '''
    Sets verbosity.
    :param verbose: 0 is none, increase to get more info.
    '''
    self.verbose = verbose
  def setJsonFile(self, filename):
    '''
    Set the json file to save to.
    :param filename: the file to save to.
    '''
    self.jsonFile = filename
    
  def saveDatasets(self):
    '''
    Saves the currently set data into the set json file.
    '''
    fp = open(self.jsonFile, 'wb')
    fp.write(json.dumps(self.data))
    fp.close()

  def downloadUrl(self, url):
    '''
    Download the given URL and haldle errors such as timeout and
    authentication that needs to be redone.
    '''
    if self.access_token == None:
      print "Not authenticated. Go to https://developers.facebook.com/tools/explorer/"
      print "reauthenticate, paste the access token in here and press enter:"
      self.setAccessToken(sys.stdin.readline())
      
    success = False
    while not success:
      # Always make sure the access token is on the URL, even if it has changed.
      url = self.createUrlWithoutAuth(url)
      if not "?" in url:
        url = url + "?"
      else:
        url = url + "&"
      url = url + "access_token="+self.access_token
      
      try:
        if self.verbose > 0:
          print "Download '%s'." % url
        response = urllib2.urlopen(url)
        jsondata = response.read()
        success = True
        if self.slow:
          time.sleep(1) #Sleep to not overload server or firewall.
      except urllib2.URLError as e:
        if str(e.reason).find("[Errno 10060]") != -1:
          print "Timeout: Wil retry in 5 seconds..."
          time.sleep(5)
        elif hasattr(e, 'code') and e.code == 400:
          responsebody = e.read()
          if responsebody != None and len(responsebody) > 0:
            respJson = json.loads(responsebody)
            if 'error' in respJson and 'code' in respJson['error'] and respJson['error']['code'] == 100:
              # Unsupported get request.
              print "Got unsupported get request for url '%s'." % url
              return None
              
          print "Not authenticated (2). Go to https://developers.facebook.com/tools/explorer/"
          print "reauthenticate, paste the access token in here and press enter:"
          self.setAccessToken(sys.stdin.readline())
        elif hasattr(e, 'code') and e.code == 500:
          print url
          responsebody = e.read()
          print "Got error 500:"
          print responsebody
          raise e
        else:
          raise e
    
    return jsondata
  def setSlow(self, slow):
    '''
    Sets if the downloader must sleep a little after each download. Some firewalls
    only lets a certain number of connections through every minute.
    '''
    self.slow = slow
  def setAccessTokenFile(self, accessTokenFile):
    '''
    Sets the path to a file where the access token is read from and written to.
    Will read the access token from that file at the same time if the file exists.
    '''
    self.accessTokenFile = accessTokenFile
    if accessTokenFile != None and os.path.isfile(accessTokenFile):
      with open (accessTokenFile, "r") as myfile:
        filedata=myfile.read()
        if len(filedata) > 0:
          self.access_token = filedata

  def setAccessToken(self, access_token):
    '''
    Sets the given access token and writes it to a cache file if requested.
    '''
    self.access_token = access_token
    if self.accessTokenFile != None:
      fp = open(self.accessTokenFile, 'w')
      fp.write(self.access_token)
      fp.close()

  def createUrlForCache(self, url):
    '''
    Creates the URL that is used in the cache.
    '''
    return self.createUrlWithoutAuth(url)

  def createUrlWithoutAuth(self, url):
    '''
    Creates the URL without authentication.
    It makes sure elements like the access_token is removed.
    '''
    parsed = urlparse(url)
    qd = parse_qs(parsed.query, keep_blank_values=True)
    filtered = dict( (k, v) for k, v in qd.iteritems() if not k == 'access_token')
    newurl = urlunparse([
      parsed.scheme,
      parsed.netloc,
      parsed.path,
      parsed.params,
      urlencode(filtered, doseq=True), # query string
      parsed.fragment
    ])
    return newurl
    
  def putInCache(self, url, jsondata):
    """Puts the given data into the cache by the given url."""
    if self.cache == None:
      return
    url = self.createUrlForCache(url)
    self.cache[url] = jsondata
    if self.cacheFile != None and len(self.cacheFile) > 0:
      if self.verbose > 2:
        print "Update cache, now %s entries." % len(self.cache)
      fp = open(self.cacheFile, 'wb')
      fp.write(json.dumps(self.cache))
      fp.close()

  def downloadData(self, url, key = None, multipleElements = True):
    '''
    Downloads the data pointed to by the given URL and handles pagination.
    
    :param url: The one to download.
    :param key: If given, data is saved under this key and not just a flat
    list. This must be set for saveDataset() to save the data.
    :param multipleElements: If True (default) the data will be treated as a
    Facebook multi element data structure, that contains info for pagination.
    This is e.g. a feed or list of attendees for an event.
    If False pagination will not be handled, but this can be used to download
    all other data structures. A single dict will be returned.
    '''
      
    datasets = []
    
    while url:
      cachurl = self.createUrlForCache(url)
      if self.cache != None and cachurl in self.cache:
        if self.verbose > 1:
          print "Get '%s' from cache." % url
        jsondata = self.cache[cachurl]
      else:
        jsondata = self.downloadUrl(url)
        if jsondata == None:
          url = None
          continue
        self.putInCache(url, jsondata)
      
      # Handle paging.
      url = None
      data = None
      multiElementData = json.loads(jsondata)
      if multipleElements:
        if 'paging' in multiElementData:
          if 'next' in multiElementData['paging']:
            url = multiElementData['paging']['next']
        data = multiElementData['data']
        data = self.ensureInternalPaging(data)
        if self.verbose > 0:
          print "Downloaded %s entries." % len(data)
        # On multiple elements, data is a list of data, so merge them.
        datasets += data
      else:
        datasets = multiElementData
      
      # Store the data under the given key.
      if key != None:
        if not key in self.data:
          self.data[key] = []
        # Add the data, if the key have been used in multiple calls (e.g. paging).
        self.data[key] += data
        if self.jsonFile != None:
          self.saveDatasets()
        
    if key != None:
      if not key in self.data:
        return []
      # Return the data from the key, with support for multiple calls for the same data.
      return self.data[key]
    else:
      # We have not stored anything: Return the internal dataset instead.
      return datasets

  def getCompletePaging(self, pagingEntry):
    '''
    Receives a data structure that may contain paging. If it does, the whole
    chain of urls are downloaded and merged into the data element.
    E.g. in:
    {data:[stuff, stuff], paging:{next:"http://..."}}
    E.g. out:
    {data:[stuff, stuff, more stuff, even more stuff]}
    
    Note: The paging element may still be present and it may be removed in
    future versions. Please just ignore it or handle that it may not be there.
    '''
    data = pagingEntry['data']
    
    if 'paging' in pagingEntry and 'next' in pagingEntry['paging']:
      data += self.downloadData(pagingEntry['paging']['next'], multipleElements = True)
    pagingEntry['data'] = data
    return pagingEntry
  
  def ensureInternalPaging(self, data):
    '''
    Takes a data structure, that may contain the sub elements comments or likes.
    These contains a list of data and a paging dictionary. If that paging dict
    contains a next link, that link and the rest of the chain is downloaded.
    The structure is then merged into a single list, where it is not nessesary
    to perform any paging to get more data.
    That final list is returned, along with the original input data.
    E.g.
    In:
    [{foo:bar, comments:{data:[stuff, stuff], paging:{next:"http://..."}}}]
    Out
    [{foo:bar, comments:{data:[stuff, stuff, more stuff, even more stuff]}}]
    
    Note: The paging element may still be present and it may be removed in
    future versions. Please just ignore it or handle that it may not be there.
    '''
    resData = []
    pagingKinds = ['comments', 'likes']
    for entry in data:
      for kind in pagingKinds:
        if kind in entry:
          if self.verbose > 0:
            print "Get paging... for "+kind
          entry[kind] = self.getCompletePaging(entry[kind])
      resData.append(entry)
    return resData

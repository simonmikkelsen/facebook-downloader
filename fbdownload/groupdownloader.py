from fbdownload.downloader import FacebookDownloader

class FacebookGroupDownloader(FacebookDownloader):
  '''
  Downloads data from a Facebook group, including events.
  Images are not downloaded.
  In this package of classes, that is done by the
  FacebookHtmlExporter, even though a stand alone download
  function would be nice.
  '''
  def __init__(self, groupId, access_token):
    '''
    Creates a new instance.
    
    :param groupId: the ID of the group to download. Use th
    FacebookGroupLister to get it.
    :param access_token: The Facebook access token.
    '''
    FacebookDownloader.__init__(self, access_token)
    self.groupId = groupId
    self.lightEvents = False

  def download(self, downloadEvents = True):
    '''
    Download everything.
    '''
    if downloadEvents:
      self.downloadEvents()
    elif self.verbose > 0:
      print "Do not download events."
    self.downloadGroup()
    return self.data
  
  def downloadGroup(self):
    '''
    Download the groups feed.
    '''
    url = "https://graph.facebook.com/%s/feed" % self.groupId
    return self.downloadData(url, 'group.posts')
  
  def downloadEvents(self):
    '''
    Download the groups events.
    '''
    url = "https://graph.facebook.com/%s/events" % self.groupId
    objects = []
    events = self.downloadData(url, 'group.events')
    for event in events:
      eventContents = {}
      url = "https://graph.facebook.com/%s/" % event['id']
      eventContents['event'] = self.downloadData(url, multipleElements = False)
      if self.lightEvents:
        pagesToGet = ['feed', 'attending', 'photos']
      else:
        pagesToGet = ['feed', 'attending', 'declined', 'invited', 'maybe', 'noreply', 'photos', 'videos']
      for action in pagesToGet:
        url = "https://graph.facebook.com/%s/%s/" % (event['id'], action)
        eventContents[action] = self.downloadData(url, multipleElements = True)
      objects.append(eventContents)
      # TODO Download, photos, videos here and not in the exporter.
      # url = "https://graph.facebook.com/%s/picture/" % event['id']

      self.data['events'] = objects
      if self.jsonFile != None:
        self.saveDatasets()
    return objects
  
  def setLightEvents(self, lightEvents):
    '''
    When True, only the most important attributes of an event are downloaded.
    '''
    self.lightEvents = lightEvents

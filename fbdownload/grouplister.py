from fbdownload.downloader import FacebookDownloader
import re

class FacebookGroupLister(FacebookDownloader):
  '''
  Returns or lists the groups that the given access token can access and is
  a member of.
  '''

  def __init__(self, access_token):
    '''
    Creates a new instance.
    :param access_token: A Facebook access token.
    '''
    FacebookDownloader.__init__(self, access_token)
  def getGroups(self):
    '''
    Returns a list of objects containing the name and id of the group, and
    the users sorting of it, if applies.
    '''
    url = "https://graph.facebook.com/me/groups?access_token=%s" % self.access_token
    groups = self.downloadData(url)
    return groups

  def listGroups(self):
    '''
    Prints a list of the groups the given access token can access.
    '''
    g = self.getGroups()
    print g
    for group in g:
      # TODO
      # I have a unicode problem, so remove anything but certain ASCII chars.
      # Ugly but works.
      name = re.sub(ur'[^a-zA-Z0-9 _-]+', u'?', group['name']) 
      print name+u": "+group['id'].encode('utf8')

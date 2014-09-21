
class HtmlHelper:
  @staticmethod
  def escapeHtml(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;').replace("\n\r", "\n").replace("\n", "<br />")

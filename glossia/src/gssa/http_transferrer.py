from zope.interface import implementer
import urllib.request as urllib2
import os
import logging
import requests

logger = logging.getLogger(__name__)

from .error import Error, makeError

from .transferrer import ITransferrer


# Gets input files from an HTTP source
@implementer(ITransferrer)
class HTTPTransferrer:
    def __init__(self):
        pass

    def connect(self):
        pass

    def disconnect(self):
        logger.debug("Disconnecting")

    def pull_files(self, files, root, remote_root):
        """Uses downloadFile to pull."""
        for local, remote in files.items():
            remote_url = "%s/%s" % (self._url, remote)
            absolute_path = os.path.join(root, local)
            logger.debug("Download File From: " + remote_url)
            logger.debug("Download File To:" + absolute_path)
            directory = os.path.dirname(absolute_path)
            logger.debug("Directory Created: " + directory)
            os.makedirs(directory, exist_ok=True)

            self.downloadFile(remote_url, absolute_path)

    def push_files(self, files, root, remote_root):
        """Push using HTTP (unless we are told to use `tmp`)."""
        for local, remote in files.items():
            absolute_path = os.path.join(root, local)
            logger.debug("Uploading from: " + absolute_path + " to:" + remote)
            self.uploadFile(absolute_path, remote)

    def downloadFile(self, sourceUrlStr, destinationStr):
        """Downloads a file from the source URL to the destination (typically a folder).

        This just grabs using urllib GET.

        Args:
            sourceUrlStr: Url of the file which will be downloaded
            destinationStr: FullPath to the destination

        """
        if not os.path.exists(destinationStr):
            '''Check If we have downloaded the file already'''
            logger.debug("Download: " + sourceUrlStr + " to " + destinationStr)

            '''download the file'''
            try:
                serverFile = urllib2.urlopen(sourceUrlStr)
            except:
                raise RuntimeError(makeError(Error.E_SERVER, "download failed"))
            localFile = open(destinationStr, "wb")
            localFile.write(serverFile.read())
            serverFile.close()
            localFile.close()

    def uploadFile(self, sourcePath, destinationUrl):
        """Uploads the file located in sourcePath to the destinationUrl.

        This uploads with a POST.

        Args:
            sourcePath: fullpath to the file which will be uploaded
            destinationUrl: Url where the file is send to

        """
        logger.debug("upload " + sourcePath + " to " + destinationUrl)
        try:
            f = {'file': open(sourcePath, 'rb')}
        except:
            logger.warning("file " + sourcePath + " does not exist.")
        try:
            r = requests.post(destinationUrl,
                              files=f)
        except:
            logger.exception("Server error!")
        if (r.status_code != 200):
            logger.error("Upload Failed")

    def configure_from_xml(self, xml):
        """The XML should indicate the source/destination URL."""
        self._url = xml.find("url").text
        self._output = xml.find("output")
        if self._output is not None:
            logger.warning("Outputting to tmp")
            self._output = self._output.text

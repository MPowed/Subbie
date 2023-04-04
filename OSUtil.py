from xmlrpc.client import ServerProxy, ProtocolError
import zlib, base64, os, time, requests, sys, struct
from cchardet import detect
from datetime import datetime
#from pythonopensubtitles.utils import File

# We are talking to the GUI status output whenever you see a q.put


class OSutil():

	#Init the backend program for subbie
	def __init__(self, name, password, library_path, q, language='eng', user_agent='Adefjukie'):#UserAgent registered with opensubtitles.
																					#UserAgent makes the username and password unneeded.
		# We are talking to the GUI status output whenever you see a q.put
		q.put_nowait('Starting')

		time.sleep(1)
		self.time_limit = 300 # 5 minutes
		self.last_checked = datetime.now()
		self.library_path = library_path
		self.username = name
		self.password = password
		self.url = 'http://api.opensubtitles.org/xml-rpc' #Import API

		self.server = ServerProxy(self.url)
		self.login_status = False
		
		#The Open subtitles server is bad and sometimes does not respond for a minute. 5 minutes is overkill
		while self.login_status == False:
			self.started = datetime.now()
			if (self.started-self.last_checked).seconds >= self.time_limit:
				
				# Alert the user that we are stuck waiting for the server.
				self.last_checked = datetime.now()
				q.put_nowait('It seems the server is down. Try again another time')

			# The Open Subtitles server seems to go down for a second now and then. Waiting for it to return fixes issue	
			try:
				self.token = self.server.LogIn(self.username, self.password, language, user_agent)['token']
				self.login_status = True
			except:
				print('The OpenSubtitles server is down, trying again in 30 seconds')
				q.put_nowait('The OpenSubtitles server is down, trying again in 30 seconds')
				time.sleep(30)



	def decompress(self, data, q, encoding='utf-8'):

		self.raw_subtitle = zlib.decompress(base64.b64decode(data), 16 + zlib.MAX_WBITS)
		self.encode_detect = detect(self.raw_subtitle)

		try:
			self.decoded = self.raw_subtitle.decode(self.encode_detect['encoding'])
		except UnicodeDecodeError as e:
			q.put_nowait(e)
			return

		return self.decoded

	def getHash(self, path, file):
		'''Original from: http://goo.gl/qqfM0
		'''

		self.longlongformat = 'q'  # long long
		self.bytesize = struct.calcsize(self.longlongformat)

		try:
			self.file = open(path + file, "rb")
		except(IOError):
			return "IOError"
		time.sleep(.1)
		self.size = os.path.getsize(path + file) 
		hash = int(self.size)

		if int(self.size) < 65536 * 2:
			return "SizeError"

		for _ in range(65536 // self.bytesize):
			buffer = self.file.read(self.bytesize)
			self.l_value = struct.unpack(self.longlongformat, buffer)
			hash += self.l_value
			hash = hash & 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

		self.file.seek(max(0, int(self.size) - 65536), 0)
		for _ in range(65536 // self.bytesize):
			buffer = self.file.read(self.bytesize)
			self.l_value = struct.unpack(self.longlongformat, buffer)
			hash += self.l_value
			hash = hash & 0xFFFFFFFFFFFFFFFF

		self.file.close()
		self.returnedhash = "%016x" % hash
		return str(self.returnedhash)


	def searchSubQuery(self, movieName, path):
		self.fullMovieName = movieName
		if '2160p' in movieName:
			self.shortMovieName = movieName.split('.2160p.')
			self.data = self.server.SearchSubtitles(self.token, [{'sublanguageid': 'eng', 'query': self.shortMovieName[0]}])
			return self.data
		elif '1080p' in movieName:
			self.shortMovieName = movieName.split('.1080p.')
			self.data = self.server.SearchSubtitles(self.token, [{'sublanguageid': 'eng', 'query': self.shortMovieName[0]}])
			return self.data
		elif '720p' in movieName:
			self.shortMovieName = movieName.split('.720p.')
			self.data = self.server.SearchSubtitles(self.token, [{'sublanguageid': 'eng', 'query': self.shortMovieName[0]}])
			return self.data
		else:
			self.movieHash = self.getHash(self.library_path, movieName)
			self.movieSize = str(os.path.getsize(path + '/' + movieName))
			self.data = self.server.SearchSubtitles(self.token, [{'sublanguageid': 'eng', 'moviehash': self.movieHash, 'moviebytesize': self.movieSize}])

	#Download the subtitle and save it to a file, while editing it for random advertisements
	def dlSub(self, ids,
						outputDirectory, q,
						encoding='utf-8'):
		
		last_chars = ''
		last_chars = self.fullMovieName[-4:]
		#avoid duplicates and seperated for future editing
		if  last_chars == '.jpg':
			pass
		elif  last_chars == '.srt':
			pass
		elif  last_chars == '.nfo':
			pass
		else:
			self.successful = {}
			self.data = self.server.DownloadSubtitles(self.token, ids)
			self.encodedData = self.data.get('data')
			for item in self.encodedData:
				self.subfile_id = item['idsubtitlefile']

				self.decodedData = self.decompress(item['data'], q, encoding=encoding)
				with open(r"files\\ads\\del_list.txt") as file_in:
					del_list = file_in.readlines()
					file_in.close()




				#They added links that are random. so lets cut it off
				with open(r"files\\ads\\end_cutoff.txt") as file_in:
					end_cutoff = file_in.readlines()
					file_in.close()
				for x, val in enumerate(del_list):
					self.decodedData = self.decodedData.replace(del_list[x].strip(), '')  
				try:
					self.decodedData = self.decodedData[0 : self.decodedData.index('Please rate this subtitle')]
				except:
					pass
				#self.fileName = self.override_filenames.get(self.subfile_id, self.subfile_id + '.' + extension)
				self.fileName = self.fullMovieName + '.srt'
				self.filePath = os.path.join(outputDirectory, self.fileName)
				try:
					with open(self.filePath, 'w', encoding="utf-8") as file:
						file.write(self.decodedData)
						file.close()
					self.successful[self.subfile_id] = self.filePath
				except IOError as error:
					print("There was an error writing file {}.".format(self.filePath),
					file=sys.stderr)
					q.put_nowait(error)

	#Combine the order of things to run when process is triggered 
	def backendProgram(self, q):

		for self.path, self.subdirs, self.files in os.walk(self.library_path):
			for self.file in self.files:
				q.put_nowait(self.file)
				self.success = False
				while self.success == False:
					try:
						self.finalData = self.searchSubQuery(self.file, self.path)
						self.success = True
						time.sleep(.5)
						if self.finalData == None:
							break


						for self.record in self.finalData["data"]:
							if self.record.get('SubForeignPartsOnly') == '1':
								q.put_nowait('Found 1')
								self.dlSub([self.record["IDSubtitleFile"]], self.path, q)
								break
					except ProtocolError:
						q.put_nowait('To Many Requests, Trying again in 10 seconds (Normal for large libraries)')
						time.sleep(10.3)

		q.put_nowait('Finished')




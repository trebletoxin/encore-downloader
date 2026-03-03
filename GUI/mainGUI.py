import requests, json, asyncio, aiohttp, sys, os, platform, shutil, re, io, hashlib
from zipfile import ZipFile
from random import randbytes
from gooey import Gooey, GooeyParser
from typing import Optional, Union
import numpy
os.environ["PYTHONIOENCODING"] = "utf-8"

class SNGHandler:
	def __init__(self, submission: Union[str,bytes], playlist: str=None, sanitize=True):
		if not ((isinstance(submission, bytes) and (submission[:6].decode('utf-8') == "SNGPKG") or submission[:4] == b"\x50\x4B\x03\x04") or
			(os.path.isfile(os.path.join(submission,"song.ini")) and
			(os.path.isfile(os.path.join(submission,"notes.chart")) or os.path.isfile(os.path.join(submission,"notes.mid"))))):
			raise TypeError("Submission must be a directory of a single chart or the bytes of an .sng")
		self._playlist = playlist
		self._sanitize = sanitize

		if isinstance(submission, bytes):
			self._files = self.get_sng_files(submission)
		
		else:
			if isinstance(submission, bytes) and submission[:4] == b"\x50\x4B\x03\x04":
				iszip = True
				with ZipFile(io.BytesIO(submission), 'r') as zip_file:
					all_files = zip_file.namelist()

					containing_paths = []
					for file_path in all_files:
						if file_path.lower().endswith('song.ini'):
							if file_path == 'song.ini':
								dir_path = ""
							else:
								dir_path = file_path.rsplit('/',1)[0]
							containing_paths.append(dir_path)

					target_dir = min(containing_paths,key=len)
					if target_dir == "":
						files = [f.lower() for f in all_files if "/" not in f and f != ""]
						file_paths = [f for f in all_files if "/" not in f and f != ""]
					else:
						files = [f.lower().split('/')[-1] for f in all_files if f.startswith(target_dir + "/") and "/" not in f.split(target_dir+"/")[1] and f.split('/')[-1] != "" ]
						file_paths = [f for f in all_files if f.startswith(target_dir + "/") and "/" not in f.split(target_dir+"/")[1] and f.split('/')[-1] != "" ]

			else:
				iszip = False
				files = os.listdir(submission)

			results = []

			valid_picture_names = ("album.","background.","highway.")
			valid_picture_extensions = ("png","jpg","jpeg")
			valid_music_names = ("guitar.","bass.","rhythm.","vocals.","vocals_1.","vocals_2.","drums.","drums_1.","drums_2.","drums_3.","drums_4.","keys.","song.","crowd.","preview.")
			valid_music_extensions = ("mp3","ogg","opus","wav")
			valid_video_names = ("video.")
			valid_video_extensions = ("mp4","avi","webm","vp8","ogv","mpeg")
			valid_notes = ["notes.chart","notes.mid"]
			valid_songini = "song.ini"

			for index, file in enumerate(files):
				if ((file.lower().startswith(valid_picture_names) and file.lower().endswith(valid_picture_extensions)) or
					(file.lower().startswith(valid_music_names) and file.lower().endswith(valid_music_extensions)) or
					(file.lower().startswith(valid_video_names) and file.lower().endswith(valid_video_extensions)) or
					(file.lower() in valid_notes) or
					(file.lower() == valid_songini)):
					if iszip:
						with ZipFile(io.BytesIO(submission), 'r') as zip_file:
							file_bytes = zip_file.read(file_paths[index])
							results.append([file, file_bytes])
					else:
						with open(os.path.join(submission,file), 'rb') as f:
							file_bytes = f.read()
							results.append([file.lower(), file_bytes])
			self._files = results

	@property
	def outputChartName(self):
		for row in self._files:
			if "song.ini" in row[0]:
				for line in row[1].decode('utf-8'):
					subd_line = re.sub("(?:<[^>]*>)", "", line)
					if line.startswith("name"):
						name = subd_line.split('=', 1)[1]
					if line.startswith("artist"):
						artist = subd_line.split('=', 1)[1]
					if line.startswith("charter"):
						charter = subd_line.split('=', 1)[1]
		newFile = f"{artist} - {name} ({charter})"
		newFile = newFile.replace("/",  u'\uFF0F') #／
		newFile = newFile.replace("\\", u'\u29F5') #⧵
		newFile = newFile.replace(":",  u'\uA789') #꞉
		newFile = newFile.replace("<",  u'\u276E') #❮
		newFile = newFile.replace(">",  u'\u276F') #❯
		newFile = newFile.replace("\"", u'\u0027') #'
		newFile = newFile.replace("?",  u'\uFF1F') #？
		newFile = newFile.replace("*",  u'\u204E') #⁎
		newFile = newFile.replace("|",  u'\u23D0') #⏐
		newFile = newFile.strip()

		encoding = 'utf-8'
		bytes_data = newFile.encode(encoding)
		sliced_bytes = bytes_data[:255]
		newFile = sliced_bytes.decode(encoding, errors='ignore')
		newFile = newFile.rstrip()

		return newFile

	@property
	def songini(self) -> bytes:
		for row in self._files:
			filename = row[0]
			if "song.ini" in filename:
				if self._sanitize:
					row[1] = re.sub(b"(?:<[^>]*>)", b"", row[1])
				return row[1]

	@property
	def chart(self) -> bytes:
		for row in self._files:
			filename = row[0]
			if "notes.chart" in filename or "notes.mid" in filename:
				return row[1]

	@property
	def is_chart_format(self) -> bool:
		for row in self._files:
			if "notes.chart" in row[0]:
				return True
		return False

	@property
	def md5(self) -> str:
		return hashlib.md5(self.chart).hexdigest()

	def parse_metadataPairArray(self, data: bytes) -> list[list[str, str]]:
		results = []
		byte_stream = io.BytesIO(data)
		while True:
			keyLen_bytes = byte_stream.read(4)
			if not keyLen_bytes:
				break
			keyLen = int.from_bytes(keyLen_bytes, byteorder='little')
			
			key_bytes = byte_stream.read(keyLen)
			key = key_bytes.decode('utf-8')
			
			valueLen_bytes = byte_stream.read(4)
			valueLen = int.from_bytes(valueLen_bytes, byteorder='little')
			
			value_bytes = byte_stream.read(valueLen)
			value = value_bytes.decode('utf-8')
			
			results.append([key, value])
		return results

	def parse_fileMetaArray(self, data: bytes) -> list[list[str, int, int]]:
		results = []
		byte_stream = io.BytesIO(data)
		while True:
			filenameLen_bytes = byte_stream.read(1)
			if not filenameLen_bytes:
				break
			filenameLen = int.from_bytes(filenameLen_bytes, byteorder='little')
			
			filename_bytes = byte_stream.read(filenameLen)
			filename = filename_bytes.decode('utf-8').casefold()
				
			contentsLen_bytes = byte_stream.read(8)
			contentsLen = int.from_bytes(contentsLen_bytes, byteorder='little')
			
			contentsIndex_bytes = byte_stream.read(8)
			contentsIndex = int.from_bytes(contentsIndex_bytes, byteorder='little')
			
			results.append([filename, contentsLen, contentsIndex])
		return results
			
	def xorMask(self, data: bytes, xor_mask: list[int]) -> bytes:
		data_arr = numpy.frombuffer(data, dtype=numpy.uint8)
		n = len(data_arr)
	
		full_cycle_len = 256
		key_cycle = numpy.array([(xor_mask[i % 16] ^ i) for i in range(full_cycle_len)], dtype=numpy.uint8)
	
		tiled_key = numpy.tile(key_cycle, (n // full_cycle_len) + 1)[:n]
		return (data_arr ^ tiled_key).tobytes()

	def get_sng_files(self, all_bytes: bytes) -> list[list[str, bytes]]:
		all_bytes_stream = io.BytesIO(all_bytes)
		all_bytes_stream.seek(10)
		
		xor_mask_bytes = all_bytes_stream.read(16)
		xorMask = list(xor_mask_bytes)

		metadataLen_bytes = all_bytes_stream.read(8)
		metadataLen = int.from_bytes(metadataLen_bytes, byteorder='little', signed=False)
		
		all_bytes_stream.seek(8,1)
		
		metadataPairArray_bytes = all_bytes_stream.read(metadataLen-8)
		metadataPairArray = self.parse_metadataPairArray(metadataPairArray_bytes)
		
		fileMetaLen_bytes = all_bytes_stream.read(8)
		fileMetaLen = int.from_bytes(fileMetaLen_bytes, byteorder='little', signed=False)

		all_bytes_stream.seek(8, 1)

		fileMetaArray_bytes = all_bytes_stream.read(fileMetaLen-8)
		fileMetaArray = self.parse_fileMetaArray(fileMetaArray_bytes)

		results = []
		with io.BytesIO() as songini_stream:
			songini_stream.write(bytes(f"[song]\n".encode('utf-8')))
			for row in metadataPairArray:
				line = f"{row[0]} = {row[1]}\n"
				songini_stream.write(line.encode('utf-8'))
			results.append(["song.ini", songini_stream.getvalue()])
			
		for row in fileMetaArray:
			all_bytes_stream.seek(row[2])
			results.append([row[0],self.xorMask(all_bytes_stream.read(row[1]),xorMask)])

		return results
	
	def build_sng(self) -> bytes:
		with io.BytesIO() as sng_stream:
			header ="SNGPKG"
			sng_stream.write(bytes(header.encode('utf-8')))
			version = 1
			sng_stream.write(version.to_bytes(4, byteorder="little"))
			xorMask = randbytes(16)
			sng_stream.write(xorMask)

			metadataPairArray = []
			for row in self._files:
				filename = row[0].lower()
				if "song.ini" in filename:
					songini_bytes = row[1]
			songini_text = songini_bytes.decode('utf-8').split('\n',1)[-1]
			for line in songini_text.strip().split('\n'):
				line = line.split('=',1)
				key = line[0].strip()
				value = line[1].strip()
				metadataPairArray.append([key,value])
			if "playlist" not in metadataPairArray[0] and self._playlist is not None:
				metadataPairArray.append(["playlist",self._playlist])
			with io.BytesIO() as songini_stream:
				for row in metadataPairArray:
					if "playlist" == row[0] and self._playlist is not None:
						key = bytes("playlist".encode('utf-8'))
						keyLen = len(key).to_bytes(4, byteorder="little",signed=True)
						value = bytes(self._playlist.encode('utf-8'))
						valueLen = len(value).to_bytes(4, byteorder='little',signed=True)
						songini_stream.write(keyLen)
						songini_stream.write(key)
						songini_stream.write(valueLen)
						songini_stream.write(value)	
						continue
					key = bytes(row[0].encode('utf-8'))
					keyLen = len(key).to_bytes(4, byteorder="little",signed=True)
					value = bytes(row[1].encode('utf-8'))
					valueLen = len(value).to_bytes(4, byteorder='little',signed=True)
					songini_stream.write(keyLen)
					songini_stream.write(key)
					songini_stream.write(valueLen)
					songini_stream.write(value)
				metadataLen = (8+songini_stream.getbuffer().nbytes).to_bytes(8, byteorder='little',signed=False)
				metadataCount = len(metadataPairArray).to_bytes(8, byteorder='little',signed=False)
				sng_stream.write(metadataLen)
				sng_stream.write(metadataCount)
				sng_stream.write(songini_stream.getvalue())
			
			fileCount = len(self._files)-1
			fileMetaLen = 8 + (17)*fileCount
			for row in self._files:
				if "song.ini" == row[0]:
					continue
				fileMetaLen += len(bytes(row[0].encode('utf-8')))
			sng_stream.write(fileMetaLen.to_bytes(8, byteorder='little', signed=False))
			sng_stream.write(fileCount.to_bytes(8, byteorder='little' ,signed=False))

			fileDataArray_index = sng_stream.getbuffer().nbytes + fileMetaLen
			fileDataArray_Array =[]
			with io.BytesIO() as fileMeta_stream:
				for row in self._files:
					if "song.ini" == row[0]:
						continue
					filename = bytes(row[0].lower().encode('utf-8'))
					filenameLen = len(filename).to_bytes(1, byteorder="little",signed=False)
					contentsLen = len(row[1]).to_bytes(8, byteorder='little',signed=False)
					contentsIndex = (fileDataArray_index).to_bytes(8, byteorder='little',signed=False)
					fileMeta_stream.write(filenameLen)
					fileMeta_stream.write(filename)
					fileMeta_stream.write(contentsLen)
					fileMeta_stream.write(contentsIndex)
					fileDataArray_Array.append([row[0], len(row[1]), fileDataArray_index])
					fileDataArray_index += len(row[1])
				sng_stream.write(fileMeta_stream.getvalue())
			
			fileDataLen = 0
			for row in fileDataArray_Array:
				fileDataLen += row[1]
			sng_stream.write((fileDataLen).to_bytes(8, byteorder='little',signed=False))

			for row in self._files:
				if "song.ini" == row[0].lower():
					continue
				sng_stream.write(bytes(self.xorMask(list(row[1]),xorMask)))

			return sng_stream.getvalue()

async def downloadChart(session: aiohttp.ClientSession, theChart: dict, chartFolder) -> Optional[str]:
	url = f"https://files.enchor.us/{theChart['md5']}{('_novideo','')[not theChart['hasVideoBackground']]}.sng"
	custom_timeout = aiohttp.ClientTimeout(sock_connect=10, total=300)
	try:
		resp = await session.get(url, timeout=custom_timeout)
		if resp.status != 200:
			print(f"Encore returned non-200 status code for chart: {resp.status}")
			return None
		theSng = await resp.content.read()
	except asyncio.TimeoutError:
		print(f"Timeout downloading chart {theChart['name']} {theChart['album']} {theChart['artist']} - {theChart['md5']}")
		return None
	except Exception as e:
		print(f"Error in reading sng chart content: {e}")
		return None
	try:
		final_chart_files = SNGHandler(submission=theSng)._files
	except Exception as e:
		print(f"Error converting SNG file: {e}", flush=True)
		return None
	outputFolder = outputChartDir(chartFolder, theChart)
	if platform.system() == "Windows":
		finalChartPath = f"{u'\\\\?\\'}{outputFolder['dir']}"
	else:
		finalChartPath = outputFolder["dir"]
	if not os.path.isdir(finalChartPath):
		os.makedirs(finalChartPath)
		for file in final_chart_files:
			with open(os.path.join(finalChartPath,file[0]),'wb') as f:
				f.write(file[1])		
	else:
		pass
	return finalChartPath

def getEncorePage(page: int, search: str, dflag: bool) -> dict:
	if dflag:
		d = { "search" : search, 'per_page' : 250, 'page' : page, 'instrument':'drums', 'drumsReviewed':False }
	else:
		d = { "search" : search, 'per_page' : 250, 'page' : page }

	resp = requests.post("https://api.enchor.us/search/", data = json.dumps(d), headers = {"Content-Type":"application/json"})
	retJson = resp.json()

	return retJson

def trimPageDuplicates(thePage) -> dict:
	for i, chart1 in enumerate(thePage):
		for j, chart2 in enumerate(thePage):
			if chart1['ordering'] == chart2['ordering'] and i != j:
				del thePage[j]
	return thePage

def outputChartDir(chartFolder, theChart: str) -> dict:
	newFile = f"{theChart['artist']} - {theChart['name']} ({theChart['charter']})"
	newFile = newFile.replace("/",  u'\uFF0F') #／
	newFile = newFile.replace("\\", u'\u29F5') #⧵
	newFile = newFile.replace(":",  u'\uA789') #꞉
	newFile = newFile.replace("<",  u'\u276E') #❮
	newFile = newFile.replace(">",  u'\u276F') #❯
	newFile = newFile.replace("\"", u'\u0027') #'
	newFile = newFile.replace("?",  u'\uFF1F') #？
	newFile = newFile.replace("*",  u'\u204E') #⁎
	newFile = newFile.replace("|",  u'\u23D0') #⏐
	newFile = newFile.strip()

	encoding = 'utf-8'
	bytes_data = newFile.encode(encoding)
	sliced_bytes = bytes_data[:255]
	newFile = sliced_bytes.decode(encoding, errors='ignore')
	newFile = newFile.rstrip()
	outputDir = os.path.join(chartFolder, newFile)
	
	return { "dir" : outputDir, "file" : newFile }

def oldOutputChartDir(chartFolder, theChart: str) -> dict:
	MAX_FILE_LEN = os.pathconf('.', 'PC_NAME_MAX') if platform.system() != "Windows" else 255
	newFile = f"{theChart['artist']} - {theChart['name']} ({theChart['charter']})"
	newFile = newFile.replace("/",  "")
	newFile = newFile.replace("\\", "")
	newFile = newFile.replace(":",  "")
	newFile = newFile.replace("<",  "")
	newFile = newFile.replace(">",  "")
	newFile = newFile.replace("\"", "")
	newFile = newFile.replace("?",  "")
	newFile = newFile.replace("*",  "")
	newFile = newFile.replace("|",  "")
	newFile = newFile.strip()

	if platform.system() == 'Windows':
		newFile = newFile[:MAX_FILE_LEN]
		newFile = newFile.rstrip()
		outputDir = f"{chartFolder}\\{newFile}"
	else:
		newFile = newFile[:MAX_FILE_LEN - 4] #-4 for .sng
		outputDir = f'{chartFolder}/{newFile}'
	
	return { "dir" : outputDir, "file" : newFile }

async def doChartDownload(theChart, args, sema, session, chartNum, numCharts):
	async with sema:
		print(f"Starting download/conversion of chart {theChart['name']} - {theChart['album']} - {theChart['artist']} - {theChart['charter']} - {theChart['md5']}", flush=True)
		finalChartFolder = await downloadChart(session, theChart, args.clone_hero_folder)
		if not finalChartFolder:
			print(f"Error downloading chart {theChart['name']} - {theChart['album']} - {theChart['artist']} - {theChart['md5']}",flush=True)
			if args.stop_on_error:
				print("Encountered error, and continue error not set, quitting.",flush=True)
				sys.exit(1)
			else:
				return

		if args.remove_playlist:
			chartDir = outputChartDir(args.clone_hero_folder, theChart)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{outputChartDir(args.clone_hero_folder, theChart)['dir']}"
			if os.path.isfile(os.path.join(chartDir, "song.ini")):
				await removePlaylist(chartDir)

async def removePlaylist(chartDir):
	fileName = os.path.join(chartDir, "song.ini")
	with open(fileName, encoding='utf-8', mode="r") as file:
		lines = file.readlines()
	with open(fileName, encoding='utf-8', mode='w') as file:
		for line in lines:
			lineTest = line.replace(" ","").strip("\n")
			if "playlist_track=" not in lineTest and "playlist=" not in lineTest:
				file.write(line)

async def schemaRename(chFolder, theChart):
	if platform.system != "Windows":
		oldDir = oldOutputChartDir(chFolder, theChart)['dir']
		newDir = outputChartDir(chFolder, theChart)['dir']
	else:
		oldDir = f"{u'\\\\?\\'}{oldOutputChartDir(chFolder, theChart)['dir']}"
		newDir = f"{u'\\\\?\\'}{outputChartDir(chFolder, theChart)['dir']}"
	if os.path.isdir(oldDir) and oldDir != newDir:
		print(f'Renaming improperly named chart folder: {oldDir}', flush=True)
		shutil.move(oldDir,newDir)

def script_path(relative_path):
	if getattr(sys, 'frozen', False):
		base_path = os.path.dirname(sys.executable)
	else:
		base_path = os.path.dirname(os.path.abspath(__file__))
		
	return os.path.join(base_path, relative_path)

@Gooey(
	program_name="Encore Chart Downloader", 
	default_size=(800, 600),
	header_bg_color="#D3D3D3",
	footer_bg_color="#D3D3D3",
	body_bg_color="#FFFFFF",
	navigation_bg_color="#D3D3D3",
	show_stop_warning=True,
	progress_regex=r"^Progress (?P<current>\d+) of (?P<total>\d+)$",
	progress_expr="current / total * 100",
	timing_options = {
		'show_time_remaining':True,
		'hide_time_remaining_on_complete':True
	},
	hide_progress_msg=False
)
def main():
	argParser = GooeyParser(description="Download every chart from Chorus Encore. Saves chart folders using Bridge\'s default naming format")
	req_group = argParser.add_argument_group("Required Arguments")
	opt_group = argParser.add_argument_group("Optional Arguments")
	debug_group = argParser.add_argument_group("Debug Arguments")
	opt_group.add_argument("-t", "--threads", help="Maximum number of threads to allow", default=4, widget="IntegerField", gooey_options={'min':1,'max':16})
	debug_group.add_argument("-s", "--search", help="Search to filter Encore results", default="", type=str,widget="TextField")
	debug_group.add_argument("-p", "--page", help="Encore download page to start on", default=1, type=int, widget="IntegerField", gooey_options={'min':1,'max':500})
	opt_group.add_argument("-td", "--temp-directory", help="Temporary directory to use for chart downloads before conversion", default=f"{script_path('scratch')}", widget="DirChooser")
	debug_group.add_argument("-soe", "--stop-on-error", help=" Continue on error during conversion or download", widget="CheckBox", action='store_true')
	req_group.add_argument("-chf", "--clone-hero-folder", help="Clone Hero songs folder to output charts to", widget="DirChooser", required=True)
	opt_group.add_argument("-rp", "--remove-playlist", help=" Remove playlist data for previously downloaded and to be downloaded charts", widget="CheckBox", action='store_true')
	opt_group.add_argument("-d", "--charts-with-drums", help=" Only downloads charts containing drum parts", widget="CheckBox", action='store_true')
	opt_group.add_argument("-sc", "--schema-cleanup", help="Only run this option if you have previously downloaded charts with an old verison of this script. Additionally, this option only needs to be run once. If you have completed a run with this flag, you do not need to run it again.", widget="BlockCheckbox", action='store_true', gooey_options={'checkbox_label':'Renames old folders to match Bridge\'s default naming format'})
	args = argParser.parse_args()

	import codecs

	if sys.stdout.encoding != 'UTF-8':
		sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
	if sys.stderr.encoding != 'UTF-8':
		sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

	if not os.path.isdir(args.clone_hero_folder):
		print("Clone Hero folder does not exist! Please provide a valid, existing path with -chf (--clone-hero-folder)", flush=True)
		sys.exit(1)

	print(f"Outputting charts to folder {args.clone_hero_folder}", flush=True)
	print(f"Using temp folder {args.temp_directory} for chart downloads", flush=True)
	print(f"Using {args.threads} threads", flush=True)
	if not args.page > 0:
		print("Page argument must be >0!", flush=True)
		sys.exit(1)
	if args.stop_on_error:
		print("Will stop download/convert of charts on error", flush=True)
	if args.remove_playlist:
		print("Removing playlist data for charts (downloaded+to-download)", flush=True)
	if args.schema_cleanup:
		print("Renaming old chart folders to new naming schema", flush=True)

	async def async_main():
		sema = asyncio.Semaphore(int(args.threads))
		page = args.page
		page_resp = await asyncio.to_thread(getEncorePage, page, args.search, args.charts_with_drums)
		numCharts = page_resp['found']
		print(f'Found {numCharts} charts', flush=True)
		pageData = trimPageDuplicates(page_resp['data'])

		async with aiohttp.ClientSession() as session:
			while len(pageData) > 0:
				tasks = []
				for i, chart in enumerate(pageData):
					chartNum = ((page - 1) * 250) + (i + 1)
					if chartNum % 500 == 0:
						print(f"Progress {chartNum} of {numCharts}", flush=True)
					if args.schema_cleanup:
						tasks.append(asyncio.create_task(schemaRename(args.clone_hero_folder, chart)))
					oldChartDir = oldOutputChartDir(args.clone_hero_folder, chart)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{oldOutputChartDir(args.clone_hero_folder, chart)['dir']}"
					chartDir = outputChartDir(args.clone_hero_folder, chart)['dir'] if platform.system() != 'Windows' else f"{u'\\\\?\\'}{outputChartDir(args.clone_hero_folder, chart)['dir']}"
					if os.path.isdir(chartDir) or os.path.isdir(oldChartDir):
						if args.remove_playlist and os.path.isfile(os.path.join(chartDir, "song.ini")):
							tasks.append(asyncio.create_task(removePlaylist(chartDir)))
						elif args.remove_playlist and os.path.isfile(os.path.join(oldChartDir, "song.ini")):
							tasks.append(asyncio.create_task(removePlaylist(oldChartDir)))
						continue

					tasks.append(asyncio.create_task(doChartDownload(chart, args, sema, session, chartNum, numCharts)))

				if tasks:
					await asyncio.gather(*tasks)

				page += 1
				page_resp = await asyncio.to_thread(getEncorePage, page, args.search, args.charts_with_drums)
				pageData = trimPageDuplicates(page_resp['data'])

	asyncio.run(async_main())

	scratch_leftovers = os.listdir(args.temp_directory)
	for item in scratch_leftovers:
		shutil.rmtree(os.path.join(args.temp_directory,item))
	print("Script completed! All charts charts have been downloaded", flush=True)
	sys.exit(0)

if __name__ == '__main__':
	main()

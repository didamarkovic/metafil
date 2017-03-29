#!python
""" metafil.py

	Dida Markovic, 29/03/2017

	Collection of old filenaming functions and other dinky meta tools.
	Many are from forumns etc (links in comments).
"""
import inspect, glob, time, subprocess, os.path, unicodedata

""" ---------------------- DEBUGGING TOOLS ----------------------- """

def lineno(string=''):
	# Returns the current line number in our program. How come not always the line in this file??
	if string is not '':
		return "L." + str(inspect.currentframe().f_back.f_lineno) + ': ' + str(string)
	else:
		return "L." + str(inspect.currentframe().f_back.f_lineno)
# http://code.activestate.com/recipes/145297-grabbing-the-current-line-number-easily/

""" ------------------- END OF DEBUGGING TOOLS ------------------- """

""" ---------------------- FILENAME TOOLS ------------------------ """

def ts(t=(2015,3,1,0,0,0,0,0,0)):
	return str(int(time.time() - time.mktime(t)))

def validate_filename(filepath):
	""" Raises an Exception if the file does not exist.

		Parameters
		----------
		filepath : str
			input filename

		Returns
		-------
		filepath : str
			validated, absolute path to the file
	"""
	if not os.path.isfile(filepath):
		raise Exception('File not found: ' + filepath)
	return os.path.abspath(filepath)


def increment_filename(filepath, fileout=None):
       """ Adds the word 'increment' to filename if such a file doesn't exist.
               If it does, it adds increment.v#, where # is the number that 
               creates a filename that doesn't exist yet.

       Parameters
       ----------
       filepath : str
               path to file whose name is to be incremented

       Returns
       -------
       filepath : str
               new path not associated with a existing file
       """
       
       # Assign the first desired filename
       if fileout is None:
               filepath = '.'.join(filepath.split('.')[:-1]) + '.increment.hdf5'
       else:
               filepath = fileout

       # If it already exists, increment it
       n=1
       while op.exists(filepath):
               n+=1
               if n==2: 
                       filepath = '.'.join(filepath.split('.')[:-1]) + '.v' + str(n) + '.hdf5'
                       continue
               filepath = '.'.join(filepath.split('.')[:-2]) + '.v' + str(n) + '.hdf5'

       # Return the absolute path so there are no relative path problems later
       return op.abspath(filepath)

def file_list(inpath):
	""" Returns a list of strings that are valid paths in the system.

	Parameters
	----------
	inpath : str or list 
		string path or a list of them, can be either a single file, 
	    single folder or a list of files or folders

	Returns
	-------
	file_list : list
		a list of strings, each is a valid path to a file in the system
	"""
	file_list = []
	for ip in ensurelist(inpath):
		if os.path.isfile(ip):
			file_list.append(ip)
		elif os.path.isdir(ip):
			file_list.extend(glob.glob(ip+'/*'))
	return file_list

def strdiff(filenames, spliton='_'):
	""" This finds the part of all the strings that differs between
		the strings. It may take long if have a lot of strings, but I am not sure.
		The problem here is that order is not retained well... Annoying. 
		Note also that if you have the the string that is unique to each filename
		also appearing in the path, you need to run securediff on the result.
		Finally, note that this doesn't work if many parts of the filename are varying
		if they are separated by _, . or -! """

	if len(filenames)==0:
		raise Exception("There are no files in the input to diff!")

	thingstospliton = ['_', '.', '-']
	
	# Stop if last separator in list
	try:
		new_spliton = thingstospliton[thingstospliton.index(spliton)+1]
	except IndexError:
		new_spliton = ''

	# Make a dictionary of sets of substrings with full filenames as keys
	namelist = {}
	for filename in filenames:
		namelist[filename] = filename.split('/')[-1].split(spliton)

	# Find intersections of all the other sets with the first, keep common strings
	for filename in filenames:
		if filename is filenames[0]: 
			saveset = namelist[filename]
			continue 
		saveset = list( set(saveset) & set(namelist[filename]) )

	# Remove common substrings and re-merge sets to strings
	for filename in filenames:
		namelist[filename] = new_spliton.join( set(namelist[filename]) - set(saveset) )

	# Nest this function - try to split it on '.' and '-' as well
	if new_spliton != '': 
		tmp = strdiff(namelist.values(), spliton=new_spliton)
		# Populate the dictionary to return
		for filename in filenames:
			namelist[filename] = tmp[namelist[filename]]

	return namelist

def securediff(fdict):
	""" This adds some security padding around the unique part of a string to make it less
		likely that there will be repetitions of it in the string. E.g. if it's just a 0,
		and have numbers in the path too. 
		Note that there should be only 1 unique string and up to 2 common strings
		surrounding it!"""

	if len(fdict)==0:
		raise Exception("There are no files in the input to diff!")

	common = None
	problematic = []
	for fname, uniqstr in fdict.items():

		# Find the string in common
		if fname.count(uniqstr) == 1:
			fparts = fname.split(uniqstr)
			
			# Check that the common string is the same in all the filenames
			if common is not None:
				for string in common:
					if string not in fparts:
						raise Exception('Something has gone terribly wrong!')
			common = fparts

		# List the files where the characteristic string repeats in the path
		elif fname.count(uniqstr) > 1:
			problematic.append(fname)

		# Check that it does appear in the path
		elif fname.count(uniqstr) == 0:
			print fname, uniqstr
			raise Exception('Something has gone terribly wrong!')

	# Check that common string found is also present in the problematic filenames
	for problem in problematic:
		for string in common:
			if string not in problem:
				raise Exception('Something has gone terribly wrong!')

	# Assuming unique string is in the middle of two (possibly empty) common
	# 	strings, pad the unique string so that it always appears only once.
	if len(problematic) > 0:
		
		for fname, uniqstr in fdict.items():

			if len(common[0]) > 0:
				new_uniqstr = common[0][-1] + uniqstr
			if len(common[1]) > 0:
				new_uniqstr += common[1][0]

			fdict[fname] = new_uniqstr

		fdict = securediff(fdict)

	return fdict

def fnamediff(pathpattern, padding=''):
	""" This finds the part of all the filenames that differs between
		the files. It may take long if have a lot of files, but I am not sure."""

	# this is complete non-sense:
	if '*' not in pathpattern: 
		if pathpattern[-1] != '/': pathpattern += '/'
		pathpattern += '*'
	
	#if len([pathpattern.start() for m in re.finditer('*', pathpattern)])>1: 
	#	raise TooSpecificErr()

	splitname = pathpattern.split('*')

	prefix = splitname[0]
	lenpre = len(prefix)

	if len(splitname) > 1:
		suffix = splitname[-1]
	else:
		suffix = ''
	lensu = len(suffix) 

	filenames = glob.glob(pathpattern)
	nfiles = len(filenames)

	refname = filenames[0]

	midtix = refname.replace(prefix,'').replace(suffix,'')
	# Prefix
	for letter in midtix:
		new_filenames = glob.glob(prefix + letter + '*' + suffix)
		if len(new_filenames) == nfiles: prefix = prefix + letter

	# Suffix
	for letter in midtix[::-1]:
		new_filenames = glob.glob(prefix + '*' + letter + suffix)
		if len(new_filenames) == nfiles: suffix = letter + suffix

	i=0
	names = {}
	for filename in filenames:
		names[filename] = padding+filename.replace(prefix,'').replace(suffix,'')
		i+=1

	return names

""" ------------------- END OF FILENAME TOOLS -------------------- """

""" ------------------------- GIT TOOLS -------------------------- """

# A class that contains the Git environment at the time of it's initialisation.
# Currently it uses the subprocess module to speak to Git through the system.
# Ideally some day it would use the GitPython module or Dulwich or something like it.
class GitEnv(object):

	# Some day could pass the directory containing the .git/ folder as a possible input to __init__.
	# Could find this by searching for it in each parent directory and keep cd .. -ing until you find it.
	def __init__(self, home='.'):
		self.git_dir = os.path.join(home, '.git')
		self.hash, self.author, self.date = [str(s) for s in self.get_commit()]
		self.url = str(self.get_remote()).split('@')[-1]
		self.branch = str(self.get_branch())
		self.repo = str(self.get_repo())
		self.printstart = ''
	# Also, should have an if that gives out the name of the parent folder + the
	# date and time in the case that it is NOT A GIT REPO!

	def __str__(self):
		startline = self.printstart
		as_string = startline + "This was generated by code from the Git repo at:"
		as_string += "\n" + startline + "\t " + self.url + ","
		as_string += "\n" + startline + "\t on the " + self.branch + " branch,"
		as_string += "\n" + startline + "\t with commit: " + self.hash
		as_string += "\n" + startline + "\t\t from " + self.date + ", "
		as_string += "\n" + startline + "\t\t by " + self.author + "."
		return unicodedata.normalize('NFKC', as_string.decode("unicode-escape")).encode('ascii', 'ignore')

	def set_print(self, startline):
		self.printstart = startline

	def get_git_cmd(self, args=[]):
		cmd = ['git']
		if self.git_dir != None:
			cmd.append('--git-dir')
			cmd.append(self.git_dir)
		for one in args:
			cmd.append(one)

		return cmd

	def get_hash(self, nochar=7, sep=''):
		return sep+self.hash[0:nochar]+sep

	# Get the hash, author and date of the most recent commit of the current repo.
	def get_commit(self):
		cmd = subprocess.Popen(self.get_git_cmd(['log', '-n','1']), stdout=subprocess.PIPE)
		cmd_out, cmd_err = cmd.communicate()
		newlist=[]
		for entry in cmd_out.strip().split('\n'):
			if entry=='': continue
			entry = entry.split(' ')
			# This is a hack, should use a dict so can be sure what we are reading in:
			if 'commit' in entry[0] or 'Author' in entry[0] or 'Date' in entry[0]:
				newlist.append(' '.join(entry[1:]).strip())
		if len(newlist)!=3: raise Exception('No commit found.')
		return newlist

	# At the moment this only gives the first url in what git returns.
	# Eventually it'd be nice if you could get the origin url, the fetch...
	def get_remote(self):
		cmd = subprocess.Popen(self.get_git_cmd(['remote', '-v']), stdout=subprocess.PIPE)
		cmd_out, cmd_err = cmd.communicate()
		if bool(cmd_out):
			try:
				return cmd_out.strip().split('https://')[1].split(' ')[0]
			except IndexError:
				ssh_url = cmd_out.strip().split('git@')[1].split(' ')[0]
				return ssh_url.replace(':','/')
		else:
			return None

	def get_branch(self):
		cmd = subprocess.Popen(self.get_git_cmd(['branch']), stdout=subprocess.PIPE)
		cmd_out, cmd_err = cmd.communicate()
		branches = cmd_out.strip().splitlines()
		for branch in branches:
			if '*' in branch:
				return branch.replace('*','').strip()

	def get_repo(self):
		cmd = subprocess.Popen(self.get_git_cmd(['rev-parse','--show-toplevel']), stdout=subprocess.PIPE)
		cmd_out, cmd_err = cmd.communicate()
		return cmd_out.strip().split('/')[-1]

""" ---------------------- END OF GIT TOOLS ---------------------- """

#!python
""" metafil.py

	Dida Markovic, 29/03/2017

	Collection of old filenaming functions and other dinky meta tools.
	Many are from forumns etc (links in comments).
"""
import inspect, glob, time, subprocess, os, os.path, unicodedata, pkg_resources, git

""" ---------------------- DEBUGGING TOOLS ----------------------- """

def lineno(string=''):
	# Returns the current line number in our program. How come not always the line in this file??
	if string != '':
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

def new_suffix(filename,suffix):
    """ If fileout exists in the file system it adds [...].v#, where # is the number that 
           creates a filename that doesn't exist yet.

    Parameters
    ----------
    filename  : str
            input filename (can be with path) with undesired suffix (defined as after last dot!)
    suffix  : str
    		new suffix (dot separator added automatically, so don't include here!)

    Returns
    -------
    filename : str
        filename with new suffix
    """

    # Read the suffix, which is assumed to be a string after the last dot
    return '.'.join(filename.split('.')[:-1] + [suffix])

def increment_filename(fileout):
    """ If fileout exists in the file system it adds [...].v#, where # is the number that 
           creates a filename that doesn't exist yet.

    Parameters
    ----------
    fileout  : str
            full desired pathname (will be incremented if exists)

    Returns
    -------
    filepath : str
        new path not associated with a existing file
    """
        
    # Read the suffix, which is assumed to be a string after the last dot
    suffix = '.' + fileout.split('.')[-1]

    # If it already exists, increment it
    n=1
    while os.path.exists(fileout):
        n+=1
        if n==2: 
            fileout = '.'.join(fileout.split('.')[:-1]) + '.v' + str(n) + suffix
            continue
        fileout = '.'.join(fileout.split('.')[:-2]) + '.v' + str(n) + suffix

    # Return the absolute path so there are no relative path problems later
    return os.path.abspath(fileout)
    
def _ensurelist(supposed_list):
	if isinstance(supposed_list,list):
		return supposed_list
	else:
		return [supposed_list]

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
	for ip in _ensurelist(inpath):
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
		tmp = strdiff(list(namelist.values()), spliton=new_spliton)
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
	for fname, uniqstr in list(fdict.items()):

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
			print(fname, uniqstr)
			raise Exception('Something has gone terribly wrong!')

	# Check that common string found is also present in the problematic filenames
	for problem in problematic:
		for string in common:
			if string not in problem:
				raise Exception('Something has gone terribly wrong!')

	# Assuming unique string is in the middle of two (possibly empty) common
	# 	strings, pad the unique string so that it always appears only once.
	if len(problematic) > 0:
		
		for fname, uniqstr in list(fdict.items()):

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

def searchup(path, filename, maxstep=3):
	""" Recursively searches up the path until it finds filename. 
		Traverses max maxstep levels. 
	"""	
	if maxstep<0: raise IOError('Path not found!')
	path = os.path.abspath(path)
	full_filename = os.path.join(path,filename)
	if os.path.exists(full_filename):
		return full_filename
	else:
		return searchup(path+'/..', filename, maxstep-1)

def gitstamp(home=inspect.stack()[-1].filename, linestart = ''):
	""" Returns a string that describes the git repo of the input path. Default value uses the
	 	path of the script that is calling this function.
		If the caller is not in a git repo, it returns some basic info about the 
		location on disk. 

		Example: `print(metafil.gitstamp())` to create the stamp for the current script.

		home : str - path to repo to create the stamp (default: caller function's directory)
		linestart : str - prepend this to each line of the string, e.g. # (default: '')
	""" 

	# Make sure it's a directory
	home = os.path.realpath(os.path.abspath(home)).split()[0]

	# Check if there is a git repo in the folder of home or above
	try:
		home = searchup(home, '.git')
	except IOError:
		isrepo = False
	else:
		isrepo = True

	# Call GitPython functions and collect the needed info
	if isrepo:
		repo = git.Repo(home)
		url = repo.remote().url
		branch = str(repo.active_branch)
		hash = str(repo.commit())
		author = str(repo.commit().author) + ' <' + str(repo.commit().author.email) + '>'
		date = repo.commit().authored_datetime.strftime("%A, %H:%M:%S %z UTC, %d %b %Y")
		#name = os.path.basename(home).split('.')[0]

	# Now construct the string stamp
	as_string = linestart + "This was generated at " + time.strftime('%H:%M:%S %z UTC, %d %b %Y')
	as_string += "\n" + linestart + "\t by code from"
	if isrepo: 
		as_string += " the Git repo:"
		as_string += "\n" + linestart + "\t\t" + url + ","
		as_string += "\n" + linestart + "\t on the " + branch + " branch,"
		as_string += "\n" + linestart + "\t with commit: " + hash[:10]
		if repo.is_dirty(): as_string += "-dirty"
		as_string += "\n" + linestart + "\t\t from " + date + ", "
		as_string += "\n" + linestart + "\t\t by " + author
	else:
		as_string += " the local folder (no Git repo found):"
		as_string += "\n" + linestart + "\t\t" + os.path.abspath(home) + ","	
		as_string += "\n" + linestart + "\t by " + os.getenv('USER')
	as_string += "."
	
	return unicodedata.normalize('NFKC', as_string)

# For backward compatibility only - to be removed (use function above):
class GitEnv(object):

	def __init__(self, home=inspect.stack()[-1].filename):
		self.home = home
		self.linestart=''
		
	def __str__(self):
		return gitstamp(home=inspect.stack()[-1].filename,linestart=self.linestart)

	def set_print(self, startline):
		self.linestart = startline

def get_version(name=None):
	# Returns the version of an imported module
	if name is None:
		return None
	else:
		try:
			return pkg_resources.require(name)[0].version
		except pkg_resources.DistributionNotFound:
			raise ImportError("A '" + name +\
				"' distribution was not found, but installation is required to access its version.")

""" ---------------------- END OF GIT TOOLS ---------------------- """

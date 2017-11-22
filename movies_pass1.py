#!/usr/bin/python
from os import listdir, rename
from os.path import isfile, join, basename, splitext
import string
import movie_metadata as mmd
import tmdbsimple as tmdb
tmdb.API_KEY = ''

def represents_int(string):
    try: 
        int(string)
        return True
    except ValueError:
        return False

''' Return True if file is a valid video container type extension.
'''
def is_movie_type(name):
	video_extensions = ['mp4', 'mpeg', 'mpg', 'mpeg4', 'avi', 'mkv', 'vob']
	extn = name.split(".")[-1].lower()
	return extn in video_extensions

''' Remove extraneous terms that might compromise the effectiveness of
	TMDB's fuzzy movie search functionality.
'''
def sanitise_filename_for_tmdb(name):
	bad_terms = ['yify', 'x264', 'bluray', 'dvdrip', 'xvid', 'ac3-myself', 'ac3', 'axxo', 'shanig', '1080p', '720p', 'hdts', 'hdtc', 'ts']
	
	# Remove file extension and all non-alphanumeric characters.
	name = splitext(name)[0]
	name = name.translate({ord(c): ' ' for c in string.punctuation})
	
	# Break up words/numbers in title.
	tokens = name.split(" ")
	new_tokens = []
	
	# Remove year (if present)
	for t in tokens:
		if represents_int(t) and int(t) > 1990 and int(t) < 2017:
			continue
		else:
			new_tokens.append(t)
	
	# Remove anything in bad_terms.
	tokens_filtered = [token for token in new_tokens if token.lower() not in bad_terms]
	name = ' '.join(tokens_filtered)
	
	return name

''' Parse a directory tree of form:
 ./movie1\ with\ a_funny-name.xVid.avi
 ./movie2/movie_in_a_folder.mp4
 ./movie2/subtitles_with_unrelated.name.srt
 ./movie3.mkv
 ...
    and return a list of dictionaries of the form:
  {'name': 'Movie 1', 'path': '/path/to/dir/movie1\ with\ a_funny-name.xVid.avi', 'directory': '/path/to/dir/'}
    for each movie under the root of the tree.
'''
def movies_full_paths(directory):
	movie_candidates = []
	for item in listdir(directory):
		if isfile(item) :
			if is_movie_type(item):
				movie_candidates.append(join(directory, item))
		else:
			for sitem in listdir(item):
				if isfile(sitem) and is_movie_type(sitem):
					movie_candidates.append(join(join(directory, item), sitem))
	return movie_candidates

''' Return the movie title that TMDB *thinks* matches the filename. None if no match.
'''
def find_moviedb_title(filename):
	search = tmdb.Search()
	search_string = sanitise_filename_for_tmdb(filename)
	response = search.movie(query=search_string)
	if len(search.results) == 0:
		return None
	else:
		return search.results[0]['title']

def get_tmdb_year(title):
	search = tmdb.Search()
	response = search.movie(query=title)
	if len(search.results) == 0:
		return None
	else:
		return search.results[0]['release_date'].split("-")[0]

		
''' Returns True if v1 > v2 with respect to video quality.
'''
def compare_video_quality(v1, v2):
	metric1 = mmd.videoQualityMetric(v1)
	metric2 = mmd.videoQualityMetric(v2)
	return metric1 > metric2
	
''' Builds and returns a dictionary mapping "real" (TMDB) movie titles
	against candidate filenames.
'''
def build_movie_dict(candidates):
	mdict = {}
	nomatch = []
	for candidate in candidates:
		title = find_moviedb_title(basename(candidate))
		if title is not None:
			if title not in mdict.keys():
				mdict[title] = [candidate]
			else:
				mdict[title].append(candidate)
		else:
			nomatch.append(candidate)
	return mdict
	
''' Return a modified dictionary with only the highest quality video files corresponding
    to each TMDB movie title entry.
'''
def deduplicate_movie_dict(mdict):
	new_dict = {}
	for movie, files in mdict.items():
		best_quality = files[0]
		for f in files:
			if compare_video_quality(f, best_quality):
				best_quality = f
		new_dict[movie] = best_quality
	return new_dict
	
''' Given a dict of 1-1 TMDB title-to-filename mappings,
	bulk-rename all movies to their correct titles and years,
	and place under dest_dir.
'''
def rename_and_move(mdict, dest_dir):
	for title, current_filename in mdict.items():
		file_extn = splitext(current_filename)[1]
		try:
			rename(current_filename, join(dest_dir, '%s [%s]%s' % (title, get_tmdb_year(title), file_extn)))
		except:
			print("Warning: Failed to copy file: " + current_filename)

if __name__ == "__main__":
	for mc in movies_full_paths('.'):
		print ("* %s" % mc)

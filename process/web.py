#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Read in:
    wav filenames from the input directory
    ELAN export files

Extract:
    sourcefile and timing information from the filenname
    English and Purepecha annotations from the ELAN export file

Write out tab-separated:
    word clip metadata spreadsheet values
    vocabularly spreadsheet values

Create:
    new copy of wav file named with English gloss

For example, inputs are:

    PR0020_105440_107180.wav, etc.
    rh1.txt, etc.

rh1.txt contains the information that there is an annotation in the range
105440 - 107180 with the value "kwiʃaˈti" for Purepecha and "sleeping" for
English. Filename is PR0020, start 105440, end 107180.

Clip gets metadata written out as:

    sleeping.wav    PR0020  1:45    1:47

Vocab metadata written out as:

    Purepecha       English     Source
    kwiʃaˈti        sleeping    PR0020_105440_107180

New copy of wav clip to be copied to fileshare is created under the name:

    sleeping.wav
"""
__author__ = 'rhorton is a student at ucsd dawt edu'

import os, random, sys
import wave
from formats import utfcsv # local module
from csv import excel_tab
from xml.etree import ElementTree as etree

## EDIT HERE TO MATCH YOUR ENVIRONMENT
#working_dir = "/Users/lucien/Data/Gitonga/my clips/"
#export_file = working_dir+'new.csv' # ELAN export file
#meta_file = working_dir+'new/GTExport.txt' # From Google doc
#eaf_dir = working_dir+'new' #  EAF input
#wav_dir = working_dir+'WAV' # WAV input
#clip_dir = working_dir+'comm/clips' # wav clip output
#meta_dir = working_dir+'comm' # csv data output

## EDIT HERE TO MATCH YOUR ENVIRONMENT
working_dir = "/Users/lucien/Data/Raramuri/"
export_file = working_dir+'ELAN Corpus/rar-new.csv' # ELAN export file
meta_file = working_dir+'ELAN Corpus/metadata_raramuri_2011.csv' # From Google doc
eaf_dir = working_dir+'ELAN Corpus/new' #  EAF input
wav_dir = working_dir+'WAV' # WAV input
clip_dir = '/Users/lucien/Data/Corpus-o-matic/Raramuri/comm/clips' # wav clip output
meta_dir = '/Users/lucien/Data/Corpus-o-matic/Raramuri/comm' # csv data output

# EDIT HERE TO MATCH YOUR ENVIRONMENT
#working_dir = "/Users/lucien/Data/Mixtec/"
#export_file = working_dir+'Transcriptions/min_feb14.csv' # ELAN export file
#meta_file = working_dir+'MixtecoMetadata.csv' # From Google doc
#eaf_dir = working_dir+'Transcriptions/new/' #  EAF input
#wav_dir = working_dir+'WAV' # WAV input
#clip_dir = '/Users/lucien/Data/Corpus-o-matic/Mixtec/comm/clips' # wav clip output
#meta_dir = '/Users/lucien/Data/Corpus-o-matic/Mixtec/comm' # csv data output

comment_field = "Annotation (other)" # necessary only if used for speaker annotation
wrapper = "../web/index_wrapper.html"

def main():
    """Perform the metadata extraction and file renaming."""

    # Parse the ELAN export, get the IPA, English and Spanish timestamps
    # fields = ["IPA","English","Spanish"] # for Purepecha?
    # fields = [] # will collect all fields, assuming the first one is primary phonetic
    # tiers, fields = parse_export_file(export_file, fields) 
    tiers, fields = parse_export_file(export_file)
    print "Export file parsed."

    # Find time ranges for which there is an IPA annotation and either an
    # English or Spanish annotation
    clippables = find_clippable_segments(tiers, fields)
    print "Clippables found."

    # Keep track of which clips we've already clipped, so that we don't
    # clip the same one twice
    already_clipped = set()

    # Output for clip metadata
    clip_fh = utfcsv.UnicodeWriter(open(meta_dir + '/clip_metadata.csv', 'w'))
    table_fh = open(meta_dir + '/clip_metadata.html', 'w')
    table_fh.write('<table id="clip_metadata">\n<thead>\n<tr>\n' +
                   '\n'.join(['<th>'+f+'&nbsp;</th>' for f in fields]) +
                   '\n' +
                   '<th>Speaker&nbsp;</th>\n' +
                   '<th>Citation&nbsp;</th>\n'
                   '<th>Length&nbsp;</th>\n' +
                   '<th class="Hide">Start&nbsp;</th>\n' +
                   '<th class="Hide">Stop&nbsp;</th>\n' +
                   '<th class="Hide">WAV&nbsp;</th>\n' +
                   '<th class="Hide">EAF&nbsp;</th>\n' +   
                   '<th class="Hide">File&nbsp;</th>\n' +
                   '<th class="Hide">Token&nbsp;</th>\n' +
                   '</tr>\n</thead>\n<tbody>\n')
    
    # Look in each EAF to see which wav file it references
    eaf_wav_files = {}
    for eaf_file, start, stop in clippables:
        if eaf_file not in eaf_wav_files:
            wav_file = find_wav_file(eaf_dir + '/'  + eaf_file)
            eaf_wav_files[eaf_file] = wav_file

    spkr_dict = get_speakers(meta_file)
    
    # If there are multiple eafs that define the same clipping regions for 
    # the same wav file, we want to use the EAF that is in the EAF metadata.
    #clippables = filter_clippables(clippables, eaf_wav_files, eaf_creators)

    tokens = {}
    for ckey in clippables:
        gkey = ":".join([tiers[f].get(ckey,'') for f in fields])
        if gkey in tokens:
            tokens[ckey] = tokens[gkey]+"-2"
        else:
            tokens[gkey] = ''.join([str(random.randint(0,9)) for i in range(8)])
            tokens[ckey] = tokens[gkey]+"-1"

    if not os.path.exists(clip_dir):
        os.mkdir(clip_dir)

    print "Started clipping."
    
    for eaf_file, start, stop in clippables:
        wav_file = eaf_wav_files[eaf_file]

        if (wav_file, start, stop) in already_clipped:
            continue
        
        values = [tiers[f].get((eaf_file, start, stop),'') for f in fields]

        clip_base = os.path.splitext(wav_file)[0]+"["+human_time(start)+"-"+human_time(stop)+"]"
        clip_base = clip_base.replace('.', '')
        clip_base = clip_base.replace(':', '_')
        cite_code = os.path.splitext(wav_file)[0]+":"+human_time(start)
        
        # If the filename for output already exists, add a number to it
        file_index = ''
        if False: # set to over-write
            while os.path.exists(clip_dir + '/' + clip_base + str(file_index)
                                 + '.wav'):
                if file_index == '':
                    file_index = 1
                else:
                    file_index += 1

        clip_file = clip_base + str(file_index) + '.wav'
        
        # Convert the times frload_purepecha_metadataom milliseconds into the
        # human-friendly minute:second format.
        start_human = human_time(start)
        stop_human = human_time(stop)
        length = stop - start
        length_human = human_time(length)

        # Write out the clip wav
        print eaf_file, clip_file
        res = clip_wav(wav_dir + '/' + wav_file,
                       clip_dir + '/' + clip_file,
                       start, stop)
        print res
        print
        if not res:
            continue
            
        already_clipped.add((wav_file, start, stop))
            
        # pull up name of speaker (contributor)
        speaker = spkr_dict[os.path.splitext(wav_file)[0]]
        if comment_field in fields: # speaker annotation in comment field
            comment = values[fields.index(comment_field)]
            if comment and comment.split()[0] == comment.split()[0].upper():
                speaker = comment.split()[0]
        
        clip_fh.write(values + [clip_file,
                                wav_file, eaf_file,
                                speaker,
                                # creator,
                                start_human, stop_human, length_human,
                                str(start), str(stop), str(length)])
        
        table_fh.write('<tr clip="' + clip_file.encode('utf-8') + '">\n' +
                       '\n'.join(['<td>'+v.encode('utf-8')+'</td>' for v in values]) +
                       '\n' +
                       '<td>' + speaker + '</td>\n' +
                       '<td>' + cite_code  + '</td>\n' +
                       '<td>' + length_human + '</td>\n' +
                       '<td>' + start_human + '</td>\n' +
                       '<td>' + stop_human + '</td>\n' +
                       '<td>' + wav_file + '</td>\n' +
                       '<td>' + eaf_file + '</td>\n' +
                       '<td>' + clip_file + '</td>\n' +
                       '<td>' + tokens[(eaf_file,start,stop)] + '</td>\n' +
                       '</tr>\n')

    table_fh.write('</tbody>\n</table>\n')
    clip_fh.close()
    table_fh.close()
    
    this_dir = os.path.dirname(sys.argv[-1])
    wrap_fh = open(os.path.join(this_dir,wrapper),'rb')

    table_fh = open(meta_dir + '/clip_metadata.html', 'rb')
    
    index_fh = open(meta_dir + '/index.html', 'wb')

    for line in wrap_fh:
        index_fh.write(line)
        if line.startswith('<div class="container"'):
            index_fh.writelines(list(table_fh))
            
    index_fh.close()
    


def find_wav_file(eaf_file):
    """Look through an EAF file to find the wav file it corresponds to."""

    tree = etree.ElementTree()
    tree.parse(eaf_file)
    media = tree.find("HEADER/MEDIA_DESCRIPTOR")
    if media == None:
        print "WARNING: No MEDIA_DESCRIPTOR tag found."
        print etree.tostring(tree.getroot())[:400]
        basename = os.path.splitext(os.path.basename(eaf_file))[0]
        print basename, eaf_file
        print "Trying "+basename+".WAV"
        return basename+".WAV"
    else:
        return os.path.basename(media.get("MEDIA_URL"))
##        
##    
##    wav_patt = re.compile('PR\d+.wav', re.IGNORECASE)
##
##    wav_file = False
##    fh = open(eaf_file)
##    while not wav_file:
##        line = fh.readline()
##        res = wav_patt.search(line)
##        if res:
##            return res.group()
##
##    return False
    

def find_clippable_segments(tiers, fields):
    """Find segments that have at least an IPA transcription and either a
    Spanish or Enlgish translation."""

    phon = tiers[fields[0]]
    good_keys = []

    for key, value in phon.iteritems():
        if value != '':
            notes = [tiers[f].get(key,'') for f in fields[1:]]
            if any(notes):
                good_keys.append(key)
                
    return good_keys

def filter_clippables(clippables, eaf_wav_files, eaf_creators):
    """We have multiple EAFs for some wavs. When this is the case, only use
    the one that is in the EAF creators metadata."""
    
    new_clippables = []
    has_metadata = {}
    
    # Find out which wav regions we have metadata for
    for eaf_file, start, stop in clippables:
        wav_file = eaf_wav_files[eaf_file]
        has_metadata[(wav_file, start, stop)] = eaf_file in eaf_creators
    
    # Retain all the clippables where that EAF has metadata, or we don't have
    # another EAF for the same wav region that does have metadata
    for eaf_file, start, stop in clippables:
        wav_file = eaf_wav_files[eaf_file]
        # If we have a creator, add it to clippables no matter what
        if ((eaf_file in eaf_creators) or
                (not has_metadata[(wav_file, start, stop)])):
            new_clippables.append((eaf_file, start, stop))

    return new_clippables

def get_speakers(meta_file, spk_field= "Contributor"):
    """Parse the metadata file to return Speaker guesses for each WAV file"""
    fh = utfcsv.UnicodeReader( open(meta_file, 'r'), dialect="excel-tab", fieldnames= True )
    
    print fh.fieldnames
    name_field = [f for f in ["Name", "File"] if f in fh.fieldnames][0]
    
    spk = {}
    for line in fh:
        if line["Format"].lower() == ("wav"):
            spk[line[name_field]] = line[spk_field]
            
    return spk
    

def parse_export_file(filename,fields=[]):
    """Parse an ELAN text export file. Columns are assumed to be:

        annotation type
        start time in ms
        stop time in ms
        field value
        eaf filename

        Args:
            filename: ELAN export text file full path

        returns:
            ipa, english, spanish: dicts keyed on (eaf, start, top) tuple,
                                   with annotation value for that type as
                                   value

    """

    tiers = {}

    fh = utfcsv.UnicodeReader(open(filename, 'r'))

    if fields: # only pay attention to specified fields
        for f in fields:
            tiers[f] = {}
        for line in fh:
            atype, start, stop, value, eaf = line
            key = (os.path.basename(eaf), int(start), int(stop))
            if atype in tiers:
                tiers[atype][key] = value
            else:
                print 'Invalid atype:',atype

    else: # collect info on all the fields found
        for line in fh:
            if len(line) == 5:
                atype, start, stop, value, eaf = line
            else:
                raise ValueError("""Line not in expected format:
                """+repr(line)+"""
                Columns are assumed to be:
                   - annotation type
                   - start time in ms
                   - stop time in ms
                   - field value
                   - eaf filename""")
            key = (os.path.basename(eaf), int(start), int(stop))
            if atype not in tiers:
                fields.append(atype)
                tiers[atype] = {}
            tiers[atype][key] = value
            
    return tiers, fields


def clip_wav(wav_file, clip_file, start, stop):
    """Clip from start to stop in wav_file file, save to clip_file.

    Args:
        wav_file: full path to input wav
        clip_file: full path to output wav clip
        start: start time in wav_file in milliseconds
        stop: stop time in wav_file in milliseconds
    """

    win = wave.open(wav_file, 'r')
    framerate = win.getframerate()
    length = stop - start
    frames = int((length / 1000.0) * framerate)
    start_frame = int((start / 1000.0) * framerate)
    wout = wave.open(clip_file, 'w')
    wout.setparams(win.getparams())
    print wav_file, clip_file, start, stop
    try:
        win.setpos(start_frame)
    except wave.Error:
        print "Bad position"
        print
        return False
    wout.setparams(win.getparams())
    wout.writeframes(win.readframes(frames))
    win.close()
    wout.close()
    
    return True

def human_time(milliseconds):
    """Take a timsetamp in milliseconds and convert it into the familiar
    minutes:seconds format.

    Args:
        milliseconds: time expressed in milliseconds

    Returns:
        str, time in the minutes:seconds format

    For example:
    """
    milliseconds = int(milliseconds)

    seconds = milliseconds / 1000.0
    minutes = seconds / 60

    seconds = "{0:0>4.1f}".format(seconds % 60)
    minutes = str(int(minutes))

    return minutes + ':' + seconds


if __name__ == "__main__":
    main()

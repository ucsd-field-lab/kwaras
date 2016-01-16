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

Authors: Lucien Carroll, Russ Horton

"""
__author__ = 'lucien@discurs.us'

import os
import json
import random
import re
import wave
from xml.etree import ElementTree as etree

from kwaras.formats import utfcsv


def config():
    lang = ["Gitonga", "Raramuri", "Mixtec"][1]

    if lang == "Gitonga":
        cfg_file = "conf/gitonga.txt"
    elif lang == "Raramuri":
        cfg_file = "conf/raramuri.txt"
    elif lang == "Mixtec":
        cfg_file = "conf/mixtec.txt"
    else:
        cfg_file = "config.txt"

    up_dir = os.path.dirname(os.getcwd())

    print "Using", cfg_file, "in", up_dir, "for configuration settings."
    cfg = json.load(os.path.join(up_dir, cfg_file))

    comment_field = "Note"  # necessary only if used for speaker annotation
    wrapper = os.path.join(up_dir, "web/index_wrapper.html")

    return cfg, comment_field, wrapper

def filter_fields(fields, export_fields):
    fnames = set([f.partition("@")[0] for f in fields])
    if export_fields is not []:
        fields = [f for f in fields if f.partition("@")[0] in export_fields]
        fnames = [f for f in export_fields if f in fnames]
    fields.sort(key=lambda f: export_fields.index(f.partition("@")[0]))
    return fnames, fields


def export_elan(cfg):

    csvfile = utfcsv.UnicodeWriter(os.path.join(cfg["FILE_DIR"], "status.csv"), "excel", mode="ab")
    csvfile.write(["Filename"] + cfg["EXP_FIELDS"].split(","))

    if True: # TODO support language selection
        from kwaras.langs import Raramuri as language
    else:
        from kwaras.langs import Mixtec as language

    for filename in os.listdir(os.path.join(cfg["FILE_DIR"], cfg["OLD_EAFS"])):
        print filename
        if not os.path.splitext(filename)[1].lower() == ".eaf":
            print "Not an eaf:", filename, os.path.splitext(filename)
        else:
            fpath = os.path.join(cfg["FILE_DIR"], cfg["OLD_EAFS"], filename)
            # template = os.path.join(cfg["FILE_DIR"], cfg["TEMPLATE"])
            eafile = language.cleanEaf(fpath)
            eafile.write(os.path.join(cfg["FILE_DIR"], cfg["NEW_EAFS"], filename))
            eafile.exportToCSV(os.path.join(cfg["FILE_DIR"], cfg["CSV"]), "excel", cfg["EXP_FIELDS"].split(","), "ab")
            status = sorted(eafile.status(cfg["EXP_FIELDS"].split(",")).items())
            print status
            csvfile.write([filename] + [str(v * 100) + "%" for (k, v) in status])


def main(cfg):
    """Perform the metadata extraction and file renaming."""

    export_elan(cfg)

    # Parse the ELAN export, get the IPA, English and Spanish timestamps
    # fields = ["IPA","English","Spanish"] # for Purepecha?
    # fields = [] # will collect all fields, assuming the first one is primary phonetic
    # tiers, fields = parse_export_file(export_file, fields) 
    tiers, fields = parse_export_file(cfg['CSV'])
    print "Export file parsed."

    # filter and sort field names
    fnames, fields = filter_fields(fields, cfg['EXP_FIELDS'])
    print "fnames:", fnames
    print "fields:", fields

    # Find time ranges for which there is indexable annotation
    clippables = find_clippable_segments(tiers, fields)
    print "Clippables found."

    # Look in each EAF to see which wav file it references
    eaf_wav_files = {}
    for eaf_file, start, stop in clippables:
        if eaf_file not in eaf_wav_files:
            wav_file = find_wav_file(cfg['NEW_EAFS'] + '/' + eaf_file)
            eaf_wav_files[eaf_file] = wav_file

    # Get mapping between EAFs and speakers
    spkr_dict = get_speakers(cfg['META'])

    # Output for clip metadata
    clip_fh = utfcsv.UnicodeWriter(open(meta_dir + '/clip_metadata.csv', 'w'))
    table_fh = open(meta_dir + '/clip_metadata.html', 'w')

    table_fh.write('<table id="clip_metadata">\n<thead>\n<tr>\n' +
                   '\n'.join(['<th class="Annotation">' + f + '&nbsp;</th>' for f in fnames]) +
                   '\n' +
                   '<th class="Citation">Speaker&nbsp;</th>\n' +
                   '<th class="Citation">Citation&nbsp;</th>\n'
                   '<th>Length&nbsp;</th>\n' +
                   '\n'.join(['<th class="Hide">' + f + '&nbsp;</th>'
                              for f in ['Start', 'Stop', 'WAV', 'EAF', 'File', 'Token']]) +
                   '</tr>\n</thead>\n')
    table_fh.write('<tfoot>\n<tr>\n' +
                   '\n'.join(['<th><div><input type="text" value="Search ' +
                              f + '" class="search_init"></div></th>' for f in fnames]) +
                   '\n' +
                   '\n'.join(['<th><div><input type="text" value="Search ' +
                              f + '" class="search_init"></div></th>'
                              for f in ['Speaker', 'Citation', 'Length']]) +
                   '\n' +
                   '\n'.join(['<th><div><input type="text" value="Search ' +
                              f + '" class="search_init"></div></th>'
                              for f in ['Start', 'Stop', 'WAV', 'EAF', 'File', 'Token']]) +
                   '\n</tr>\n</tfoot>\n<tbody>\n')


    # If there are multiple eafs that define the same clipping regions for 
    # the same wav file, we want to use the EAF that is in the EAF metadata.
    # clippables = filter_clippables(clippables, eaf_wav_files, eaf_creators)

    # define duplicates as rows with identical annotations in @fields
    tokens = {}
    for ckey in clippables:
        gkey = ":".join([tiers[f].get(ckey, '') for f in fields])
        if gkey in tokens:
            tokens[ckey] = tokens[gkey] + "-2"
        else:
            tokens[gkey] = ''.join([str(random.randint(0, 9)) for _i in range(8)])
            tokens[ckey] = tokens[gkey] + "-1"

    if not os.path.exists(clip_dir):
        os.mkdir(clip_dir)

    print "Started clipping."

    mk_table_rows(clippables)

    table_fh.write('</tbody>\n</table>\n')
    clip_fh.close()
    table_fh.close()


def wrap_html(cfg, wrapper):

    wrap_fh = open(os.path.join(www_dir, wrapper), 'rb')

    table_fh = open(os.path.join(cfg['WWW'], '/clip_metadata.html'), 'rb')

    index_fh = open(meta_dir + '/index.html', 'wb')

    for line in wrap_fh:
        if line.strip().startswith('<title>'):
            index_fh.write('<title>' + page_title + '</title>')
        else:
            index_fh.write(line)

        if line.strip().startswith('<body>'):
            index_fh.write(NAV_BAR)

        if line.strip().startswith('<div class="container"'):
            index_fh.writelines(list(table_fh))

    index_fh.close()

def mk_table_rows(clippables):

    already_clipped = set()

    for eaf_file, start, stop in clippables:

        wav_file = eaf_wav_files[eaf_file]

        if (wav_file, start, stop) in already_clipped:
            continue

        vdict = {}
        spkr_code = ''
        speaker = ''
        for f in fields:
            fname = f.partition("@")[0]
            v = tiers[f].get((eaf_file, start, stop), '')
            vdict[fname] = vdict.get(fname, '') + v
            if v is not '':
                spkr_code = f.partition("@")[2]
                if spkr_code is not '':
                    speaker = spkr_code
        values = [vdict[f] for f in fnames]
        # values = [tiers[f].get((eaf_file, start, stop),'') for f in fields] #TODO dereference the fname vs field
        print values, speaker

        clip_base = os.path.splitext(wav_file)[0] + "[" + human_time(start) + "-" + human_time(stop) + "]"
        clip_base = clip_base.replace('.', '')
        clip_base = clip_base.replace(':', '_')
        cite_code = os.path.splitext(wav_file)[0] + ":" + human_time(start)

        # If the filename for output already exists, add a number to it
        file_index = ''
        if False:  # set to over-write
            while os.path.exists(clip_dir + '/' + clip_base + str(file_index)
                                         + '.wav'):
                if file_index == '':
                    file_index = 1
                else:
                    file_index += 1

        clip_file = clip_base + str(file_index) + '.wav'

        # Convert the times into the
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
        print "spkr 1:", speaker
        if speaker == '':
            speaker = spkr_dict[os.path.splitext(wav_file)[0]]
            print "spkr 2:", speaker
            if comment_field in fnames:  # speaker annotation in comment field
                comment = values[fnames.index(comment_field)]
                if comment.strip() and re.match("[A-Z, ]+", comment.split()[0]):
                    # formerly  == comment.split()[0].upper():
                    speaker = comment.split()[0]
                    print "spkr 3:", speaker


        clip_fh.write(values + [clip_file,
                                wav_file, eaf_file,
                                speaker,
                                # creator,
                                start_human, stop_human, length_human,
                                str(start), str(stop), str(length)])

        table_fh.write('<tr clip="' + clip_file.encode('utf-8') + '">\n' +
                       '\n'.join(['<td>' + v.encode('utf-8') + '</td>' for v in values]) +
                       '\n' +
                       '<td>' + speaker + '</td>\n' +
                       '<td>' + cite_code + '</td>\n' +
                       '<td>' + length_human + '</td>\n' +
                       '<td>' + start_human + '</td>\n' +
                       '<td>' + stop_human + '</td>\n' +
                       '<td>' + wav_file + '</td>\n' +
                       '<td>' + eaf_file + '</td>\n' +
                       '<td> <a href="clips/' + clip_file + '" target="_blank">' + clip_file + '</a></td>\n' +
                       '<td>' + tokens[(eaf_file, start, stop)] + '</td>\n' +
                       '</tr>\n')


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
        print "Trying " + basename + ".WAV"
        return basename + ".WAV"
    else:
        return os.path.basename(media.get("MEDIA_URL"))



def find_clippable_segments(tiers, fields):
    """Find segments that have non-empty annotations"""

    fieldtypes = [f.partition("@")[0] for f in fields]
    fnames = sorted(list(set(fieldtypes)), key=lambda x: fieldtypes.index(x))[
             :3]  # assuming one of first 3 field types is baseline
    print "fnames", fnames
    basefields = [f for f in fields if f.partition("@")[0] in fnames]
    print "basefields", basefields
    allkeys = [k for f in basefields for k in tiers[f].keys()]
    # tiers[fields[0]].keys() + tiers[fields[1]].keys() + tiers[fields[2]].keys() + tiers[fields[3]].keys()
    allkeys = list(set(allkeys))  # uniq
    good_keys = []

    for key in allkeys:
        notes = [tiers[f].get(key, '').strip() for f in fields]
        if any(notes):
            good_keys.append(key)

    print len(allkeys), len(good_keys)
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


def get_speakers(meta_file, spk_field="Contributor"):
    """Parse the metadata file to return Speaker guesses for each WAV file"""
    fh = utfcsv.UnicodeReader(open(meta_file, 'r'), fieldnames=True)

    print fh.fieldnames
    name_field = [f for f in ["Name", "File"] if f in fh.fieldnames][0]

    spk = {}
    for line in fh:
        if line["Format"].lower() == ("wav"):
            spk[line[name_field]] = line[spk_field]

    return spk


def parse_export_file(filename, fields=[]):
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

    if fields:  # only pay attention to specified fields
        for f in fields:
            tiers[f] = {}
        for line in fh:
            atype, start, stop, value, eaf = line
            key = (os.path.basename(eaf), int(start), int(stop))
            if atype in tiers:
                tiers[atype][key] = value
            else:
                print 'Invalid atype:', atype

    else:  # collect info on all the fields found
        for line in fh:
            if len(line) == 5:
                atype, start, stop, value, eaf = line
            else:
                raise ValueError("""Line not in expected format:
                """ + repr(line) + """
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
    cfg, comments, wrapper = config()
    main(cfg)

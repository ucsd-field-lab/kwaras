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

import os
import csv
import json
import random
import re
import wave
from xml.etree import ElementTree as etree

from kwaras.formats import xlsx


def config(lang=None):
    if lang == "Gitonga":
        cfg_file = "conf/gitonga.txt"
    elif lang == "Raramuri":
        cfg_file = "conf/raramuri.txt"
    elif lang == "Mixtec":
        cfg_file = "conf/mixtec.txt"
    elif lang == "Kumiai":
        cfg_file = "conf/kumiai.txt"
    else:  # Other
        cfg_file = "config.txt"

    up_dir = os.path.dirname(os.getcwd())

    print("Using", cfg_file, "in", up_dir, "for configuration settings.")
    cfg = json.load(os.path.join(up_dir, cfg_file))

    return cfg


def filter_fields(fields, export_fields):
    fnames = set([f.partition("@")[0] for f in fields])
    if export_fields is not []:
        fields = [f for f in fields if f.partition("@")[0] in export_fields]
        fnames = [f for f in export_fields if f in fnames]
    fields.sort(key=lambda f: export_fields.index(f.partition("@")[0]))
    return fnames, fields


def export_elan(cfg, export_fields):
    csvfile = csv.writer(open(os.path.join(cfg["FILE_DIR"], "status.csv"), mode="w", encoding='utf-8'))
    csvfile.writerow(["Filename"] + export_fields)

    if cfg['LANGUAGE'].lower() == "raramuri":
        from kwaras.langs import Raramuri as language
    elif cfg['LANGUAGE'].lower() == "mixtec":
        from kwaras.langs import Mixtec as language
    elif cfg['LANGUAGE'].lower() == "kumiai":
        from kwaras.langs import Kumiai as language
    else:
        from kwaras.langs import Other as language

    template = None

    cfg["CSV"] = os.path.join(cfg["FILE_DIR"], "data.csv")
    cfg['NEW_EAFS'] = os.path.join(cfg['OLD_EAFS'], 'auto')
    if not os.path.exists(cfg['NEW_EAFS']):
        os.mkdir(cfg['NEW_EAFS'])
    if os.path.exists(cfg["CSV"]):
        os.remove(cfg["CSV"])

    for filename in os.listdir(cfg["OLD_EAFS"]):
        print(filename)
        if not os.path.splitext(filename)[1].lower() == ".eaf":
            print("Not an eaf:", filename, os.path.splitext(filename)[1])
        elif os.path.basename(filename).startswith('.'):
            print("Hidden file:", filename)
        else:
            fpath = os.path.join(cfg["OLD_EAFS"], filename)
            if template is None:
                template = fpath
                print("Using {0} as template for ELAN types".format(fpath))
            # template = os.path.join(cfg["FILE_DIR"], cfg["TEMPLATE"])
            eafile = language.clean_eaf(fpath, template)
            eafile.write(os.path.join(cfg["NEW_EAFS"], filename))
            eafile.export_to_csv(cfg["CSV"], "excel", export_fields, "a")
            status = sorted(eafile.status(export_fields).items())
            print(status)
            csvfile.writerow([filename] + [str(v * 100) + "%" for (k, v) in status])


def main(cfg):
    """Perform the metadata extraction and file renaming."""

    export_fields = [f.strip() for f in cfg["EXP_FIELDS"].split(',')]
    print("Exporting fields: {0}".format(export_fields))
    export_elan(cfg, export_fields)
    print("ELAN data exported.")

    # Parse the ELAN export, get the IPA, English and Spanish timestamps
    # fields = ["IPA","English","Spanish"] # for Purepecha?
    # fields = [] # will collect all fields, assuming the first one is primary phonetic
    # tiers, fields = parse_export_file(export_file, fields)
    tiers, fields = parse_export_file(cfg['CSV'])
    print("Export file parsed.")

    # filter and sort field names
    fnames, fields = filter_fields(fields, export_fields)
    print("fnames:", fnames)
    print("fields:", fields)

    # Find time ranges for which there is indexable annotation
    clippables = find_clippable_segments(tiers, fields)
    print("Clippables found.")

    # Look in each EAF to see which wav file it references
    eaf_wav_files = {}
    for eaf_file, start, stop in clippables:
        if eaf_file not in eaf_wav_files:
            wav_file = find_wav_file(os.path.join(cfg['NEW_EAFS'], eaf_file))
            eaf_wav_files[eaf_file] = wav_file

    # Get mapping between EAFs and speakers
    spkr_dict = get_speakers(cfg['META'])

    # Output for clip metadata
    clip_fh = csv.writer(open(os.path.join(cfg['WWW'], 'clip_metadata.csv'), 'w'))
    table_fh = open(os.path.join(cfg['WWW'], 'clip_metadata.html'), 'w')

    # Write header/footer
    clip_fh.write(fnames + ['Speaker', 'Citation', 'Length', 'Start', 'Stop', 'WAV', 'EAF', 'File', 'Token'])

    table_fh.write('''<table id="clip_metadata">
                        <thead>
                          <tr>
                            ''' +
                   '\n'.join(['<th class="Annotation">{0}&nbsp;</th>'.format(f) for f in fnames]) +
                   '''
                            <th class="Citation">Speaker&nbsp;</th>
                            <th class="Citation">Citation&nbsp;</th>
                            <th>Length&nbsp;</th>'
                            ''' +
                   '\n'.join(['<th class="Hide">{0}&nbsp;</th>'.format(f)
                              for f in ['Start', 'Stop', 'WAV', 'EAF', 'File', 'Token']]) +
                   '''
                          </tr>
                        </thead>''')

    table_fh.write('''<tfoot>
                        <tr>
                          ''' +
                   '\n'.join(['<th><div><input type="text" value="Search {0}" class="search_init"></div></th>'.format(f)
                              for f in fnames + ['Speaker', 'Citation', 'Length', 'Start', 'Stop',
                                                 'WAV', 'EAF', 'File', 'Token']]) +
                   '''
                        </tr>
                      </tfoot>
                      <tbody>''')

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
            tokens[gkey] = ''.join([str(random.randint(0, 9)) for _ in range(8)])
            tokens[ckey] = tokens[gkey] + "-1"

    cfg['CLIPS'] = os.path.join(cfg['WWW'], 'clips')
    if not os.path.exists(cfg['CLIPS']):
        os.mkdir(cfg['CLIPS'])

    print("Started clipping.")

    mk_table_rows(clippables, eaf_wav_files, spkr_dict, tiers, fields, fnames, clip_fh, table_fh, tokens, cfg)

    table_fh.write('</tbody>\n</table>\n')
    clip_fh.close()
    table_fh.close()

    wrap_html(cfg, 'web/index_wrapper.html')

    print("Finished.")


def wrap_html(cfg, wrapper):
    wrap_fh = open(wrapper, 'rb')

    table_fh = open(os.path.join(cfg['WWW'], 'clip_metadata.html'), 'rb')

    index_fh = open(os.path.join(cfg['WWW'], 'index.html'), 'wb')

    for line in wrap_fh:
        if line.strip().startswith('<title>'):
            index_fh.write('<title>' + cfg['PG_TITLE'].encode('utf-8') + '</title>')
        else:
            index_fh.write(line)

        if line.strip().startswith('<body>'):
            index_fh.write(cfg['NAV_BAR'].encode('utf-8'))

        if line.strip().startswith('<div class="container"'):
            index_fh.writelines(list(table_fh))

    index_fh.close()


def mk_table_rows(clippables, eaf_wav_files, spkr_dict, tiers, fields, fnames, clip_fh, table_fh, tokens, cfg):
    comment_field = 'Note'
    already_clipped = set()

    for eaf_file, start, stop in clippables:

        print()

        wav_file = eaf_wav_files[eaf_file]

        if (wav_file, start, stop) in already_clipped:
            continue

        vdict = {}
        speaker = ''
        for f in fields:
            fname = f.partition("@")[0]
            v = tiers[f].get((eaf_file, start, stop), '')
            vdict[fname] = vdict.get(fname, '') + v
            if v:
                spkr_code = f.partition("@")[2]
                if spkr_code:
                    speaker = spkr_code
        values = [vdict[f] for f in fnames]
        # values = [tiers[f].get((eaf_file, start, stop),'') for f in fields] #TODO dereference the fname vs field
        print(values, speaker)

        clip_base = os.path.splitext(wav_file)[0] + "[" + human_time(start, True) + "-" + human_time(stop, True) + "]"
        clip_base = clip_base.replace('.', '')
        clip_base = clip_base.replace(':', '_')
        cite_code = os.path.splitext(wav_file)[0] + ":" + human_time(start, padded=True)

        # If the filename for output already exists, add a number to it
        file_index = ''
        if False:  # set to over-write
            while os.path.exists(os.path.join(cfg['CLIPS'], clip_base + str(file_index) + '.wav')):
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
        print(eaf_file, clip_file)
        try:
            res = clip_wav(os.path.join(cfg['WAV'], wav_file),
                           os.path.join(cfg['CLIPS'], clip_file),
                           start, stop)
        except IOError:
            print("WARNING: no WAV file named {0} found".format(wav_file))
            continue

        print('clipping successful:', res)
        if not res:
            continue

        already_clipped.add((wav_file, start, stop))

        # pull up name of speaker (contributor)
        if speaker != '':
            print("speaker value from tier name:", speaker)
        else:
            wav_file_base = os.path.splitext(wav_file)[0]
            if wav_file_base in spkr_dict:
                speaker = spkr_dict[wav_file_base]
                print("speaker value from metadata:", speaker)
            else:
                print("WARNING: No metadata for {0} found in metadata file".format(wav_file_base))
                if comment_field in fnames:  # speaker annotation in comment field
                    comment = values[fnames.index(comment_field)]
                    if comment.strip() and re.match("[A-Z, ]+", comment.split()[0]):
                        # formerly  == comment.split()[0].upper():
                        speaker = comment.split()[0]
                        print("speaker value from comment field:", speaker)

        clip_fh.write(values + [speaker, cite_code, length_human,
                                start_human, stop_human,
                                wav_file, eaf_file,
                                clip_file,
                                tokens[(eaf_file, start, stop)]])

        row = '\n'.join(['<tr clip="{0}">'.format(clip_file)] +
                         ['<td>{0}</td>'.format(v) for v in values] +
                         ['<td>{0}</td>'.format(v) for v in (speaker, cite_code, length_human,
                                                              start_human, stop_human,
                                                              wav_file, eaf_file)] +
                         ['<td> <a href="clips/{0}" target="_blank">{1}</a></td>'.format(clip_file, clip_file)] +
                         ['<td>{0}</td>'.format(tokens[(eaf_file, start, stop)])]
                         )
        try:
            table_fh.write(row.encode('utf-8'))
        except UnicodeDecodeError as err:
            print("WARNING: Skipping annotation because it can't be decoded:", err.message)
            print(repr(row))


def find_wav_file(eaf_file):
    """Look through an EAF file to find the wav file it corresponds to."""

    tree = etree.ElementTree()
    tree.parse(eaf_file)
    media = tree.find("HEADER/MEDIA_DESCRIPTOR")
    if media is None:
        print("WARNING: No MEDIA_DESCRIPTOR tag found.")
        print(etree.tostring(tree.getroot())[:400])
        basename = os.path.splitext(os.path.basename(eaf_file))[0]
        print(basename, eaf_file)
        print("Trying " + basename + ".WAV")
        return basename + ".WAV"
    else:
        return os.path.basename(media.get("MEDIA_URL"))


def find_clippable_segments(tiers, fields):
    """Find segments that have non-empty annotations"""

    fieldtypes = [f.partition("@")[0] for f in fields]
    fnames = sorted(list(set(fieldtypes)), key=lambda x: fieldtypes.index(x))[
             :3]  # assuming one of first 3 field types is baseline
    print("fnames", fnames)
    basefields = [f for f in fields if f.partition("@")[0] in fnames]
    print("basefields", basefields)
    allkeys = [k for f in basefields for k in list(tiers[f].keys())]
    # tiers[fields[0]].keys() + tiers[fields[1]].keys() + tiers[fields[2]].keys() + tiers[fields[3]].keys()
    allkeys = list(set(allkeys))  # uniq
    good_keys = []

    for key in allkeys:
        notes = [tiers[f].get(key, '').strip() for f in fields]
        if any(notes):
            good_keys.append(key)

    print(len(allkeys), len(good_keys))
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


def get_speakers(meta_file):
    """Parse the metadata file to return Speaker guesses for each WAV file"""
    filename_fields = ["Name", "File"]
    speaker_fields = ["Contributor"]
    format_fields = ["Format"]

    fh = None
    if not os.path.exists(meta_file):
        print("WARNING: no META data file '{0}' found".format(meta_file))
        return {}
    if os.path.splitext(meta_file)[1].lower() == '.csv':
        for encoding in ('utf-8', 'windows-1252', 'windows-1251'):
            try:
                fh = csv.reader(open(meta_file, 'r', encoding=encoding, newline=''))
                fieldnames = next(fh)
            except UnicodeDecodeError:
                print("Failed to decode metadata file as {} encoding.".format(encoding))
            else:
                print("Opening metadata file as {} encoding.".format(encoding))
                break
    elif os.path.splitext(meta_file)[1].lower() == '.xlsx':
        fh = xlsx.ExcelReader(meta_file)
        fieldnames = fh.fieldnames
    else:
        print("Error: file type '{}' not recognized".format(os.path.splitext(meta_file)[1]))
    if fh is None:
        print("WARNING: Failed to read metadata file. Try saving as XLSX or UTF-8 CSV.")
        return {}

    print('Session Metadata Column Names:', fieldnames)
    name_field = [f for f in filename_fields if f in fieldnames][0]
    spk_field = [f for f in speaker_fields if f in fieldnames][0]
    fmt_field = [f for f in format_fields if f in fieldnames]
    fmt_field = fmt_field[0] if len(fmt_field) > 0 else None

    spk = {}
    if fmt_field is None:
        for line in fh:
            spk[line[name_field]] = line[spk_field]
    else:
        for line in fh:
            if line["Format"].lower() == "wav":
                spk[line[name_field]] = line[spk_field]

    return spk


def parse_export_file(filename, fields=()):
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

    fh = csv.reader(open(filename, 'r', encoding='utf-8', newline=''))

    if fields:  # only pay attention to specified fields
        for f in fields:
            tiers[f] = {}
        for line in fh:
            atype, start, stop, value, eaf = line
            key = (os.path.basename(eaf), int(start), int(stop))
            if atype in tiers:
                tiers[atype][key] = value
            else:
                print('Invalid atype:', atype)

    else:  # collect info on all the fields found
        fields = []
        for line in fh:
            if not line:
                print(f'Warning: empty line in {filename}')
                continue
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
    print(wav_file, clip_file, start, stop)
    try:
        win.setpos(start_frame)
    except wave.Error:
        print("Bad position")
        print()
        return False
    wout.setparams(win.getparams())
    wout.writeframes(win.readframes(frames))
    win.close()
    wout.close()

    return True


def human_time(milliseconds, padded=False):
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

    if padded:
        stamp = "{0:0>2}:{1:0>4.1f}".format(int(minutes), seconds % 60)
    else:
        stamp = "{0}:{1:0>4.1f}".format(int(minutes), seconds % 60)

    return stamp


if __name__ == "__main__":
    cfg = config()
    main(cfg)

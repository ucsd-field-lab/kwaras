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
Edited by Mark Simmons 9/6/2023
"""

import os
import csv
import json
import shutil
import logging
import random
import re
import wave
from xml.etree import ElementTree as etree

from typing import List, Tuple, Union

from kwaras.formats import xlsx

logger = logging.getLogger(__file__)

CITATION_COLUMNS = ['Speaker', 'Citation', 'Length']
HIDDEN_COLUMNS = ['Start', 'Stop', 'WAV', 'EAF', 'File', 'Token']


def config(lang: str = 'config') -> dict:
    """
    Looks for config file corresponding to lang in parent directory
    and returns as json object if found,
    if not found defaults to config.cfg.
    """
    # TODO: add script for making config files
    cfg_file = f"{lang.lower()}.cfg"

    up_dir = os.path.dirname(os.getcwd())

    try:
        cfg = json.load(os.path.join(up_dir, cfg_file))
        logger.info("Using %s in %s for configuration settings.", cfg_file, up_dir)
    except FileNotFoundError:
        logger.info("Using config.cfg in %s for configuration settings.", up_dir)
        cfg = json.load(os.path.join(up_dir, 'config.cfg'))

    return cfg


def filter_fields(fields: List[str], export_fields: List[str]) -> Tuple[List[str], List[str]]:
    fnames = set([f.partition("@")[0] for f in fields])
    if export_fields is not []:
        fields = [f for f in fields if f.partition("@")[0] in export_fields]
        fnames = [f for f in export_fields if f in fnames]
    fields.sort(key=lambda f: export_fields.index(f.partition("@")[0]))
    return fnames, fields


def export_elan(cfg: dict, export_fields: List[str]) -> None:
    csvfile = csv.DictWriter(
        open(os.path.join(cfg["FILE_DIR"], "status.csv"), mode="w", encoding='utf-8', newline=''),
        fieldnames=["Filename", "Speaker"] + export_fields, 
    )
    csvfile.writeheader()

    # TODO: create and import lang classes automatically
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
        if not os.path.splitext(filename)[1].lower() == ".eaf":
            logger.info("Skipping %s as not an eaf", filename)
        elif os.path.basename(filename).startswith('.'):
            logger.info("Skipping hidden file: %s", filename)
        else:
            fpath = os.path.join(cfg["OLD_EAFS"], filename)
            if template is None:
                template = fpath
                logger.info("Using %s as template for ELAN types", fpath)
            eafile = language.clean_eaf(fpath, template)
            eafile.write(os.path.join(cfg["NEW_EAFS"], filename))
            eafile.export_to_csv(cfg["CSV"], "excel", export_fields, "a")
            status = sorted(eafile.status(export_fields).items())
            logger.info("Status: %s", status)
            speakers = {k.partition('@')[2] for k, v in status}
            row = {s: {"Filename": filename, "Speaker": s} for s in speakers}
            for k, v in status:
                field, _, spkr = k.partition('@')
                row[spkr][field] = f"{v*100}%"
            for r in row.values():
                csvfile.writerow(r)


def main(cfg):
    """Perform the metadata extraction and file renaming."""

    export_fields = [f.strip() for f in cfg["EXP_FIELDS"]]
    logger.info("Exporting fields: %s".format(export_fields))
    export_elan(cfg, export_fields)
    logger.info("ELAN data exported.")

    # Parse the ELAN export
    tiers, fields = parse_export_file(cfg['CSV'])
    logger.info("Export file parsed.")

    # filter and sort field names
    fnames, fields = filter_fields(fields, export_fields)

    # Find time ranges for which there is indexable annotation
    clippables = find_clippable_segments(tiers, fields)

    # Look in each EAF to see which wav file it references
    eaf_wav_files = {}
    for eaf_file, start, stop in clippables:
        if eaf_file not in eaf_wav_files:
            wav_file = find_wav_file(os.path.join(cfg['NEW_EAFS'], eaf_file))
            eaf_wav_files[eaf_file] = wav_file

    # Get mapping between EAFs and speakers
    spkr_dict = get_speakers(cfg['META'])

    # Output for clip metadata
    clip_fh = csv.DictWriter(
        open(os.path.join(cfg['WWW'], 'clip_metadata.csv'), 'w', encoding='utf-8', newline=''), 
        fieldnames = fnames + CITATION_COLUMNS + HIDDEN_COLUMNS
    )
    table_fh = open(os.path.join(cfg['WWW'], 'clip_metadata.html'), 'w', encoding='utf-8')

    # Write header and footer
    clip_fh.writeheader()

    table_fh.write('''<table id="clip_metadata">
                        <thead>
                          <tr>
                            ''' +
                   '\n'.join(['<th class="Annotation">{0}&nbsp;</th>'.format(f) for f in fnames]) +
                   '\n'.join(['<th class="Citation">{0}&nbsp;</th>'.format(f) for f in CITATION_COLUMNS]) +
                   '\n'.join(['<th class="Hide">{0}&nbsp;</th>'.format(f) for f in HIDDEN_COLUMNS]) +
                   '''
                          </tr>
                        </thead>''')

    table_fh.write('''<tfoot>
                        <tr>
                          ''' +
                   '\n'.join(['<th><div><input type="text" value="Search {0}" class="search_init"></div></th>'.format(f)
                              for f in fnames + CITATION_COLUMNS + HIDDEN_COLUMNS]) +
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

    logger.info("Started clipping.")

    mk_table_rows(clippables, eaf_wav_files, spkr_dict, tiers, fields, fnames, clip_fh, table_fh, tokens, cfg)

    table_fh.write('</tbody>\n</table>\n')
    table_fh.close()

    wrap_html(cfg, 'web/index_wrapper.html')
    copy_web_files(cfg['WWW'])

    logger.info("Finished.")


def wrap_html(cfg, wrapper):
    wrap_fh = open(wrapper, 'r', encoding='utf-8')

    table_fh = open(os.path.join(cfg['WWW'], 'clip_metadata.html'), 'r', encoding='utf-8')

    index_fh = open(os.path.join(cfg['WWW'], 'index.html'), 'w', encoding='utf-8')

    for line in wrap_fh:
        if line.strip().startswith('<title>'):
            index_fh.write('<title>' + cfg['PG_TITLE'] + '</title>')
        else:
            index_fh.write(line)

        if line.strip().startswith('<body>'):
            index_fh.write(cfg['NAV_BAR'])

        if line.strip().startswith('<div class="container"'):
            index_fh.writelines(list(table_fh))

    index_fh.close()


def mk_table_rows(clippables, eaf_wav_files, spkr_dict, tiers, fields, fnames, clip_fh, table_fh, tokens, cfg):
    comment_field = 'Note'
    already_clipped = set()

    for eaf_file, start, stop in clippables:

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
        try:
            res = clip_wav(os.path.join(cfg['WAV'], wav_file),
                           os.path.join(cfg['CLIPS'], clip_file),
                           start, stop)
        except IOError:
            logger.warning("No WAV file named '%s' found", wav_file)
            continue

        if not res:
            continue

        already_clipped.add((wav_file, start, stop))

        # pull up name of speaker (contributor)
        if speaker != '':
            logger.info("Using speaker value from tier name: %s", speaker)
        else:
            wav_file_base = os.path.splitext(wav_file)[0]
            if wav_file_base in spkr_dict:
                speaker = spkr_dict[wav_file_base]
                logger.info("Using speaker value from metadata: %s", speaker)
            else:
                logger.warning("No metadata for %s found in metadata file", wav_file_base)
                if comment_field in fnames:  # speaker annotation in comment field
                    comment = values[fnames.index(comment_field)]
                    if comment.strip() and re.match("[A-Z, ]+", comment.split()[0]):
                        # formerly  == comment.split()[0].upper():
                        speaker = comment.split()[0]
                        logger.info("Using speaker value from comment field: %s", speaker)

        row = {
            **dict(zip(fnames, values)),
            **dict(zip(
                CITATION_COLUMNS + HIDDEN_COLUMNS,
                [speaker, cite_code, length_human, start_human, stop_human, wav_file, eaf_file, clip_file, tokens[(eaf_file, start, stop)]]
            ))
        }
        clip_fh.writerow(row)

        row = '\n'.join(['<tr clip="{0}">'.format(clip_file)] +
                         ['<td>{0}</td>'.format(v) for v in values] +
                         ['<td>{0}</td>'.format(v) for v in (speaker, cite_code, length_human,
                                                              start_human, stop_human,
                                                              wav_file, eaf_file)] +
                         ['<td> <a href="clips/{0}" target="_blank">{1}</a></td>'.format(clip_file, clip_file)] +
                         ['<td>{0}</td>'.format(tokens[(eaf_file, start, stop)])]
                         )
        try:
            table_fh.write(row)
        except UnicodeDecodeError as err:
            logger.warning("Skipping annotation because it can't be decoded (%s): %s", err.message, repr(row))

def copy_web_files(www_dir):
    shutil.copy('web/index_wrapper.html', os.path.join(www_dir, 'index_wrapper.html'))
    shutil.copytree('web/css', os.path.join(www_dir, 'css'))
    shutil.copytree('web/js', os.path.join(www_dir, 'js'))

def find_wav_file(eaf_file):
    """Look through an EAF file to find the wav file it corresponds to."""

    tree = etree.ElementTree()
    tree.parse(eaf_file)
    media = tree.find("HEADER/MEDIA_DESCRIPTOR")
    if media is None:
        logger.warning("No MEDIA_DESCRIPTOR tag found: %s", etree.tostring(tree.getroot())[:200])
        basename = os.path.splitext(os.path.basename(eaf_file))[0]
        logger.info("Assuming %s.WAV", basename)
        return basename + ".WAV"
    else:
        return os.path.basename(media.get("MEDIA_URL"))


def find_clippable_segments(tiers, fields):
    """Find segments that have non-empty annotations"""

    fieldtypes = [f.partition("@")[0] for f in fields]
    fnames = sorted(list(set(fieldtypes)), key=lambda x: fieldtypes.index(x))[:3]  # assume baseline is in first 3 fields
    basefields = [f for f in fields if f.partition("@")[0] in fnames]
    allkeys = [k for f in basefields for k in list(tiers[f].keys())]
    allkeys = list(set(allkeys))  # uniq
    good_keys = []

    for key in allkeys:
        notes = [tiers[f].get(key, '').strip() for f in fields]
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
                fh = csv.DictReader(open(meta_file, 'r', encoding=encoding, newline=''))
            except UnicodeDecodeError:
                print("Failed to decode metadata file as {} encoding.".format(encoding))
            else:
                print("Opening metadata file as {} encoding.".format(encoding))
                break
    elif os.path.splitext(meta_file)[1].lower() == '.xlsx':
        fh = xlsx.ExcelReader(meta_file)
    else:
        print("Error: file type '{}' not recognized".format(os.path.splitext(meta_file)[1]))
    if fh is None:
        print("WARNING: Failed to read metadata file. Try saving as XLSX or UTF-8 CSV.")
        return {}

    print('Session Metadata Column Names:', fh.fieldnames)
    name_field = [f for f in filename_fields if f in fh.fieldnames][0]
    spk_field = [f for f in speaker_fields if f in fh.fieldnames][0]
    fmt_field = [f for f in format_fields if f in fh.fieldnames]
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


def human_time(milliseconds: int, padded: bool = False) -> str:
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

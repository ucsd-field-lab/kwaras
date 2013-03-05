import wave, re, os

def framesToSecs(nframes,wavfile):
    return nframes / float(wavfile.getframerate())

def secsToFrames(nsecs,wavfile):
    return nsecs * wavfile.getframerate()

def bytesToFrames(nbytes,wavfile):
    return nbytes / wavfile.getsampwidth()

def framesToBytes(nframes,wavfile):
    return nframes * wavfile.getsampwidth()

def getFrames(clipname,longname):
    clip = wave.open(clipname)
    longsound = wave.open(longname)
    
    clipre = re.compile(re.escape(clip.readframes(clip.getframerate()/10))) # 0.1 seconds of bytes
    cliplen = clip.getnframes()
    clip.rewind()
    longsound.rewind()
    clipbytes = clip.readframes(cliplen)
            
    chunk = longsound.getframerate()*100 # 100 seconds
    nframes = longsound.getnframes() / chunk
    framelen = len(longsound.readframes(1))

    frames = None
    for idx in range(nframes+1):
        longsound.setpos(idx*chunk)
        longpiece = longsound.readframes(chunk)
        matches = list(clipre.finditer(longpiece))
        for m in matches:
            longsound.setpos(idx*chunk + m.start()/framelen)
            longbytes = longsound.readframes(cliplen)
            if longbytes == clipbytes:
                init = idx*chunk + m.start()/framelen
                frames = (init,init+cliplen,clip.getframerate())
                print "MATCH!",idx,frames,float(init)/clip.getframerate()
                return frames
            else:
                print "Missed match",idx,m.start()/framelen,m.end()/framelen
                print longsound.getsampwidth(),clip.getsampwidth(),framelen
                print len(longbytes),repr([longbytes[:30],longbytes[-10:]])
                print len(clipbytes),repr([clipbytes[:30],clipbytes[-10:]])
                print len(m.group()),repr([m.group()[:30],m.group()[-10:]])
    return frames



if __name__ == "__main__":
    
    clipname = "/Users/lucien/Data/Gitonga/my clips/clips/GT00169_4330_5610.wav"
    longname = "/Users/lucien/Data/Gitonga/my clips/WAV/GT00169.WAV"

    print "Finding",clipname,"in",longname,"..."
    print getFrames(wave.open(clipname),wave.open(longname))

    clipdir = "/Users/lucien/Data/Gitonga/my clips/GT065-069/"
    longname = "/Users/lucien/Data/Gitonga/gitonga/WAV files/GT00068.wav"
    longsound = wave.open(longname)
    for clipname in os.listdir(clipdir)[:5]:
        print "Finding",clipname,"in",longname,"..."
        print getFrames(wave.open(os.path.join(clipdir,clipname)),longsound)
     
    clipdir = "/Users/lucien/Data/Gitonga/my clips/GT001"
    wavdir = "/Users/lucien/Data/Gitonga/gitonga/WAV files"

    for longname in [l for l in os.listdir(wavdir)[:5] if l.lower().endswith(".wav")]:
        longsound = wave.open(os.path.join(wavdir,longname))
        print longname
        for clipname in [c for c in os.listdir(clipdir) if c.lower().endswith(".wav")]:
            # print "Finding",clipname,"in",longname,"..."
            if getFrames(wave.open(os.path.join(clipdir,clipname)),longsound):
                print clipname,"in",longname
        


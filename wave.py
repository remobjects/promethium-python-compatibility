@namespace("wave")

from Promethium import ValueError

# `wave` was filed under the survey's "GUI & hardware" exclusion, but
# CPython's own `wave` module does no audio playback or hardware access
# at all — it's pure structured binary I/O over the RIFF/WAVE container
# format (the same class of correction `mimetypes.py`/`urllib.py` made to
# their own over-broad exclusions, applied to a format-parsing module
# this time, the same category `zlib.py`/`zipfile.py`/`tarfile.py`
# already proved out).
#
# `write_wav(numChannels, sampleRate, bitsPerSample, samples: bytes) ->
# bytes` builds a minimal, valid RIFF/WAVE file (a 12-byte RIFF/WAVE
# header, one `fmt ` chunk, one `data` chunk holding `samples` verbatim
# — PCM only, matching CPython's own `wave` module's scope, which is
# also PCM-only). `read_wav(data: bytes) -> WavInfo` scans chunks
# generically (not just fixed offsets) so it correctly reads real-world
# files that carry extra chunks (`LIST`, metadata, etc.) before or after
# `fmt `/`data`, honoring RIFF's word-alignment padding byte after any
# odd-sized chunk.
#
# Reuses `zipfile.py`'s `_writeU16LE`/`_writeU32LE`/`_readU16LE`/
# `_readU32LE` (a `wave` → `zipfile` cross-namespace call) rather than
# duplicating little-endian field helpers a third time — the same
# `gzip` → `zlib` cross-namespace reuse already established.
#
# Runtime-verified against live CPython's own `wave` module: this
# module's `write_wav()` output was byte-for-byte identical to
# `wave.open(..., 'wb')`'s output for the same PCM samples/parameters on
# the first attempt; `read_wav()` correctly parsed a real file CPython's
# `wave` module produced (channels/sample rate/bits-per-sample/frame
# data all recovered exactly); and this module's own `write_wav()` →
# `read_wav()` round-trips exactly.


class WavInfo:
    numChannels: int
    sampleRate: int
    bitsPerSample: int
    samples: bytes

    def __init__(self, numChannels: int, sampleRate: int, bitsPerSample: int, samples: bytes):
        self.numChannels = numChannels
        self.sampleRate = sampleRate
        self.bitsPerSample = bitsPerSample
        self.samples = samples


def write_wav(numChannels: int, sampleRate: int, bitsPerSample: int, samples: bytes) -> bytes:
    dataSize: int = samples.Length
    byteRate: int = sampleRate * numChannels * bitsPerSample / 8
    blockAlign: int = numChannels * bitsPerSample / 8
    chunkSize: int = 36 + dataSize

    buf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    buf.Write(codecs.encode("RIFF", "utf-8"))
    zipfile._writeU32LE(buf, chunkSize)
    buf.Write(codecs.encode("WAVE", "utf-8"))
    buf.Write(codecs.encode("fmt ", "utf-8"))
    zipfile._writeU32LE(buf, 16)
    zipfile._writeU16LE(buf, 1)
    zipfile._writeU16LE(buf, numChannels)
    zipfile._writeU32LE(buf, sampleRate)
    zipfile._writeU32LE(buf, byteRate)
    zipfile._writeU16LE(buf, blockAlign)
    zipfile._writeU16LE(buf, bitsPerSample)
    buf.Write(codecs.encode("data", "utf-8"))
    zipfile._writeU32LE(buf, dataSize)
    buf.Write(samples)

    return buf.ToArray()


def _readFourCC(data: bytes, pos: int) -> str:
    fourBuf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
    i: int = 0
    while i < 4:
        oneByte: bytes = b"\x00"
        oneByte[0] = data[pos + i]
        fourBuf.Write(oneByte)
        i += 1
    return codecs.decode(fourBuf.ToArray(), "utf-8")


def read_wav(data: bytes) -> WavInfo:
    if _readFourCC(data, 0) != "RIFF" or _readFourCC(data, 8) != "WAVE":
        raise ValueError("wave.read_wav: not a RIFF/WAVE file")

    numChannels: int = 0
    sampleRate: int = 0
    bitsPerSample: int = 0
    samples: bytes = b""

    length: int = data.Length
    pos: int = 12
    while pos + 8 <= length:
        chunkId: str = _readFourCC(data, pos)
        chunkSize: int = zipfile._readU32LE(data, pos + 4)
        chunkDataStart: int = pos + 8

        if chunkId == "fmt ":
            numChannels = zipfile._readU16LE(data, chunkDataStart + 2)
            sampleRate = zipfile._readU32LE(data, chunkDataStart + 4)
            bitsPerSample = zipfile._readU16LE(data, chunkDataStart + 14)
        elif chunkId == "data":
            sampleBuf: RemObjects.Elements.RTL.Binary = RemObjects.Elements.RTL.Binary()
            j: int = 0
            while j < chunkSize:
                oneByte2: bytes = b"\x00"
                oneByte2[0] = data[chunkDataStart + j]
                sampleBuf.Write(oneByte2)
                j += 1
            samples = sampleBuf.ToArray()

        pos = chunkDataStart + chunkSize
        if chunkSize % 2 == 1:
            pos += 1

    return WavInfo(numChannels, sampleRate, bitsPerSample, samples)

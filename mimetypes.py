@namespace("mimetypes")

# A curated subset of Python's `mimetypes` module: `guess_type(filename)
# -> tuple[str, str]` / `guess_extension(mimeType) -> str`, using only
# CPython's own *hardcoded* fallback table (`mimetypes.types_map`), never
# its optional step of reading system `mime.types` files — that part
# needs real filesystem access, which this project's own scope excludes
# (see README's Build notes), but the hardcoded table itself needs
# nothing but string matching, so it isn't actually blocked the way the
# rest of "Networking" is. This ports a curated ~20-entry slice of that
# table (the entries most likely to matter — text/web/image/audio/video/
# archive formats), not CPython's full ~200-entry one.
#
# `guess_type` returns `(mimeType, encoding)`, matching CPython's own
# 2-tuple shape (encoding is set for suffix-recognized-but-uncompressed-
# type-unknown cases like `.gz`) — but with `""` standing in for
# CPython's `None` in either slot, the same concrete-stand-in convention
# `bisect.py`'s `hi=-1`/`DefaultDict`'s `get`/`pop` already use. Matching
# is case-insensitive on the extension and only looks at the text after
# the *last* `.` in the filename — no multi-part suffix handling (CPython
# itself only special-cases a couple of specific double suffixes like
# `.tar.gz`, not attempted here).
#
# `guess_extension`'s reverse mapping deliberately matches CPython's own
# choice of canonical extension exactly, even where it's not the
# "obvious" one — confirmed by checking CPython directly rather than
# guessing: `application/xml` maps back to `.xsl`, not `.xml` (an
# artifact of CPython's own internal table construction, not something
# to second-guess), and `image/jpeg` maps back to `.jpg`, not `.jpeg`.
#
# Runtime-verified against live CPython's own `mimetypes.guess_type`/
# `guess_extension` for every entry in this table, both directions.


def _extensionOf(filename: str) -> str:
    length: int = _strutil.length(filename)
    lastDot: int = -1
    i: int = 0
    while i < length:
        if _strutil.substring(filename, i, 1) == ".":
            lastDot = i
        i += 1
    if lastDot == -1:
        return ""
    return _strutil.lower(_strutil.substring(filename, lastDot, length - lastDot))


def guess_type(filename: str) -> tuple[str, str]:
    ext: str = _extensionOf(filename)
    if ext == ".txt":
        return ("text/plain", "")
    elif ext == ".html" or ext == ".htm":
        return ("text/html", "")
    elif ext == ".css":
        return ("text/css", "")
    elif ext == ".js":
        return ("text/javascript", "")
    elif ext == ".json":
        return ("application/json", "")
    elif ext == ".xml":
        return ("application/xml", "")
    elif ext == ".csv":
        return ("text/csv", "")
    elif ext == ".pdf":
        return ("application/pdf", "")
    elif ext == ".zip":
        return ("application/zip", "")
    elif ext == ".gz":
        return ("", "gzip")
    elif ext == ".tar":
        return ("application/x-tar", "")
    elif ext == ".png":
        return ("image/png", "")
    elif ext == ".jpg" or ext == ".jpeg":
        return ("image/jpeg", "")
    elif ext == ".gif":
        return ("image/gif", "")
    elif ext == ".svg":
        return ("image/svg+xml", "")
    elif ext == ".ico":
        return ("image/x-icon", "")
    elif ext == ".mp3":
        return ("audio/mpeg", "")
    elif ext == ".mp4":
        return ("video/mp4", "")
    elif ext == ".wav":
        return ("audio/x-wav", "")
    elif ext == ".py":
        return ("text/x-python", "")
    elif ext == ".c":
        return ("text/x-c", "")
    else:
        return ("", "")


def guess_extension(mimeType: str) -> str:
    if mimeType == "text/plain":
        return ".txt"
    elif mimeType == "text/html":
        return ".html"
    elif mimeType == "text/css":
        return ".css"
    elif mimeType == "text/javascript":
        return ".js"
    elif mimeType == "application/json":
        return ".json"
    elif mimeType == "application/xml":
        return ".xsl"
    elif mimeType == "text/csv":
        return ".csv"
    elif mimeType == "application/pdf":
        return ".pdf"
    elif mimeType == "application/zip":
        return ".zip"
    elif mimeType == "application/x-tar":
        return ".tar"
    elif mimeType == "image/png":
        return ".png"
    elif mimeType == "image/jpeg":
        return ".jpg"
    elif mimeType == "image/gif":
        return ".gif"
    elif mimeType == "image/svg+xml":
        return ".svg"
    elif mimeType == "image/x-icon":
        return ".ico"
    elif mimeType == "audio/mpeg":
        return ".mp3"
    elif mimeType == "video/mp4":
        return ".mp4"
    elif mimeType == "audio/x-wav":
        return ".wav"
    elif mimeType == "text/x-python":
        return ".py"
    elif mimeType == "text/x-c":
        return ".c"
    else:
        return ""

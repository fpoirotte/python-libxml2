#define quote "
#define f(x) x
#define tquote f(quote)f(quote)f(quote)

[config]
/*
    The following multi-line string is used to store whatever
    gets returned by <libxml/xmlversion.h> when included.
*/
_dummy = tquote
; See the comments in libxml2-config.h for more information
#include <libxml/xmlversion.h>
tquote

version = LIBXML_DOTTED_VERSION

#ifdef LIBXML_THREAD_ENABLED
with_threads = true
#else
with_threads = false
#endif

#ifdef LIBXML_ICONV_ENABLED
with_iconv = true
#else
with_iconv = false
#endif

#ifdef LIBXML_ZLIB_ENABLED
with_zlib = true
#else
with_zlib = false
#endif

#ifdef LIBXML_LZMA_ENABLED
with_lzma = true
#else
with_lzma = false
#endif

#ifdef LIBXML_ICU_ENABLED
with_icu = true
#else
with_icu = false
#endif

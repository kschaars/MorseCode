find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_BINARY_DECODER gnuradio-Binary_Decoder)

FIND_PATH(
    GR_BINARY_DECODER_INCLUDE_DIRS
    NAMES gnuradio/Binary_Decoder/api.h
    HINTS $ENV{BINARY_DECODER_DIR}/include
        ${PC_BINARY_DECODER_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_BINARY_DECODER_LIBRARIES
    NAMES gnuradio-Binary_Decoder
    HINTS $ENV{BINARY_DECODER_DIR}/lib
        ${PC_BINARY_DECODER_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-Binary_DecoderTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_BINARY_DECODER DEFAULT_MSG GR_BINARY_DECODER_LIBRARIES GR_BINARY_DECODER_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_BINARY_DECODER_LIBRARIES GR_BINARY_DECODER_INCLUDE_DIRS)

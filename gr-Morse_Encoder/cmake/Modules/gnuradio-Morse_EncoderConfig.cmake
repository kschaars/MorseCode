find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_MORSE_ENCODER gnuradio-Morse_Encoder)

FIND_PATH(
    GR_MORSE_ENCODER_INCLUDE_DIRS
    NAMES gnuradio/Morse_Encoder/api.h
    HINTS $ENV{MORSE_ENCODER_DIR}/include
        ${PC_MORSE_ENCODER_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_MORSE_ENCODER_LIBRARIES
    NAMES gnuradio-Morse_Encoder
    HINTS $ENV{MORSE_ENCODER_DIR}/lib
        ${PC_MORSE_ENCODER_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-Morse_EncoderTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_MORSE_ENCODER DEFAULT_MSG GR_MORSE_ENCODER_LIBRARIES GR_MORSE_ENCODER_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_MORSE_ENCODER_LIBRARIES GR_MORSE_ENCODER_INCLUDE_DIRS)

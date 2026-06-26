cmake_minimum_required(VERSION 3.20)
include("C:/Program Files/CMake/bin/ewdk.cmake")

project(x64dbg_mcp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# nlohmann_json (header-only, bundled)
add_library(nlohmann_json INTERFACE)
target_include_directories(nlohmann_json INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# Source files (auto-discovered, ewdk templates handle unity build automatically)
file(GLOB_RECURSE PLUGIN_SOURCES src/*.cpp)

# ============================================================
# x64dbg_mcp - x64dbg Plugin (x64)
# ============================================================
um_dp64(x64dbg_mcp
    SOURCES ${PLUGIN_SOURCES}
    INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/src
    LINK_LIBS nlohmann_json ws2_32 dbghelp comctl32
    DEFINES _CRT_SECURE_NO_WARNINGS NOMINMAX WIN32_LEAN_AND_MEAN BUILD_PLUGIN
    EXTRA_SOURCES src/plugin.def
)

# ============================================================
# x64dbg_mcp - x32dbg Plugin (x86)
# ============================================================
um_dp86(x64dbg_mcp
    SOURCES ${PLUGIN_SOURCES}
    INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/src
    LINK_LIBS ws2_32.lib dbghelp.lib comctl32.lib "/DEF:${CMAKE_CURRENT_SOURCE_DIR}/src/plugin.def"
    DEFINES _CRT_SECURE_NO_WARNINGS NOMINMAX WIN32_LEAN_AND_MEAN BUILD_PLUGIN
)

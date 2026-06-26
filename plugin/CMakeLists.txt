cmake_minimum_required(VERSION 3.20)
include("C:/Program Files/CMake/bin/ewdk.cmake")
include("C:/Program Files/CMake/bin/unity.cmake")

project(x64dbg_mcp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Collect all plugin sources
collect_sources(
    src/bridge src/handlers src/http src/ui src/util
    PLUGIN_SOURCES
)
file(GLOB _root_src "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")
list(APPEND PLUGIN_SOURCES ${_root_src})

# Generate unity.cpp — 合并所有源文件到一个编译单元，编译速度翻 29 倍
generate_unity(unity ${PLUGIN_SOURCES})

# nlohmann_json (header-only, bundled)
add_library(nlohmann_json INTERFACE)
target_include_directories(nlohmann_json INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# ============================================================
# x64dbg_mcp - x64dbg Plugin (x64)
# ============================================================
um_dp64(x64dbg_mcp
    SOURCES ${UNITY_FILE}
    INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/src
    LINK_LIBS nlohmann_json ws2_32 dbghelp comctl32
    DEFINES _CRT_SECURE_NO_WARNINGS NOMINMAX WIN32_LEAN_AND_MEAN BUILD_PLUGIN
    EXTRA_SOURCES src/plugin.def
)

# ============================================================
# x64dbg_mcp - x32dbg Plugin (x86)
# ============================================================
um_dp86(x64dbg_mcp
    SOURCES ${UNITY_FILE}
    INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/src
    LINK_LIBS ws2_32.lib dbghelp.lib comctl32.lib "/DEF:${CMAKE_CURRENT_SOURCE_DIR}/src/plugin.def"
    DEFINES _CRT_SECURE_NO_WARNINGS NOMINMAX WIN32_LEAN_AND_MEAN BUILD_PLUGIN
)

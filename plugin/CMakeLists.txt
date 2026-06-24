cmake_minimum_required(VERSION 3.20)
include("${CMAKE_CURRENT_SOURCE_DIR}/ewdk.cmake")

project(x64dbg_mcp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# nlohmann_json (header-only, bundled)
add_library(nlohmann_json INTERFACE)
target_include_directories(nlohmann_json INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# Source files
set(PLUGIN_SOURCES
    src/plugin_main.cpp
    src/http/c_http_server.cpp
    src/http/c_http_router.cpp
    src/bridge/c_bridge_executor.cpp
    src/util/format_utils.cpp
    src/handlers/debug_handler.cpp
    src/handlers/register_handler.cpp
    src/handlers/memory_handler.cpp
    src/handlers/breakpoint_handler.cpp
    src/handlers/disasm_handler.cpp
    src/handlers/module_handler.cpp
    src/handlers/thread_handler.cpp
    src/handlers/stack_handler.cpp
    src/handlers/symbol_handler.cpp
    src/handlers/annotation_handler.cpp
    src/handlers/search_handler.cpp
    src/handlers/patch_handler.cpp
    src/handlers/memmap_handler.cpp
    src/handlers/command_handler.cpp
    src/handlers/analysis_handler.cpp
    src/handlers/tracing_handler.cpp
    src/handlers/dumping_handler.cpp
    src/handlers/antidebug_handler.cpp
    src/handlers/exceptions_handler.cpp
    src/handlers/process_handler.cpp
    src/handlers/handles_handler.cpp
    src/handlers/controlflow_handler.cpp
    src/ui/settings_dialog.cpp
    src/ui/about_dialog.cpp
)

# ============================================================
# x64dbg_mcp - x64dbg Plugin (x64)
# ============================================================
add_library(x64dbg_mcp SHARED ${PLUGIN_SOURCES} src/plugin.def)
set_target_properties(x64dbg_mcp PROPERTIES SUFFIX ".dp64")
set_target_properties(x64dbg_mcp PROPERTIES
    CXX_STANDARD 23
    MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>"
)
target_include_directories(x64dbg_mcp PRIVATE
    ${WDK_UM_INCLUDE_DIRS}
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}
)
target_include_directories(x64dbg_mcp SYSTEM PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/pluginsdk
)
target_compile_definitions(x64dbg_mcp PRIVATE
    _CRT_SECURE_NO_WARNINGS
    NOMINMAX
    WIN32_LEAN_AND_MEAN
    BUILD_PLUGIN
)
target_compile_options(x64dbg_mcp PRIVATE /utf-8 /EHsc)
foreach(_lib_dir ${WDK_UM_LIB_DIRS})
    target_link_directories(x64dbg_mcp PRIVATE "${_lib_dir}")
endforeach()
target_link_directories(x64dbg_mcp PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(x64dbg_mcp
    nlohmann_json
    pluginsdk/x64bridge
    pluginsdk/x64dbg
    pluginsdk/jansson/jansson_x64
    ws2_32
    dbghelp
    user32.lib
    gdi32.lib
    comctl32.lib
    shell32.lib
)

# ============================================================
# x64dbg_mcp_x86 - x32dbg Plugin (x86)
# ============================================================
um_dll_x86(x64dbg_mcp_x86
    SOURCES ${PLUGIN_SOURCES}
    INCLUDE_DIRS
        ${WDK_UM_INCLUDE_DIRS_X86}
        ${CMAKE_CURRENT_SOURCE_DIR}/src
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}/pluginsdk
    LINK_DIRS
        ${WDK_UM_LIB_DIRS_X86}
        ${CMAKE_CURRENT_SOURCE_DIR}
    LINK_LIBS
        pluginsdk/x32bridge.lib
        pluginsdk/x32dbg.lib
        pluginsdk/jansson/jansson_x86.lib
        ws2_32.lib
        dbghelp.lib
        user32.lib
        gdi32.lib
        comctl32.lib
        shell32.lib
        "/DEF:${CMAKE_CURRENT_SOURCE_DIR}/src/plugin.def"
    DEFINITIONS
        _CRT_SECURE_NO_WARNINGS
        NOMINMAX
        WIN32_LEAN_AND_MEAN
        BUILD_PLUGIN
)

# ─── 从注册表读取 x64dbg 路径，复制插件到 plugins 目录 ───
execute_process(
    COMMAND powershell -NoLogo -NoProfile -Command
        "(Get-ItemPropertyValue 'Registry::HKEY_CLASSES_ROOT\\.dd32\\DefaultIcon' '(Default)')"
    OUTPUT_VARIABLE _X32
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
execute_process(
    COMMAND powershell -NoLogo -NoProfile -Command
        "(Get-ItemPropertyValue 'Registry::HKEY_CLASSES_ROOT\\.dd64\\DefaultIcon' '(Default)')"
    OUTPUT_VARIABLE _X64
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
get_filename_component(X64DBG_X32_DIR "${_X32}" DIRECTORY)
get_filename_component(X64DBG_X64_DIR "${_X64}" DIRECTORY)

function(x64dbg_copy_plugin PLUGIN_NAME SOURCE_FILE FILENAME ARCH)
    if(ARCH STREQUAL "x64")
        set(_DST "${X64DBG_X64_DIR}/plugins/${FILENAME}")
    else()
        set(_DST "${X64DBG_X32_DIR}/plugins/${FILENAME}")
    endif()
    add_custom_target(${PLUGIN_NAME}_copy ALL
        COMMAND ${CMAKE_COMMAND} -E make_directory "${X64DBG_X${ARCH}_DIR}/plugins"
        COMMAND powershell -NoLogo -NoProfile -Command
            "if (Test-Path '${SOURCE_FILE}') { Copy-Item -Path '${SOURCE_FILE}' -Destination '${_DST}' -Force; Write-Host '[OK] ${FILENAME} -> ${_DST}' } else { Write-Error '[FAIL] ${FILENAME} not found: ${SOURCE_FILE}'; exit 1 }"
        DEPENDS ${PLUGIN_NAME}
        COMMENT "Copy ${FILENAME} -> plugins/${ARCH}"
    )
endfunction()

x64dbg_copy_plugin(x64dbg_mcp     "${CMAKE_CURRENT_BINARY_DIR}/x64dbg_mcp.dp64"   "x64dbg_mcp.dp64" x64)
x64dbg_copy_plugin(x64dbg_mcp_x86 "${CMAKE_CURRENT_BINARY_DIR}/x64dbg_mcp_x86.dp32" "x64dbg_mcp.dp32" x32)

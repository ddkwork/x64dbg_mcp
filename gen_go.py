#!/usr/bin/env python3
"""Generate Go client code from TS tool definition files."""

import os
import re
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "servergo"

# ─── Endpoint → Go response type mapping ─────────────────────────────────
ENDPOINT_RESPONSE_TYPES: dict[str, str] = {
    "/api/debug/state":            "DebugState",
    "/api/debug/run":              "StatusMsg",
    "/api/debug/pause":            "StatusMsg",
    "/api/debug/step_into":        "StepResult",
    "/api/debug/step_over":        "StepResult",
    "/api/debug/step_out":         "StepResult",
    "/api/debug/stop":             "StatusMsg",
    "/api/debug/restart":          "StatusMsg",
    "/api/debug/run_to":           "StatusMsg",
    "/api/debug/force_pause":      "StatusMsg",
    "/api/registers/all":          "map[string]any",
    "/api/registers/flags":        "map[string]string",
    "/api/registers/avx512":       "map[string]string",
    "/api/registers/get":          "map[string]string",
    "/api/registers/set":          "StatusMsg",
    "/api/memory/read":            "MemoryReadData",
    "/api/memory/write":           "MemoryWriteData",
    "/api/memory/page_info":       "PageInfo",
    "/api/memory/is_valid":        "MemoryValid",
    "/api/memory/is_code":         "MemoryValid",
    "/api/memory/allocate":        "MemoryAlloc",
    "/api/memory/free":            "StatusMsg",
    "/api/memory/protect":         "StatusMsg",
    "/api/memory/update_map":      "StatusMsg",
    "/api/memmap/list":            "MemMapList",
    "/api/memmap/at":              "map[string]string",
    "/api/breakpoints/list":       "BpListData",
    "/api/breakpoints/get":        "BpItem",
    "/api/breakpoints/set":        "BpSetData",
    "/api/breakpoints/set_hardware": "BpSetData",
    "/api/breakpoints/set_memory":  "BpSetData",
    "/api/breakpoints/delete":     "StatusMsg",
    "/api/breakpoints/enable":     "StatusMsg",
    "/api/breakpoints/disable":    "StatusMsg",
    "/api/breakpoints/toggle":     "StatusMsg",
    "/api/breakpoints/set_condition": "StatusMsg",
    "/api/breakpoints/set_log":    "StatusMsg",
    "/api/breakpoints/configure":  "StatusMsg",
    "/api/breakpoints/reset_hit_count": "StatusMsg",
    "/api/disasm/at":              "DisasmResult",
    "/api/disasm/function":        "DisasmFunctionResult",
    "/api/disasm/basic":           "DisasmBasicInfo",
    "/api/disasm/assemble":        "AssembleResult",
    "/api/stack/trace":            "CallStack",
    "/api/stack/callstack_thread": "CallStack",
    "/api/stack/read":             "StackReadData",
    "/api/stack/pointers":         "map[string]string",
    "/api/stack/seh_chain":        "map[string]string",
    "/api/stack/return_address":   "map[string]string",
    "/api/stack/comment":          "map[string]string",
    "/api/modules/list":           "ModuleList",
    "/api/modules/get":            "map[string]string",
    "/api/modules/base":           "map[string]string",
    "/api/modules/section":        "map[string]string",
    "/api/modules/party":          "map[string]string",
    "/api/symbols/resolve":        "map[string]string",
    "/api/symbols/at":             "map[string]string",
    "/api/symbols/search":         "SymbolSearchResult",
    "/api/symbols/list":           "SymbolList",
    "/api/labels/get":             "map[string]string",
    "/api/labels/set":             "StatusMsg",
    "/api/comments/get":           "map[string]string",
    "/api/comments/set":           "StatusMsg",
    "/api/bookmarks/set":          "StatusMsg",
    "/api/command/exec":           "CommandResult",
    "/api/command/script":         "CommandResult",
    "/api/command/eval":           "EvalResult",
    "/api/command/format":         "FormatResult",
    "/api/command/init_script":    "StatusMsg",
    "/api/command/hash":           "map[string]string",
    "/api/command/events":         "EventsResult",
    "/api/process/info":           "ProcessBasicInfo",
    "/api/process/details":        "ProcessDetails",
    "/api/process/cmdline":        "map[string]string",
    "/api/process/set_cmdline":    "StatusMsg",
    "/api/process/elevated":       "map[string]string",
    "/api/process/dbversion":      "map[string]string",
    "/api/threads/list":           "ThreadList",
    "/api/threads/current":        "map[string]string",
    "/api/threads/count":          "ThreadCount",
    "/api/threads/get":            "map[string]string",
    "/api/threads/teb":            "map[string]string",
    "/api/threads/name":           "map[string]string",
    "/api/threads/switch":         "StatusMsg",
    "/api/threads/suspend":        "StatusMsg",
    "/api/threads/resume":         "StatusMsg",
    "/api/exceptions/set_bp":      "StatusMsg",
    "/api/exceptions/delete_bp":   "StatusMsg",
    "/api/exceptions/list_bps":    "map[string]string",
    "/api/exceptions/list_codes":  "map[string]any",
    "/api/exceptions/skip":        "StatusMsg",
    "/api/handles/list":           "HandleList",
    "/api/handles/tcp":            "map[string]string",
    "/api/handles/windows":        "map[string]string",
    "/api/handles/heaps":          "map[string]string",
    "/api/handles/get":            "map[string]string",
    "/api/handles/close":          "StatusMsg",
    "/api/search/pattern":         "PatternResult",
    "/api/search/string":          "StringSearchResult",
    "/api/search/string_at":       "StringAtResult",
    "/api/search/auto_complete":   "AutoCompleteResult",
    "/api/search/encode_type":     "map[string]any",
    "/api/analysis/function":      "map[string]string",
    "/api/analysis/xrefs_to":      "XrefList",
    "/api/analysis/xrefs_from":    "XrefList",
    "/api/analysis/basic_blocks":  "BasicBlockList",
    "/api/analysis/source":        "map[string]string",
    "/api/analysis/mnemonic_brief":"map[string]string",
    "/api/analysis/constants":     "map[string]string",
    "/api/analysis/error_codes":   "map[string]string",
    "/api/analysis/structs":       "map[string]string",
    "/api/analysis/strings":       "map[string]string",
    "/api/analysis/va_to_file":    "map[string]any",
    "/api/analysis/file_to_va":    "map[string]string",
    "/api/analysis/watch":         "map[string]string",
    "/api/trace/into":             "map[string]string",
    "/api/trace/over":             "map[string]string",
    "/api/trace/run":              "StatusMsg",
    "/api/trace/stop":             "StatusMsg",
    "/api/trace/status":           "TraceStatus",
    "/api/trace/animate":          "map[string]string",
    "/api/trace/conditional_run":  "map[string]string",
    "/api/trace/log":              "StatusMsg",
    "/api/trace/record/hitcount":  "map[string]string",
    "/api/trace/record/type":      "map[string]string",
    "/api/trace/record/set_type":  "StatusMsg",
    "/api/dump/pe_header":         "map[string]string",
    "/api/dump/sections":          "map[string]string",
    "/api/dump/imports":           "map[string]string",
    "/api/dump/exports":           "map[string]string",
    "/api/dump/entry_point":       "map[string]string",
    "/api/dump/relocations":       "map[string]string",
    "/api/dump/module":            "map[string]string",
    "/api/dump/fix_iat":           "map[string]string",
    "/api/patches/list":           "PatchList",
    "/api/patches/apply":          "StatusMsg",
    "/api/patches/restore":        "StatusMsg",
    "/api/patches/export":         "StatusMsg",
    "/api/patches/export_file":    "StatusMsg",
    "/api/antidebug/peb":          "map[string]string",
    "/api/antidebug/teb":          "map[string]string",
    "/api/antidebug/dep_status":   "map[string]any",
    "/api/antidebug/hide_debugger":"StatusMsg",
    "/api/cfg/function":           "map[string]string",
    "/api/cfg/branch_dest":        "map[string]any",
    "/api/cfg/is_jump_taken":      "map[string]any",
    "/api/cfg/loops":              "map[string]string",
    "/api/cfg/func_type":          "map[string]any",
    "/api/cfg/add_function":       "StatusMsg",
    "/api/cfg/delete_function":    "StatusMsg",
    "/api/health":                 "HealthData",
}

# ─── Tool actions ────────────────────────────────────────────────────────
# Format: (action_name, method, endpoint, body_type_name, has_body, get_params)

TOOL_ACTIONS: dict[str, list[tuple]] = {
    "debug": [
        ("run",        "POST", "/api/debug/run",          None, False, None),
        ("pause",      "POST", "/api/debug/pause",        None, False, None),
        ("force_pause","POST", "/api/debug/force_pause",  None, False, None),
        ("get_state",  "GET",  "/api/debug/state",        None, False, None),
        ("step_into",  "POST", "/api/debug/step_into",    None, False, None),
        ("step_over",  "POST", "/api/debug/step_over",    None, False, None),
        ("step_out",   "POST", "/api/debug/step_out",     None, False, None),
        ("stop_debug", "POST", "/api/debug/stop",         None, False, None),
        ("restart_debug", "POST", "/api/debug/restart",   None, False, None),
        ("run_to_address","POST", "/api/debug/run_to",
         "struct{Address string `json:\"address\"`}", True, None),
    ],
    "registers": [
        ("get_all",    "GET",  "/api/registers/all",      None, False, None),
        ("get_flags",  "GET",  "/api/registers/flags",    None, False, None),
        ("get_avx512", "GET",  "/api/registers/avx512",   None, False, None),
        ("get_specific","GET", "/api/registers/get",      None, False, ["name"]),
        ("set_reg",    "POST", "/api/registers/set",
         "struct{Name string `json:\"name\"`; Value string `json:\"value\"`}", True, None),
    ],
    "memory": [
        ("read",       "GET",  "/api/memory/read",        None, False, ["address", "size"]),
        ("write",      "POST", "/api/memory/write",
         "struct{Address string `json:\"address\"`; Bytes string `json:\"bytes\"`; Verify bool `json:\"verify,omitempty\"`}", True, None),
        ("page_info",  "GET",  "/api/memory/page_info",   None, False, ["address"]),
        ("is_valid",   "GET",  "/api/memory/is_valid",    None, False, ["address"]),
        ("is_code",    "GET",  "/api/memory/is_code",     None, False, ["address"]),
        ("allocate",   "POST", "/api/memory/allocate",
         "struct{Size string `json:\"size\"`}", True, None),
        ("free",       "POST", "/api/memory/free",
         "struct{Address string `json:\"address\"`}", True, None),
        ("protect",    "POST", "/api/memory/protect",
         "struct{Address string `json:\"address\"`; Size string `json:\"size\"`; Protection string `json:\"protection\"`}", True, None),
        ("update_map", "POST", "/api/memory/update_map",  None, False, None),
    ],
    "breakpoints": [
        ("set_software",   "POST", "/api/breakpoints/set",           "BpSetSoftwareReq", True, None),
        ("set_hardware",   "POST", "/api/breakpoints/set_hardware",  "BpSetHardwareReq", True, None),
        ("set_memory",     "POST", "/api/breakpoints/set_memory",    "BpSetMemoryReq", True, None),
        ("bp_delete",      "POST", "/api/breakpoints/delete",        "BpDeleteReq", True, None),
        ("enable",         "POST", "/api/breakpoints/enable",        "BpAddrReq", True, None),
        ("disable",        "POST", "/api/breakpoints/disable",       "BpAddrReq", True, None),
        ("toggle",         "POST", "/api/breakpoints/toggle",        "BpAddrReq", True, None),
        ("set_condition",  "POST", "/api/breakpoints/set_condition", "BpConditionReq", True, None),
        ("set_log",        "POST", "/api/breakpoints/set_log",       "BpLogReq", True, None),
        ("reset_hit_count","POST", "/api/breakpoints/reset_hit_count","BpAddrReq", True, None),
        ("get_bp",         "GET",  "/api/breakpoints/get",           None, False, ["address"]),
        ("list_bps",       "GET",  "/api/breakpoints/list",          None, False, None),
        ("configure_bp",   "POST", "/api/breakpoints/configure",     "BpConfigureReq", True, None),
    ],
    "disassembly": [
        ("at_address",  "GET",  "/api/disasm/at",         None, False, ["address", "count"]),
        ("disasm_func", "GET",  "/api/disasm/function",    None, False, ["address", "max_instructions"]),
        ("disasm_basic_info",  "GET",  "/api/disasm/basic",       None, False, ["address"]),
        ("assemble",    "POST", "/api/disasm/assemble",    "DisasmAssembleReq", True, None),
    ],
    "stack": [
        ("get_call_stack", "GET", "/api/stack/trace",       None, False, ["max_depth"]),
        ("read_stack",     "GET", "/api/stack/read",        None, False, ["address", "size"]),
        ("pointers",       "GET", "/api/stack/pointers",    None, False, None),
        ("seh_chain",      "GET", "/api/stack/seh_chain",   None, False, None),
        ("return_address", "GET", "/api/stack/return_address",None, False, None),
        ("stack_comment",  "GET", "/api/stack/comment",     None, False, ["address"]),
    ],
    "modules": [
        ("list_modules", "GET", "/api/modules/list",         None, False, None),
        ("get_info", "GET", "/api/modules/get",              None, False, ["name"]),
        ("get_base", "GET", "/api/modules/base",             None, False, ["name"]),
        ("get_section","GET","/api/modules/section",         None, False, ["address"]),
        ("get_party","GET", "/api/modules/party",            None, False, ["base"]),
    ],
    "symbols": [
        ("resolve",    "GET", "/api/symbols/resolve",        None, False, ["name"]),
        ("sym_at", "GET", "/api/symbols/at",                  None, False, ["address"]),
        ("search_sym", "GET", "/api/symbols/search",         None, False, ["pattern", "module"]),
        ("list_module","GET", "/api/symbols/list",           None, False, ["module"]),
        ("get_label",  "GET", "/api/labels/get",             None, False, ["address"]),
        ("set_label",  "POST","/api/labels/set",             "LabelSetReq", True, None),
        ("get_comment","GET", "/api/comments/get",           None, False, ["address"]),
        ("set_comment","POST","/api/comments/set",           "CommentSetReq", True, None),
        ("bookmark",   "POST","/api/bookmarks/set",          "BookmarkSetReq", True, None),
    ],
    "command": [
        ("execute",      "POST", "/api/command/exec",        "struct{Command string `json:\"command\"`}", True, None),
        ("script",       "POST", "/api/command/script",      "struct{Commands []string `json:\"commands\"`}", True, None),
        ("evaluate",     "POST", "/api/command/eval",        "struct{Expression string `json:\"expression\"`}", True, None),
        ("format",       "POST", "/api/command/format",      "struct{Format string `json:\"format\"`}", True, None),
        ("set_init_script","POST","/api/command/init_script","struct{File string `json:\"file\"`}", True, None),
        ("get_init_script","GET","/api/command/init_script",  None, False, None),
        ("get_hash",     "GET",  "/api/command/hash",        None, False, None),
        ("get_events",   "GET",  "/api/command/events",      None, False, None),
    ],
    "process": [
        ("basic_info",    "GET", "/api/process/info",        None, False, None),
        ("detailed",      "GET", "/api/process/details",     None, False, None),
        ("cmdline",       "GET", "/api/process/cmdline",     None, False, None),
        ("elevated",      "GET", "/api/process/elevated",    None, False, None),
        ("dbversion",     "GET", "/api/process/dbversion",   None, False, None),
        ("set_cmdline",   "POST","/api/process/set_cmdline", "struct{Cmdline string `json:\"cmdline\"`}", True, None),
    ],
    "threads": [
        ("list_threads","GET",  "/api/threads/list",         None, False, None),
        ("current",    "GET",  "/api/threads/current",      None, False, None),
        ("count",      "GET",  "/api/threads/count",        None, False, None),
        ("get_thread", "GET",  "/api/threads/get",          None, False, ["id"]),
        ("thread_teb", "GET",  "/api/threads/teb",          None, False, ["tid"]),
        ("thread_name","GET",  "/api/threads/name",         None, False, ["tid"]),
        ("switch",     "POST", "/api/threads/switch",       "IdReq", True, None),
        ("suspend",    "POST", "/api/threads/suspend",       "IdReq", True, None),
        ("resume",     "POST", "/api/threads/resume",        "IdReq", True, None),
    ],
    "exceptions": [
        ("set_exc",      "POST", "/api/exceptions/set_bp",    "struct{Code string `json:\"code\"`; Chance string `json:\"chance\"`}", True, None),
        ("del_exc",      "POST", "/api/exceptions/delete_bp", "struct{Code string `json:\"code\"`}", True, None),
        ("list_exc",     "GET",  "/api/exceptions/list_bps",  None, False, None),
        ("list_codes",   "GET",  "/api/exceptions/list_codes",None, False, None),
        ("skip_exc",     "POST", "/api/exceptions/skip",      None, False, None),
    ],
    "handles": [
        ("list_handles","GET", "/api/handles/list",           None, False, None),
        ("list_tcp",   "GET",  "/api/handles/tcp",            None, False, None),
        ("list_windows","GET", "/api/handles/windows",        None, False, None),
        ("list_heaps", "GET",  "/api/handles/heaps",          None, False, None),
        ("get_name",   "GET",  "/api/handles/get",            None, False, ["handle"]),
        ("close_handle","POST","/api/handles/close",          "struct{Handle string `json:\"handle\"`}", True, None),
    ],
    "search": [
        ("pattern",          "POST", "/api/search/pattern",           "SearchPatternReq", True, None),
        ("search_string",    "POST", "/api/search/string",            "SearchStringReq", True, None),
        ("string_at",        "GET",  "/api/search/string_at",         None, False, ["address", "encoding", "max_length"]),
        ("symbol_auto_complete","POST","/api/search/auto_complete",   "SearchAutoCompleteReq", True, None),
        ("encode_type",      "GET",  "/api/search/encode_type",       None, False, ["address", "size"]),
    ],
    "analysis": [
        ("function",    "GET",  "/api/analysis/function",     None, False, ["address"]),
        ("xrefs_to",    "GET",  "/api/analysis/xrefs_to",    None, False, ["address"]),
        ("xrefs_from",  "GET",  "/api/analysis/xrefs_from",  None, False, ["address"]),
        ("basic_blocks","GET",  "/api/analysis/basic_blocks",None, False, ["address"]),
        ("source",      "GET",  "/api/analysis/source",      None, False, ["address"]),
        ("mnemonic_brief","GET","/api/analysis/mnemonic_brief",None, False, ["mnemonic"]),
    ],
    "database": [
        ("constants",  "GET",  "/api/analysis/constants",     None, False, None),
        ("error_codes","GET",  "/api/analysis/error_codes",   None, False, None),
        ("structs",    "GET",  "/api/analysis/structs",       None, False, None),
        ("strings",    "GET",  "/api/analysis/strings",       None, False, ["module"]),
    ],
    "address_convert": [
        ("va_to_file", "GET", "/api/analysis/va_to_file",     None, False, ["address"]),
        ("file_to_va", "GET", "/api/analysis/file_to_va",     None, False, ["module", "offset"]),
    ],
    "tracing": [
        ("trace_into",        "POST", "/api/trace/into",               "TraceIntoReq", True, None),
        ("trace_over",        "POST", "/api/trace/over",               "TraceOverReq", True, None),
        ("trace_run",         "POST", "/api/trace/run",                 "struct{Party string `json:\"party\"`}", True, None),
        ("trace_stop",        "POST", "/api/trace/stop",                None, False, None),
        ("trace_status",      "GET",  "/api/trace/status",             None, False, None),
        ("animate",           "POST", "/api/trace/animate",            "struct{Command string `json:\"command\"`}", True, None),
        ("conditional_run",   "POST", "/api/trace/conditional_run",     "TraceConditionalRunReq", True, None),
        ("log_setup",         "POST", "/api/trace/log",                "TraceLogReq", True, None),
        ("hitcount",          "GET",  "/api/trace/record/hitcount",    None, False, ["address"]),
        ("trace_type",        "GET",  "/api/trace/record/type",        None, False, ["address"]),
        ("set_trace_type",    "POST", "/api/trace/record/set_type",    "struct{Address string `json:\"address\"`; Type int `json:\"type\"`}", True, None),
    ],
    "dumping": [
        ("pe_header",   "GET",  "/api/dump/pe_header",        None, False, ["address"]),
        ("sections",    "GET",  "/api/dump/sections",         None, False, ["module"]),
        ("imports",     "GET",  "/api/dump/imports",          None, False, ["module"]),
        ("exports",     "GET",  "/api/dump/exports",          None, False, ["module"]),
        ("entry_point", "GET",  "/api/dump/entry_point",      None, False, ["module"]),
        ("relocations", "GET",  "/api/dump/relocations",      None, False, ["address"]),
        ("dump_module", "POST", "/api/dump/module",           "struct{Module string `json:\"module\"`; File string `json:\"file\"`}", True, None),
        ("fix_iat",     "POST", "/api/dump/fix_iat",          "struct{OEP string `json:\"oep\"`}", True, None),
    ],
    "patches": [
        ("list_patches","GET",  "/api/patches/list",           None, False, None),
        ("apply",       "POST", "/api/patches/apply",          "struct{Address string `json:\"address\"`; Bytes string `json:\"bytes\"`}", True, None),
        ("restore",     "POST", "/api/patches/restore",        "struct{Address string `json:\"address\"`}", True, None),
        ("export_patch","POST", "/api/patches/export",         "struct{Module string `json:\"module,omitempty\"`; Path string `json:\"path\"`}", True, None),
    ],
    "antidebug": [
        ("peb",          "GET",  "/api/antidebug/peb",         None, False, ["pid"]),
        ("teb",          "GET",  "/api/antidebug/teb",         None, False, ["tid"]),
        ("dep",          "GET",  "/api/antidebug/dep_status",  None, False, None),
        ("hide_debugger","POST", "/api/antidebug/hide_debugger", None, False, None),
    ],
    "controlflow": [
        ("cfg",              "GET",  "/api/cfg/function",         None, False, ["address"]),
        ("branch_dest",      "GET",  "/api/cfg/branch_dest",      None, False, ["address"]),
        ("is_jump_taken",    "GET",  "/api/cfg/is_jump_taken",    None, False, ["address"]),
        ("loops",            "GET",  "/api/cfg/loops",            None, False, ["address"]),
        ("func_type",        "GET",  "/api/cfg/func_type",        None, False, ["address"]),
        ("add_function",     "POST", "/api/cfg/add_function",     "struct{Start string `json:\"start\"`; End string `json:\"end\"`}", True, None),
        ("delete_function",  "POST", "/api/cfg/delete_function",  "struct{Address string `json:\"address\"`}", True, None),
    ],
}

# ─── Go code templates ──────────────────────────────────────────────────

CLIENT_GO = '''// Code generated by gen_go.py - DO NOT EDIT.
package servergo

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"
)

// Client is the HTTP client for the x64dbg MCP plugin REST API.
type Client struct {
    baseURL    string
    httpClient *http.Client
    token      string
}

// NewClient creates a new Client with default settings.
func NewClient(host string, port int, token string) *Client {
    if host == "" { host = "127.0.0.1" }
    if port == 0  { port = 27042 }
    return &Client{
        baseURL:    fmt.Sprintf("http://%s:%d", host, port),
        httpClient: &http.Client{Timeout: 30 * time.Second},
        token:      token,
    }
}

// SetTimeout changes the HTTP client timeout (0 = no timeout).
func (c *Client) SetTimeout(d time.Duration) { c.httpClient.Timeout = d }

func doGET[T any](c *Client, path string, params map[string]string) (T, error) {
    var zero T
    reqURL := c.baseURL + path
    if len(params) > 0 {
        reqURL += "?"
        for k, v := range params {
            if v != "" { reqURL += fmt.Sprintf("%s=%s&", k, v) }
        }
        reqURL = reqURL[:len(reqURL)-1]
    }
    req, err := http.NewRequest("GET", reqURL, nil)
    if err != nil { return zero, fmt.Errorf("NewRequest: %w", err) }
    if c.token != "" { req.Header.Set("Authorization", "Bearer "+c.token) }
    resp, err := c.httpClient.Do(req)
    if err != nil { return zero, fmt.Errorf("http.Do: %w", err) }
    defer resp.Body.Close()
    return parseEnvelope[T](resp)
}

func doPOST[T any](c *Client, path string, body any) (T, error) {
    var zero T
    var bodyReader io.Reader
    if body != nil {
        b, err := json.Marshal(body)
        if err != nil { return zero, fmt.Errorf("json.Marshal: %w", err) }
        bodyReader = bytes.NewReader(b)
    }
    req, err := http.NewRequest("POST", c.baseURL+path, bodyReader)
    if err != nil { return zero, fmt.Errorf("NewRequest: %w", err) }
    if body != nil { req.Header.Set("Content-Type", "application/json") }
    if c.token != "" { req.Header.Set("Authorization", "Bearer "+c.token) }
    resp, err := c.httpClient.Do(req)
    if err != nil { return zero, fmt.Errorf("http.Do: %w", err) }
    defer resp.Body.Close()
    return parseEnvelope[T](resp)
}

func parseEnvelope[T any](resp *http.Response) (T, error) {
    var zero T
    raw, err := io.ReadAll(resp.Body)
    if err != nil { return zero, fmt.Errorf("read body: %w", err) }
    var env struct {
        Success bool             `json:"success"`
        Data    json.RawMessage  `json:"data"`
        Error   *struct {
            Code    int    `json:"code"`
            Message string `json:"message"`
        } `json:"error,omitempty"`
    }
    if err := json.Unmarshal(raw, &env); err != nil {
        return zero, fmt.Errorf("json.Unmarshal envelope: %w (body: %s)", err, string(raw))
    }
    if !env.Success {
        code, msg := 0, "unknown error"
        if env.Error != nil { code = env.Error.Code; msg = env.Error.Message }
        return zero, fmt.Errorf("plugin error (%d): %s", code, msg)
    }
    var data T
    if len(env.Data) > 0 {
        if err := json.Unmarshal(env.Data, &data); err != nil {
            return zero, fmt.Errorf("json.Unmarshal data: %w (body: %s)", err, string(env.Data))
        }
    }
    return data, nil
}
'''

TYPES_GO = '''// Code generated by gen_go.py - DO NOT EDIT.
package servergo

import "encoding/json"

type Envelope struct {
    Success bool             `json:"success"`
    Data    json.RawMessage  `json:"data,omitempty"`
    Error   *struct {
        Code    int    `json:"code"`
        Message string `json:"message"`
    } `json:"error,omitempty"`
}

type StatusMsg struct {
    Message string `json:"message,omitempty"`
}

type StepResult struct {
    CIP     string `json:"cip,omitempty"`
    Message string `json:"message,omitempty"`
}

type DebugState struct {
    CIP    string `json:"cip,omitempty"`
    State  string `json:"state"`
    Module string `json:"module,omitempty"`
    Label  string `json:"label,omitempty"`
}

type MemoryReadData struct {
    Address string `json:"address"`
    Size    int    `json:"size"`
    Hex     string `json:"hex"`
    ASCII   string `json:"ascii"`
}

type MemoryWriteData struct {
    Address      string `json:"address"`
    BytesWritten int    `json:"bytes_written"`
    Verified     bool   `json:"verified,omitempty"`
    VerifyError  string `json:"verify_error,omitempty"`
}

type MemoryValid struct {
    Address string `json:"address"`
    Valid   bool   `json:"valid"`
}

type MemoryAlloc struct {
    Address string `json:"address"`
    Size    string `json:"size"`
}

type PageInfo struct {
    Address    string `json:"address"`
    Size       string `json:"size"`
    Protection string `json:"protection"`
    State      string `json:"state"`
    Type       string `json:"type"`
}

type MemMapEntry struct {
    Address    string `json:"address"`
    Size       string `json:"size"`
    Protection string `json:"protection"`
    State      string `json:"state"`
    Type       string `json:"type"`
    Info       string `json:"info,omitempty"`
    Module     string `json:"module,omitempty"`
    Section    string `json:"section,omitempty"`
}

type MemMapList struct {
    Map   []MemMapEntry `json:"map"`
    Count int           `json:"count"`
}

type BpItem struct {
    Address          string `json:"address"`
    Enabled          bool   `json:"enabled"`
    Active           bool   `json:"active"`
    Singleshot       bool   `json:"singleshoot"`
    Name             string `json:"name"`
    Module           string `json:"module"`
    HitCount         int    `json:"hit_count"`
    FastResume       bool   `json:"fast_resume"`
    Silent           bool   `json:"silent"`
    BreakCondition   string `json:"break_condition"`
    CommandCondition string `json:"command_condition"`
    CommandText      string `json:"command_text"`
    LogText          string `json:"log_text"`
    LogCondition     string `json:"log_condition"`
    Type             int    `json:"type"`
    TypeName         string `json:"type_name"`
    Label            string `json:"label,omitempty"`
}

type BpListData struct {
    Breakpoints []BpItem `json:"breakpoints"`
    Count       int      `json:"count"`
}

type BpSetData struct {
    Address    string `json:"address"`
    Type       string `json:"type"`
    Singleshot bool   `json:"singleshot,omitempty"`
}

type InstrInfo struct {
    Address  string `json:"address"`
    Mnemonic string `json:"mnemonic"`
    Op       string `json:"op"`
    Bytes    string `json:"bytes"`
    Size     int    `json:"size"`
    Comment  string `json:"comment,omitempty"`
}

type DisasmResult struct {
    Address      string      `json:"address"`
    Count        int         `json:"count"`
    Instructions []InstrInfo `json:"instructions"`
}

type DisasmFunctionResult struct {
    Address       string      `json:"address"`
    Instructions  []InstrInfo `json:"instructions,omitempty"`
    Note          string      `json:"note,omitempty"`
    FallbackCount int         `json:"fallback_count,omitempty"`
}

type DisasmBasicInfo struct {
    Address string `json:"address,omitempty"`
    Size    int    `json:"size,omitempty"`
    Branch  bool   `json:"branch,omitempty"`
    Call    bool   `json:"call,omitempty"`
}

type AssembleResult struct {
    Size  int    `json:"size"`
    Bytes string `json:"bytes"`
}

type CallStackEntry struct {
    Address string `json:"address"`
    To      string `json:"to,omitempty"`
    From    string `json:"from,omitempty"`
    Comment string `json:"comment,omitempty"`
}

type CallStack struct {
    Stack []CallStackEntry `json:"stack"`
    Count int              `json:"count"`
}

type StackReadData struct {
    Address string `json:"address"`
    Size    int    `json:"size"`
    Hex     string `json:"hex"`
    ASCII   string `json:"ascii"`
}

type ModuleInfoData struct {
    Name         string `json:"name"`
    Base         string `json:"base"`
    Size         int    `json:"size"`
    Entry        string `json:"entry"`
    SectionCount int    `json:"sectionCount"`
    Path         string `json:"path"`
}

type ModuleList struct {
    Modules []ModuleInfoData `json:"modules"`
    Count   int              `json:"count"`
}

type SymbolEntry struct {
    Address     string `json:"address"`
    Decorated   string `json:"decorated"`
    Undecorated string `json:"undecorated"`
}

type SymbolList struct {
    Symbols []SymbolEntry `json:"symbols"`
}

type SymbolSearchResult struct {
    Symbols []SymbolEntry `json:"symbols,omitempty"`
}

type CommandResult struct {
    Output string `json:"output"`
}

type EvalResult struct {
    Value string `json:"value"`
}

type FormatResult struct {
    Result string `json:"result"`
}

type EventsResult struct {
    Events []string `json:"events"`
}

type ProcessBasicInfo struct {
    PID           int    `json:"pid"`
    PEBAddress    string `json:"peb_address"`
    EntryPoint    string `json:"entry_point"`
    DebuggerState string `json:"debugger_state"`
}

type ProcessDetails struct {
    PID           int    `json:"pid"`
    PEBAddress    string `json:"peb_address"`
    EntryPoint    string `json:"entry_point"`
    DebuggerState string `json:"debugger_state"`
    IsElevated    bool   `json:"is_elevated"`
    DepEnabled    bool   `json:"dep_enabled"`
}

type ThreadEntry struct {
    ID     int    `json:"id,omitempty"`
    Name   string `json:"name,omitempty"`
    Handle string `json:"handle,omitempty"`
    TEB    string `json:"teb,omitempty"`
    Entry  string `json:"entry,omitempty"`
}

type ThreadList struct {
    Threads []ThreadEntry `json:"threads"`
    Count   int           `json:"count"`
}

type ThreadCount struct {
    Count int `json:"count"`
}

type HandleInfo struct {
    Handle string `json:"handle"`
    Type   string `json:"type"`
    Name   string `json:"name,omitempty"`
}

type HandleList struct {
    Handles []HandleInfo `json:"handles"`
    Count   int          `json:"count"`
}

type SearchHit struct {
    Address string `json:"address"`
    Data    string `json:"data,omitempty"`
}

type PatternResult struct {
    Hits         []SearchHit `json:"hits"`
    Count        int         `json:"count"`
    TotalMatches int         `json:"total_matches"`
}

type StringSearchResult struct {
    Hits  []SearchHit `json:"hits"`
    Count int         `json:"count"`
}

type StringAtResult struct {
    Address string `json:"address"`
    String  string `json:"string"`
}

type AutoCompleteResult struct {
    Suggestions []string `json:"suggestions"`
}

type XrefEntry struct {
    Address string `json:"address"`
    Type    string `json:"type,omitempty"`
}

type XrefList struct {
    Xrefs []XrefEntry `json:"xrefs"`
}

type BasicBlockEntry struct {
    Start string `json:"start"`
    End   string `json:"end"`
}

type BasicBlockList struct {
    Blocks []BasicBlockEntry `json:"blocks"`
}

type TraceStatus struct {
    Tracing bool   `json:"tracing,omitempty"`
    File    string `json:"file,omitempty"`
}

type PatchEntry struct {
    Address string `json:"address"`
    Old     string `json:"old"`
    New     string `json:"new"`
}

type PatchList struct {
    Patches []PatchEntry `json:"patches"`
    Count   int          `json:"count"`
}

type HealthData struct {
    Version string `json:"version"`
    Plugin  string `json:"plugin"`
    Status  string `json:"status"`
}
'''

REQUEST_TYPES_GO = '''// Code generated by gen_go.py - DO NOT EDIT.
package servergo

type BpAddrReq struct {
    Address string `json:"address"`
}

type BpSetSoftwareReq struct {
    Address    string `json:"address"`
    Singleshot bool   `json:"singleshot,omitempty"`
}

type BpSetHardwareReq struct {
    Address string `json:"address"`
    Type    string `json:"type,omitempty"`
    Size    string `json:"size,omitempty"`
}

type BpSetMemoryReq struct {
    Address string `json:"address"`
    Type    string `json:"type,omitempty"`
}

type BpDeleteReq struct {
    Address string `json:"address"`
    Type    string `json:"type,omitempty"`
}

type BpConditionReq struct {
    Address   string `json:"address"`
    Condition string `json:"condition"`
}

type BpLogReq struct {
    Address string `json:"address"`
    Text    string `json:"text"`
}

type BpConfigureReq struct{}

type DisasmAssembleReq struct {
    Address     string `json:"address"`
    Instruction string `json:"instruction"`
}

type LabelSetReq struct {
    Address string `json:"address"`
    Text    string `json:"text"`
}

type CommentSetReq struct {
    Address string `json:"address"`
    Text    string `json:"text"`
}

type BookmarkSetReq struct {
    Address string `json:"address"`
    Set     bool   `json:"set"`
}

type SearchPatternReq struct {
    Pattern    string `json:"pattern"`
    Address    string `json:"address,omitempty"`
    Size       string `json:"size,omitempty"`
    MaxResults int    `json:"max_results,omitempty"`
}

type SearchStringReq struct {
    Text     string `json:"text"`
    Module   string `json:"module,omitempty"`
    Encoding string `json:"encoding,omitempty"`
}

type SearchAutoCompleteReq struct {
    Search     string `json:"search"`
    MaxResults int    `json:"max_results,omitempty"`
}

type TraceIntoReq struct {
    Condition string `json:"condition,omitempty"`
    MaxSteps  string `json:"max_steps,omitempty"`
    LogText   string `json:"log_text,omitempty"`
}

type TraceOverReq struct {
    Condition string `json:"condition,omitempty"`
    MaxSteps  string `json:"max_steps,omitempty"`
    LogText   string `json:"log_text,omitempty"`
}

type TraceConditionalRunReq struct {
    Type              string `json:"type,omitempty"`
    BreakCondition    string `json:"break_condition,omitempty"`
    LogText           string `json:"log_text,omitempty"`
    LogCondition      string `json:"log_condition,omitempty"`
    CommandText       string `json:"command_text,omitempty"`
    CommandCondition  string `json:"command_condition,omitempty"`
}

type TraceLogReq struct {
    File      string `json:"file"`
    Text      string `json:"text,omitempty"`
    Condition string `json:"condition,omitempty"`
}

type IdReq struct {
    ID string `json:"id"`
}
'''

# ─── Code generation ─────────────────────────────────────────────────────

def pascal(s: str) -> str:
    return ''.join(word.capitalize() for word in s.replace('-', '_').split('_'))

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def gen_action(cat: str, action: str, method: str, endpoint: str,
               body_type: str, has_body: bool, get_params: list[str]):
    func_name = pascal(action)
    resp_type = ENDPOINT_RESPONSE_TYPES.get(endpoint, "map[string]any")
    lines = []

    lines.append(f"// {func_name} calls {method} {endpoint}")

    func_params = []
    if has_body and body_type:
        func_params.append(f"req {body_type}")
    if get_params:
        for p in get_params:
            func_params.append(f"{p} string")

    param_str = ", ".join(func_params)
    lines.append(f"func (c *Client) {func_name}({param_str}) ({resp_type}, error) {{")

    if method == "GET":
        if get_params:
            pm = "map[string]string{\n"
            for p in get_params:
                pm += f'        "{p}": {p},\n'
            pm += "    }"
            lines.append(f"    return doGET[{resp_type}](c, \"{endpoint}\", {pm})")
        else:
            lines.append(f"    return doGET[{resp_type}](c, \"{endpoint}\", nil)")
    elif method == "POST":
        if body_type:
            lines.append(f"    return doPOST[{resp_type}](c, \"{endpoint}\", req)")
        else:
            lines.append(f"    return doPOST[{resp_type}](c, \"{endpoint}\", nil)")

    lines.append("}")
    return lines

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate client.go
    write_file(OUTPUT_DIR / "client.go", CLIENT_GO)
    print("  ✓ client.go")

    # Generate types.go
    write_file(OUTPUT_DIR / "types.go", TYPES_GO)
    print("  ✓ types.go")

    # Generate request.go
    write_file(OUTPUT_DIR / "request.go", REQUEST_TYPES_GO)
    print("  ✓ request.go")

    # Generate api_*.go per tool category
    api_count = 0
    for cat, actions in TOOL_ACTIONS.items():
        file_path = OUTPUT_DIR / f"api_{cat}.go"
        lines = ["// Code generated by gen_go.py - DO NOT EDIT.\npackage servergo\n"]
        lines.append(f"// ─── {pascal(cat)} API ────────────────────────────────────────\n")

        for action in actions:
            a, method, endpoint, body_type, has_body, get_params = action
            gl = gen_action(cat, a, method, endpoint, body_type, has_body, get_params)
            lines.extend(gl)
            lines.append("")

        write_file(file_path, "\n".join(lines))
        api_count += 1

    # Generate api_health.go
    with open(OUTPUT_DIR / "api_health.go", "w", encoding='utf-8') as f:
        f.write("// Code generated by gen_go.py - DO NOT EDIT.\n")
        f.write("package servergo\n\n")
        f.write("// Health checks the plugin connectivity.\n")
        f.write("func (c *Client) Health() (HealthData, error) {\n")
        f.write("    return doGET[HealthData](c, \"/api/health\", nil)\n")
        f.write("}\n")
    print("  ✓ api_health.go")

    print(f"\nDone: {api_count} API files generated in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

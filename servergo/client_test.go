package servergo

import (
	"fmt"
	"os"
	"testing"
)

var client *Client

func TestMain(m *testing.M) {
	client = NewClient("", 0, "")
	fmt.Println("[setup] Client created, target: 127.0.0.1:27042")
	os.Exit(m.Run())
}

func TestHealth(t *testing.T) {
	data, err := client.Health()
	if err != nil {
		t.Fatalf("Health() failed: %v", err)
	}
	t.Logf("Health: %+v", data)
}

// ─── Debug ──────────────────────────────────────────────────────────────

func TestDebugGetState(t *testing.T) {
	data, err := client.GetState()
	if err != nil {
		t.Fatalf("GetState() failed: %v", err)
	}
	t.Logf("GetState: %+v", data)
	if data.State == "" {
		t.Error("State is empty")
	}
}

func TestDebugStepInto(t *testing.T) {
	data, err := client.StepInto()
	if err != nil {
		t.Logf("StepInto() may fail: %v", err)
	} else {
		t.Logf("StepInto: %+v", data)
	}
}

// ─── Registers ──────────────────────────────────────────────────────────

func TestRegGetAll(t *testing.T) {
	data, err := client.GetAll()
	if err != nil {
		t.Fatalf("GetAll() failed: %v", err)
	}
	t.Logf("Registers: %d keys", len(data))
	for k, v := range data {
		t.Logf("  %s = %s", k, v)
		break
	}
}

func TestRegGetSpecific(t *testing.T) {
	data, err := client.GetSpecific("eip")
	if err != nil {
		t.Fatalf("GetSpecific(eip) failed: %v", err)
	}
	t.Logf("Reg eip: %+v", data)
}

// ─── Process ────────────────────────────────────────────────────────────

func TestProcessBasicInfo(t *testing.T) {
	data, err := client.BasicInfo()
	if err != nil {
		t.Fatalf("BasicInfo() failed: %v", err)
	}
	t.Logf("BasicInfo: %+v", data)
}

func TestProcessDetailed(t *testing.T) {
	data, err := client.Detailed()
	if err != nil {
		t.Fatalf("Detailed() failed: %v", err)
	}
	t.Logf("Detailed: %+v", data)
}

func TestProcessCmdline(t *testing.T) {
	data, err := client.Cmdline()
	if err != nil {
		t.Fatalf("Cmdline() failed: %v", err)
	}
	t.Logf("Cmdline: %+v", data)
}

// ─── Memory ─────────────────────────────────────────────────────────────

func TestMemoryRead(t *testing.T) {
	data, err := client.Read("cip", "64")
	if err != nil {
		t.Fatalf("Read() failed: %v", err)
	}
	t.Logf("Read: addr=%s size=%d hex_len=%d", data.Address, data.Size, len(data.Hex))
}

func TestMemoryPageInfo(t *testing.T) {
	data, err := client.PageInfo("cip")
	if err != nil {
		t.Fatalf("PageInfo() failed: %v", err)
	}
	t.Logf("PageInfo: %+v", data)
}

func TestMemoryIsValid(t *testing.T) {
	data, err := client.IsValid("cip")
	if err != nil {
		t.Fatalf("IsValid() failed: %v", err)
	}
	t.Logf("IsValid: %+v", data)
}

// ─── Breakpoints ────────────────────────────────────────────────────────

func TestBpList(t *testing.T) {
	data, err := client.ListBps()
	if err != nil {
		t.Fatalf("ListBps() failed: %v", err)
	}
	t.Logf("Breakpoints: count=%d", data.Count)
}

// ─── Disassembly ────────────────────────────────────────────────────────

func TestDisasmAtAddress(t *testing.T) {
	data, err := client.AtAddress("cip", "5")
	if err != nil {
		t.Fatalf("AtAddress() failed: %v", err)
	}
	t.Logf("Disasm: addr=%s count=%d", data.Address, data.Count)
	for _, ins := range data.Instructions {
		t.Logf("  %s  %s %s", ins.Address, ins.Mnemonic, ins.Op)
	}
}

func TestDisasmBasicInfo(t *testing.T) {
	data, err := client.DisasmBasicInfo("cip")
	if err != nil {
		t.Fatalf("DisasmBasicInfo() failed: %v", err)
	}
	t.Logf("DisasmBasicInfo: %+v", data)
}

// ─── Stack ──────────────────────────────────────────────────────────────

func TestStackRead(t *testing.T) {
	data, err := client.ReadStack("csp", "64")
	if err != nil {
		t.Fatalf("ReadStack() failed: %v", err)
	}
	t.Logf("StackRead: addr=%s size=%d", data.Address, data.Size)
}

func TestStackCallStack(t *testing.T) {
	data, err := client.GetCallStack("50")
	if err != nil {
		t.Fatalf("GetCallStack() failed: %v", err)
	}
	t.Logf("CallStack: count=%d", data.Count)
}

// ─── Modules ────────────────────────────────────────────────────────────

func TestModuleList(t *testing.T) {
	data, err := client.ListModules()
	if err != nil {
		t.Fatalf("ListModules() failed: %v", err)
	}
	t.Logf("Modules: count=%d", data.Count)
	for _, m := range data.Modules {
		t.Logf("  %s base=%s", m.Name, m.Base)
	}
}

// ─── Threads ────────────────────────────────────────────────────────────

func TestThreadsList(t *testing.T) {
	data, err := client.ListThreads()
	if err != nil {
		t.Fatalf("ListThreads() failed: %v", err)
	}
	t.Logf("Threads: count=%d", data.Count)
}

func TestThreadsCount(t *testing.T) {
	data, err := client.Count()
	if err != nil {
		t.Fatalf("Count() failed: %v", err)
	}
	t.Logf("ThreadCount: %+v", data)
}

// ─── Symbols ────────────────────────────────────────────────────────────

func TestSymbolResolve(t *testing.T) {
	data, err := client.Resolve("ntdll.NtCreateFile")
	if err != nil {
		t.Logf("Resolve() may fail: %v", err)
	} else {
		t.Logf("Resolve: %+v", data)
	}
}

// ─── Command ────────────────────────────────────────────────────────────

func TestCommandEval(t *testing.T) {
	data, err := client.Evaluate(struct {
		Expression string `json:"expression"`
	}{Expression: "cip"})
	if err != nil {
		t.Fatalf("Evaluate() failed: %v", err)
	}
	t.Logf("Eval cip: %+v", data)
}

// ─── Anti-Debug ─────────────────────────────────────────────────────────

func TestAntiDebugDep(t *testing.T) {
	data, err := client.Dep()
	if err != nil {
		t.Fatalf("Dep() failed: %v", err)
	}
	t.Logf("DEP: %+v", data)
}

// ─── Control Flow ───────────────────────────────────────────────────────

func TestControlFlowFuncType(t *testing.T) {
	data, err := client.FuncType("eip")
	if err != nil {
		t.Logf("FuncType() failed: %v", err)
	} else {
		t.Logf("FuncType: %+v", data)
	}
}

func TestControlFlowBranchDest(t *testing.T) {
	data, err := client.BranchDest("eip")
	if err != nil {
		t.Logf("BranchDest() failed: %v", err)
	} else {
		t.Logf("BranchDest: %+v", data)
	}
}

// ─── Handles ────────────────────────────────────────────────────────────

func TestHandlesList(t *testing.T) {
	data, err := client.ListHandles()
	if err != nil {
		t.Logf("ListHandles() failed: %v", err)
	} else {
		t.Logf("Handles: count=%d", data.Count)
	}
}

// ─── Patches ────────────────────────────────────────────────────────────

func TestPatchesList(t *testing.T) {
	data, err := client.ListPatches()
	if err != nil {
		t.Logf("ListPatches() failed: %v", err)
	} else {
		t.Logf("Patches: count=%d", data.Count)
	}
}

// ─── Exceptions ─────────────────────────────────────────────────────────

func TestExceptionsListCodes(t *testing.T) {
	data, err := client.ListCodes()
	if err != nil {
		t.Fatalf("ListCodes() failed: %v", err)
	}
	t.Logf("Exception codes: %d entries", len(data))
}

// ─── Tracing ────────────────────────────────────────────────────────────

func TestTraceStatus(t *testing.T) {
	data, err := client.TraceStatus()
	if err != nil {
		t.Fatalf("TraceStatus() failed: %v", err)
	}
	t.Logf("TraceStatus: %+v", data)
}

// ─── Analysis ───────────────────────────────────────────────────────────

func TestAnalysisXrefsTo(t *testing.T) {
	data, err := client.XrefsTo("eip")
	if err != nil {
		t.Logf("XrefsTo() may fail: %v", err)
	} else {
		t.Logf("XrefsTo: count=%d", len(data.Xrefs))
	}
}

// ─── Search ─────────────────────────────────────────────────────────────

func TestSearchEncodeType(t *testing.T) {
	data, err := client.EncodeType("eip", "1")
	if err != nil {
		t.Logf("EncodeType() failed: %v", err)
	} else {
		t.Logf("EncodeType: %+v", data)
	}
}

// ─── Address Convert ────────────────────────────────────────────────────

func TestAddressVaToFile(t *testing.T) {
	data, err := client.VaToFile("eip")
	if err != nil {
		t.Logf("VaToFile() failed: %v", err)
	} else {
		t.Logf("VaToFile: %+v", data)
	}
}
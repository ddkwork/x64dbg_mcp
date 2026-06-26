package servergo

import (
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"math/big"
	"strconv"
	"strings"
	"testing"
)

// getTargetAddr 从 "jmp <addr>" 或 "call <addr>" 格式的反汇编文本中提取目标地址。
func getTargetAddr[T uint32 | uint64](assembly string) T {
	parts := strings.Fields(assembly)
	if len(parts) != 2 {
		panic(fmt.Sprintf("invalid disassembly: %q", assembly))
	}
	addrStr := strings.TrimPrefix(parts[1], "0x")
	b, err := hex.DecodeString(addrStr)
	if err != nil {
		panic(fmt.Sprintf("decode address hex: %v", err))
	}
	switch any(T(0)).(type) {
	case uint32:
		if len(b) < 4 {
			var padded [4]byte
			copy(padded[4-len(b):], b)
			return T(binary.BigEndian.Uint32(padded[:]))
		}
		return T(binary.BigEndian.Uint32(b[len(b)-4:]))
	default:
		if len(b) < 8 {
			var padded [8]byte
			copy(padded[8-len(b):], b)
			return T(binary.BigEndian.Uint64(padded[:]))
		}
		return T(binary.BigEndian.Uint64(b[len(b)-8:]))
	}
}

// peekStackUint32 从栈上读取第 n 个 uint32 值（n 从 1 开始，esp+0 为第 1 个）。
func (c *Client) peekStackUint32(n int) (uint32, error) {
	// 读取 csp 寄存器获取当前栈指针
	reg, err := c.GetSpecific("csp")
	if err != nil {
		return 0, fmt.Errorf("GetSpecific(csp): %w", err)
	}
	cspStr := reg["csp"]
	if cspStr == "" {
		return 0, fmt.Errorf("csp value empty")
	}
	cspStr = strings.TrimPrefix(cspStr, "0x")
	csp, err := strconv.ParseUint(cspStr, 16, 64)
	if err != nil {
		return 0, fmt.Errorf("parse csp: %w", err)
	}
	offset := uint64(n-1) * 4
	addr := fmt.Sprintf("0x%x", csp+offset)
	data, err := c.Read(addr, "4")
	if err != nil {
		return 0, fmt.Errorf("Read(%s): %w", addr, err)
	}
	b, err := hex.DecodeString(data.Hex)
	if err != nil {
		return 0, fmt.Errorf("decode hex: %w", err)
	}
	if len(b) < 4 {
		return 0, fmt.Errorf("short read: %d bytes", len(b))
	}
	return binary.LittleEndian.Uint32(b[:4]), nil
}

// Test_x32dbg_GetMainModuleEntry 移植自 x32dbg_test.go 的 big number trace 测试。
//
// PS:
// panic: read tcp 127.0.0.1:56525->127.0.0.1:6589: wsarecv: An established connection was aborted by the software in your host machine.
// 在端口正常的情况下，这种是由于发包参数错误，然而插件 tcp 服务端并不会回复一个参数错误的包,没有源代码无法修复通信的可读性
func Test_x32dbg_GetMainModuleEntry(t *testing.T) {
	// ── 1. 获取主模块入口点 ──
	info, err := client.BasicInfo()
	if err != nil {
		t.Fatalf("BasicInfo() failed: %v", err)
	}
	entry := info.EntryPoint
	t.Logf("EntryPoint: %s", entry)

	// ── 2. 清空所有断点 ──
	bps, err := client.ListBps()
	if err != nil {
		t.Fatalf("ListBps() failed: %v", err)
	}
	for _, bp := range bps.Breakpoints {
		if _, err := client.BpDelete(BpDeleteReq{Address: bp.Address}); err != nil {
			t.Logf("BpDelete(%s) warning: %v", bp.Address, err)
		}
	}
	t.Logf("Removed %d breakpoints", bps.Count)

	// ── 3. 从 entry+0x19 的反汇编中提取 asm1 地址 ──
	asmAddr := fmt.Sprintf("(%s)+0x19", entry)
	disasm, err := client.AtAddress(asmAddr, "1")
	if err != nil {
		t.Fatalf("AtAddress(%s) failed: %v", asmAddr, err)
	}
	if len(disasm.Instructions) == 0 {
		t.Fatal("no instruction at entry+0x19")
	}
	ins := disasm.Instructions[0]
	t.Logf("  %s  %s %s", ins.Address, ins.Mnemonic, ins.Op)

	fullAsm := ins.Mnemonic + " " + ins.Op
	asm1 := getTargetAddr[uint32](fullAsm)
	t.Logf("asm1 = 0x%x", asm1)

	// ── 4. 计算 end 地址并设置断点/注释/标签 ──
	end := asm1 + 0x50B
	endStr := fmt.Sprintf("0x%x", end)

	if _, err := client.SetSoftware(BpSetSoftwareReq{Address: endStr}); err != nil {
		t.Fatalf("SetSoftware(end) failed: %v", err)
	}
	if _, err := client.SetComment(CommentSetReq{Address: endStr, Text: "end trace"}); err != nil {
		t.Fatalf("SetComment(end) failed: %v", err)
	}
	if _, err := client.SetLabel(LabelSetReq{Address: endStr, Text: "end_trace"}); err != nil {
		t.Fatalf("SetLabel(end) failed: %v", err)
	}
	t.Logf("end = %s (breakpoint + comment + label set)", endStr)

	// ── 5. 从 asm1+0xA7 的反汇编中提取 __allmul 地址 ──
	allmulAddr := fmt.Sprintf("0x%x", asm1+0xA7)
	disasm, err = client.AtAddress(allmulAddr, "1")
	if err != nil {
		t.Fatalf("AtAddress(%s) failed: %v", allmulAddr, err)
	}
	if len(disasm.Instructions) == 0 {
		t.Fatal("no instruction at asm1+0xa7")
	}
	ins = disasm.Instructions[0]
	fullAsm = ins.Mnemonic + " " + ins.Op
	allmul := getTargetAddr[uint32](fullAsm)
	allmulStr := fmt.Sprintf("0x%x", allmul)
	t.Logf("__allmul = %s", allmulStr)

	if _, err := client.SetComment(CommentSetReq{Address: allmulStr, Text: "__allmul"}); err != nil {
		t.Fatalf("SetComment(allmul) failed: %v", err)
	}
	if _, err := client.SetLabel(LabelSetReq{Address: allmulStr, Text: "__allmul"}); err != nil {
		t.Fatalf("SetLabel(allmul) failed: %v", err)
	}
	if _, err := client.SetSoftware(BpSetSoftwareReq{Address: allmulStr}); err != nil {
		t.Fatalf("SetSoftware(allmul) failed: %v", err)
	}

	// ── 6. 从 asm1+0x10B 的反汇编中提取 __alldiv 地址 ──
	alldivAddr := fmt.Sprintf("0x%x", asm1+0x10B)
	disasm, err = client.AtAddress(alldivAddr, "1")
	if err != nil {
		t.Fatalf("AtAddress(%s) failed: %v", alldivAddr, err)
	}
	if len(disasm.Instructions) == 0 {
		t.Fatal("no instruction at asm1+0x10b")
	}
	ins = disasm.Instructions[0]
	fullAsm = ins.Mnemonic + " " + ins.Op
	alldiv := getTargetAddr[uint32](fullAsm)
	alldivStr := fmt.Sprintf("0x%x", alldiv)
	t.Logf("__alldiv = %s", alldivStr)

	if _, err := client.SetComment(CommentSetReq{Address: alldivStr, Text: "__alldiv"}); err != nil {
		t.Fatalf("SetComment(alldiv) failed: %v", err)
	}
	if _, err := client.SetLabel(LabelSetReq{Address: alldivStr, Text: "__alldiv"}); err != nil {
		t.Fatalf("SetLabel(alldiv) failed: %v", err)
	}
	if _, err := client.SetSoftware(BpSetSoftwareReq{Address: alldivStr}); err != nil {
		t.Fatalf("SetSoftware(alldiv) failed: %v", err)
	}

	// ── 7. 启动 trace 运行 ──
	//
	// 原测试使用 RunCommandWithCount("run", 400, bigNumTrace) 在每次断点命中时回调,
	// 通过 Eip 判断命中哪个断点，并调用 mul/div 辅助函数记录大数运算。
	// 这里使用 ConditionalRun 实现类似功能：
	traceReq := TraceConditionalRunReq{
		Type:           "0",
		BreakCondition: "",
		LogText:        "",
		LogCondition:   "",
		CommandText:    "",
		CommandCondition: "",
	}
	if _, err := client.ConditionalRun(traceReq); err != nil {
		t.Fatalf("ConditionalRun() failed: %v", err)
	}

	// ── 8. 读取寄存器进行 big number trace 验证 ──
	// 模拟 bigNumTrace 回调中的 mul/alldiv 调用：
	// 读取 eip
	eipReg, err := client.GetSpecific("eip")
	if err != nil {
		t.Fatalf("GetSpecific(eip) failed: %v", err)
	}
	eipStr := strings.TrimPrefix(eipReg["eip"], "0x")
	eipVal, _ := strconv.ParseUint(eipStr, 16, 32)
	eip32 := uint32(eipVal)
	t.Logf("EIP = 0x%x", eip32)

	switch eip32 {
	case allmul:
		t.Log("hit __allmul breakpoint")
		xLow, _ := client.peekStackUint32(1)
		xHigh, _ := client.peekStackUint32(2)
		yLow, _ := client.peekStackUint32(3)
		yHigh, _ := client.peekStackUint32(4)

		x := new(big.Int).SetUint64(uint64(xHigh)<<32 | uint64(xLow))
		y := new(big.Int).SetUint64(uint64(yHigh)<<32 | uint64(yLow))
		z := new(big.Int).Mul(x, y)
		t.Logf("mul: %d * %d = %d", x, y, z)
	case alldiv:
		t.Log("hit __alldiv breakpoint")
		xLow, _ := client.peekStackUint32(1)
		xHigh, _ := client.peekStackUint32(2)
		yLow, _ := client.peekStackUint32(3)
		yHigh, _ := client.peekStackUint32(4)

		x := new(big.Int).SetUint64(uint64(xHigh)<<32 | uint64(xLow))
		y := new(big.Int).SetUint64(uint64(yHigh)<<32 | uint64(yLow))
		if y.Sign() != 0 {
			z := new(big.Int).Div(x, y)
			t.Logf("div: %d / %d = %d", x, y, z)
		} else {
			t.Log("div: division by zero")
		}
	case end:
		t.Log("hit end trace breakpoint, restarting...")
		if _, err := client.RestartDebug(); err != nil {
			t.Logf("RestartDebug() warning: %v", err)
		}
		/*
			bugfix:
			Restart 重启服务端 97% 的情况下都失败的修复方案：
				restartadmin 命令执行后不是每次都能成功重启服务端,
				如果重启失败，客户端无论如何都无法连接了，只能手动到调试器输入命令 reloadplugin LyScript,
				这样每次都能成功重启服务端，但是这样太浪费时间了,
				所以需要在插件执行命令前检测命令是否是 restartadmin，如果是,
				则执行完命令之后直接调用 c api 的命令运行函数直接运行 reloadplugin LyScript 命令，
				这样就能保证每次 restartadmin 之后服务端都能重启成功，且客户端可以正常连接了.
		*/
	}
}

// The desktop launcher stub.
//
// It is generic: one binary, shipped with argsense, copied once per app and
// told what to run by a payload appended after the last PE section (see
// `argsense/launcher/config.py`).
//
// Nothing here knows about argsense or python beyond "start this executable
// with these arguments, in this directory". The window is Gui-subsystem (see
// the second #flag), so double-clicking it never flashes a console.

import os

#flag windows -luser32
#flag windows -Wl,--subsystem,windows

const magic = 'ARGSNCHR'

fn C.MessageBoxW(hwnd voidptr, text &u16, caption &u16, flags u32) int

struct Config {
mut:
	python       string
	script       string
	module       string
	cwd          string
	args         []string
	log          string
	port         string
	window_size  string
	window_title string
	icon         string
}

fn main() {
	exe := os.executable()
	mut cfg := read_config(exe) or {
		alert('This launcher is damaged.\n\n${err.msg()}')
		return
	}

	if !os.exists(cfg.python) {
		alert('The interpreter this launcher needs is missing:\n\n' + cfg.python)
		return
	}
	// a payload names either a script file or a module to run with `-m`.
	mut args := []string{}
	if cfg.module != '' {
		args << ['-m', cfg.module]
	} else {
		if !os.exists(cfg.script) {
			alert('The script this launcher starts is missing:\n\n' + cfg.script)
			return
		}
		args << cfg.script
	}
	args << cfg.args
	args << launcher_options(cfg)

	mut env := os.environ()
	env['PYTHONUTF8'] = '1'
	env['PYTHONBREAKPOINT'] = '0'

	mut proc := os.new_process(cfg.python)
	proc.set_args(args)
	if cfg.cwd != '' {
		proc.set_work_folder(cfg.cwd)
	}
	proc.set_environment(env)
	proc.run()
	proc.wait()
	code := proc.code
	proc.close()

	// a gui app that returns 0 was closed by its user; anything else is worth
	// saying out loud, because the window (and with it the evidence) is gone.
	// code 3 means the app already showed its own dialog (see
	// `argsense/launcher/boot.py`), so the user is not told twice.
	if code != 0 && code != 3 {
		mut message := 'The app exited with code ${code}.'
		if cfg.log != '' {
			message += '\n\nLog: ${cfg.log}'
		}
		alert(message)
	}
}

fn read_config(path string) !Config {
	data := os.read_bytes(path)!
	if data.len < 12 {
		return error('the file is too short to hold a payload')
	}
	if data[data.len - 8..].bytestr() != magic {
		return error('no launcher payload found')
	}
	length := int(u32(data[data.len - 12]) | u32(data[data.len - 11]) << 8 |
		u32(data[data.len - 10]) << 16 | u32(data[data.len - 9]) << 24)
	if length <= 0 || length > data.len - 12 {
		return error('the payload length is wrong')
	}

	mut cfg := Config{}
	text := data[data.len - 12 - length..data.len - 12].bytestr()
	for line in text.split_into_lines() {
		if line == '' {
			continue
		}
		pos := line.index('=') or { continue }
		key := line[..pos]
		value := line[pos + 1..]
		match key {
			'python' { cfg.python = value }
			'script' { cfg.script = value }
			'module' { cfg.module = value }
			'cwd' { cfg.cwd = value }
			'args' { cfg.args = split_args(value) }
			'log' { cfg.log = value }
			'port' { cfg.port = value }
			'window_size' { cfg.window_size = value }
			'window_title' { cfg.window_title = value }
			'icon' { cfg.icon = value }
			else {}
		}
	}
	if cfg.python == '' {
		return error('the payload names no interpreter')
	}
	return cfg
}

fn split_args(text string) []string {
	if text == '' {
		return []
	}
	return text.split('\x1f')
}

fn launcher_options(cfg Config) []string {
	mut out := []string{}
	if cfg.port != '' {
		out << ['--argsense-port', cfg.port]
	}
	if cfg.window_size != '' {
		out << ['--argsense-window-size', cfg.window_size]
	}
	if cfg.window_title != '' {
		out << ['--argsense-window-title', cfg.window_title]
	}
	if cfg.icon != '' {
		out << ['--argsense-window-icon', cfg.icon]
	}
	if cfg.log != '' {
		out << ['--argsense-log', cfg.log]
	}
	return out
}

fn alert(message string) {
	C.MessageBoxW(voidptr(0), message.to_wide(), 'argsense'.to_wide(), 0x10)
}
